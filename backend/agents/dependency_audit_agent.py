import json
import os
import re
from typing import Dict, Any, AsyncGenerator, Optional, Set, TypedDict, List
from dataclasses import dataclass
from tools.security.go_vulnerability_tool import GoVulnerabilityTool
from services.build_validator import BuildValidator
from config.settings import settings
from services.repository_service import repository_service
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class FixResult:
    success: bool
    updated_files: Dict[str, str]  # file_path -> new_content
    fix_explanation: str
    vulnerabilities_addressed: int
    error_message: Optional[str] = None

class DependencyAuditState(TypedDict):
    repository_url: str
    clone_path: str
    temp_dir: str
    govulncheck_output: str
    fix_result: Optional[FixResult]
    build_result: Any
    pr_result: Dict[str, Any]
    vulnerabilities_found: int
    progress: float
    current_step: str
    errors: List[str]
    completed: bool

class DependencyAuditAgent:    
    def __init__(self, openai_api_key: str):
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0,
            api_key=openai_api_key
        )
        self.build_validator = BuildValidator()
        self.temp_dir = None
        self.current_state = None
    
    async def clone_and_setup(self, state: DependencyAuditState) -> DependencyAuditState:
        """Step 1: Clone repository and basic setup."""
        state["current_step"] = "Cloning repository for vulnerability audit..."
        state["progress"] = 10.0
        
        clone_result = repository_service.clone_repository(state["repository_url"])
        if clone_result["status"] != "success":
            state["errors"].append(f"Failed to clone repository: {clone_result.get('error', 'Unknown error')}")
            state["completed"] = True
            return state

        state["clone_path"] = clone_result["clone_path"]
        state["temp_dir"] = clone_result["clone_path"]
        self.temp_dir = clone_result["clone_path"]
        
        logger.info(f"Successfully cloned repository to: {clone_result['clone_path']}")
        state["current_step"] = "Repository cloned successfully"
        state["progress"] = 20.0
        
        return state

    async def check_go_project(self, state: DependencyAuditState) -> DependencyAuditState:
        """Step 2: Check if this is a Go project."""
        state["current_step"] = "Checking for Go project..."
        state["progress"] = 25.0
        
        if not state["clone_path"]:
            state["errors"].append("No clone path available")
            state["completed"] = True
            return state
        
        go_mod_path = os.path.join(state["clone_path"], "go.mod")
        if not os.path.exists(go_mod_path):
            state["errors"].append("No Go project detected")
            state["completed"] = True
            state["current_step"] = "No Go project found"
            state["progress"] = 100.0
            return state
        
        state["current_step"] = "Go project detected"
        state["progress"] = 30.0
        return state

    async def scan_vulnerabilities(self, state: DependencyAuditState) -> DependencyAuditState:
        """Step 3: Scan for security vulnerabilities."""
        state["current_step"] = "Scanning for security vulnerabilities..."
        state["progress"] = 40.0
        
        try:
            vuln_tool = GoVulnerabilityTool()
            govulncheck_output = await vuln_tool.get_govulncheck_output(state["clone_path"])
            
            if not govulncheck_output:
                state["errors"].append("govulncheck not available or failed")
                state["completed"] = True
                state["current_step"] = "Vulnerability scanner unavailable"
                state["progress"] = 100.0
                return state
            
            state["govulncheck_output"] = govulncheck_output
            logger.info(f"Got govulncheck output: {len(govulncheck_output)} characters")
            
            # Check if vulnerabilities were found
            if "Your code is affected by 0 vulnerabilities" in govulncheck_output or "No vulnerabilities found" in govulncheck_output:
                state["vulnerabilities_found"] = 0
                state["completed"] = True
                state["current_step"] = "No vulnerabilities found"
                state["progress"] = 100.0
                return state
            
            state["current_step"] = "Vulnerabilities detected"
            state["progress"] = 50.0
            
        except Exception as e:
            state["errors"].append(f"Vulnerability scanning failed: {str(e)}")
            state["completed"] = True
        
        return state

    async def ai_vulnerability_fixing(self, state: DependencyAuditState) -> DependencyAuditState:
        """Step 4: Use AI to analyze vulnerabilities and generate fixes."""
        state["current_step"] = "Using AI to analyze vulnerabilities and generate fixes..."
        state["progress"] = 60.0
        
        try:
            logger.info("Starting AI-powered vulnerability fixing")
            
            affected_files = self._extract_file_paths(state["govulncheck_output"])
            logger.info(f"Found {len(affected_files)} affected files: {affected_files}")
            
            file_contents = self._read_source_files(state["clone_path"], affected_files)
            logger.info(f"Read {len(file_contents)} files for analysis")
            
            ai_response = await self._send_to_ai(state["govulncheck_output"], file_contents)
            fix_result = self._parse_ai_response(ai_response)
            
            state["fix_result"] = fix_result
            
            if not fix_result.success:
                state["errors"].append(f"AI fix generation failed: {fix_result.error_message}")
                state["completed"] = True
                state["current_step"] = "AI fix generation failed"
                state["progress"] = 100.0
                return state
            
            state["vulnerabilities_found"] = fix_result.vulnerabilities_addressed
            state["current_step"] = "AI fixes generated successfully"
            state["progress"] = 65.0
            
        except Exception as e:
            logger.error(f"Vulnerability fixing failed: {e}")
            state["errors"].append(f"Vulnerability fixing failed: {str(e)}")
            state["completed"] = True
        
        return state

    async def validate_fixes(self, state: DependencyAuditState) -> DependencyAuditState:
        """Step 5: Validate fixes with go build."""
        state["current_step"] = "Validating fixes with go build..."
        state["progress"] = 70.0
        
        try:
            if not state["fix_result"] or not state["fix_result"].updated_files:
                state["errors"].append("No fixes to validate")
                state["completed"] = True
                return state
            
            build_result = self.build_validator.validate_fixes(
                state["clone_path"], 
                state["fix_result"].updated_files
            )
            state["build_result"] = build_result
            
            if not build_result.success:
                logger.warning(f"Build validation failed: {build_result.error_message}")
                state["errors"].append(f"Build validation failed: {build_result.error_message}")
                state["completed"] = True
                state["current_step"] = "Build validation failed"
                state["progress"] = 100.0
                return state
            
            logger.info(f"Build validation successful in {build_result.duration:.2f}s")
            state["current_step"] = "Build validation passed"
            state["progress"] = 80.0
            
        except Exception as e:
            state["errors"].append(f"Build validation failed: {str(e)}")
            state["completed"] = True
        
        return state

    async def create_pr(self, state: DependencyAuditState) -> DependencyAuditState:
        """Step 6: Create pull request with fixes."""
        state["current_step"] = f"Build validation passed - creating PR with {len(state['fix_result'].updated_files)} file fixes..."
        state["progress"] = 85.0
        
        try:
            from services.github_service import github_service
            
            vulnerability_results_for_pr = {
                "scan_summary": {
                    "vulnerabilities_found": state["vulnerabilities_found"],
                    "risk_level": "HIGH" if state["vulnerabilities_found"] > 5 else "MEDIUM" if state["vulnerabilities_found"] > 0 else "LOW"
                },
                "affected_modules": list(state["fix_result"].updated_files.keys()),
                "ai_fixes": state["fix_result"].updated_files,
                "fix_explanation": state["fix_result"].fix_explanation,
                "raw_govulncheck_output": state["govulncheck_output"]
            }

            if settings.GITHUB_DRY_RUN:
                logger.info("DRY RUN MODE: Simulating PR creation")
                pr_dict = {
                    "success": True,
                    "pr_url": "DRY_RUN",
                    "pr_number": "DRY_RUN",
                    "branch_name": "DRY_RUN",
                    "files_changed": list(state["fix_result"].updated_files.keys()),
                    "vulnerabilities_fixed": state["vulnerabilities_found"],
                    "dry_run": True,
                    "message": "This is a dry run. No actual PR was created.",
                    "ai_explanation": state["fix_result"].fix_explanation
                }
            else:
                pr_result = github_service.create_pull_request(
                    state["repository_url"], 
                    vulnerability_results_for_pr,
                    state["clone_path"]
                )
                
                pr_dict = {
                    "success": pr_result.success,
                    "pr_url": pr_result.pr_url,
                    "pr_number": pr_result.pr_number,
                    "branch_name": pr_result.branch_name,
                    "files_changed": pr_result.files_changed,
                    "vulnerabilities_fixed": pr_result.vulnerabilities_fixed,
                    "error": pr_result.error_message,
                    "ai_explanation": state["fix_result"].fix_explanation
                }
            
            state["pr_result"] = pr_dict
            state["completed"] = True
            state["current_step"] = "PR created successfully"
            state["progress"] = 100.0
            
        except Exception as e:
            logger.error(f"Failed to create security PR: {e}")
            state["errors"].append(f"Failed to create security PR: {str(e)}")
            state["completed"] = True
            state["current_step"] = "PR creation failed"
            state["progress"] = 100.0
        
        return state

    def _extract_file_paths(self, govulncheck_output: str) -> Set[str]:
        """Extract file paths mentioned in govulncheck output."""
        file_paths = set()
        
        file_paths.add("go.mod")
        file_paths.add("go.sum")

        # Extract file paths from trace lines (e.g., "cmd/api/api.go:88:27")
        # trace_pattern = r'#\d+:\s+([^:]+\.go):\d+:\d+:'
        # matches = re.findall(trace_pattern, govulncheck_output)
        # for match in matches:
        #     file_paths.add(match)
        
        # Extract file paths from other mentions (more general pattern)
        # file_pattern = r'([a-zA-Z_][a-zA-Z0-9_/\-]*\.go)(?::\d+)?'
        # matches = re.findall(file_pattern, govulncheck_output)
        # for match in matches:
            # Filter out Go standard library files and focus on project files
            # if not match.startswith('/') and not match.startswith('go/'):
            #     file_paths.add(match)
        
        return file_paths
    
    def _read_source_files(self, repo_path: str, file_paths: Set[str]) -> Dict[str, str]:
        """Read contents of source files."""
        file_contents: Dict[str, str] = {}
        
        for file_path in file_paths:
            full_path = os.path.join(repo_path, file_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        file_contents[file_path] = f.read()
                    logger.debug(f"Read file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to read file {file_path}: {e}")
            else:
                logger.debug(f"File not found: {file_path}")
        
        return file_contents
    
    async def _send_to_ai(self, govulncheck_output: str, file_contents: Dict[str, str]) -> str:        
        files_section = ""
        for file_path, content in file_contents.items():
            files_section += f"\n--- {file_path} ---\n{content}\n"
        
        system_prompt = """You are a Go security expert specializing in fixing vulnerabilities. 

        Your task is to analyze govulncheck output and fix the identified vulnerabilities by updating the necessary files.

        IMPORTANT RULES:
        1. Focus on dependency updates in go.mod when possible (safest approach)
        2. Only modify source code if absolutely necessary for the fix
        3. Provide the complete updated file content for each file you modify
        4. Explain your reasoning for each change
        5. Be conservative - prefer minimal changes that fix the vulnerability

        Output Format:
        ```json
        {
            "success": true,
            "updated_files": {
                "go.mod": "complete updated go.mod content here",
                "path/to/file.go": "complete updated file content here"
            },
            "fix_explanation": "Detailed explanation of what was changed and why",
            "vulnerabilities_addressed": 3
        }
        ```

        If you cannot fix the vulnerabilities safely, return:
        ```json
        {
            "success": false,
            "updated_files": {},
            "fix_explanation": "Explanation of why fixes cannot be applied safely",
            "vulnerabilities_addressed": 0
        }
        ```"""

        human_prompt = f"""Please analyze this govulncheck output and fix the vulnerabilities:

        GOVULNCHECK OUTPUT:
        {govulncheck_output}

        CURRENT FILES:
        {files_section}

        Please provide fixes following the JSON format specified in the system prompt."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        logger.info("Sending vulnerability data to AI for analysis")
        response = await self.llm.ainvoke(messages)
        return response.content
    
    def _parse_ai_response(self, ai_response: str) -> FixResult:
        """Parse AI response and return FixResult."""
        try:
            json_match = re.search(r'```json\s*\n(.*?)\n```', ai_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                json_str = ai_response.strip()
            
            data = json.loads(json_str)
            
            return FixResult(
                success=data.get("success", False),
                updated_files=data.get("updated_files", {}),
                fix_explanation=data.get("fix_explanation", ""),
                vulnerabilities_addressed=data.get("vulnerabilities_addressed", 0)
            )
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {e}")
            logger.debug(f"AI response was: {ai_response}")
            
            return FixResult(
                success=False,
                updated_files={},
                fix_explanation=f"Failed to parse AI response: {str(e)}",
                vulnerabilities_addressed=0,
                error_message=str(e)
            )

    def create_workflow(self):
        workflow = StateGraph(DependencyAuditState)
        
        workflow.add_node("clone", self.clone_and_setup)
        workflow.add_node("check_go", self.check_go_project)
        workflow.add_node("scan", self.scan_vulnerabilities)
        workflow.add_node("ai_fix", self.ai_vulnerability_fixing)
        workflow.add_node("validate", self.validate_fixes)
        workflow.add_node("create_pr", self.create_pr)
        
        workflow.set_entry_point("clone")
        
        workflow.add_edge("clone", "check_go")
        workflow.add_edge("check_go", "scan")
        workflow.add_edge("scan", "ai_fix")
        workflow.add_edge("ai_fix", "validate")
        workflow.add_edge("validate", "create_pr")
        workflow.add_edge("create_pr", END)
        
        return workflow.compile()

    async def analyze_repository(self, repository_url: str) -> AsyncGenerator[Dict[str, Any], None]:
        logger.info(f"Starting vulnerability audit for repository: {repository_url}")
        
        initial_state = DependencyAuditState(
            repository_url=repository_url,
            clone_path="",
            temp_dir="",
            govulncheck_output="",
            fix_result=None,
            build_result=None,
            pr_result={},
            vulnerabilities_found=0,
            progress=0.0,
            current_step="Starting vulnerability audit...",
            errors=[],
            completed=False
        )
        
        self.current_state = initial_state
        workflow = self.create_workflow()
        
        final_state = None
        try:
            async for step_output in workflow.astream(initial_state):
                for node_name, state in step_output.items():
                    final_state = state
                    self.current_state = state

                    yield {
                        "type": "progress",
                        "current_step": state["current_step"],
                        "progress": state["progress"]
                    }
                    
                    if state["completed"]:
                        break
            
            if final_state:
                if final_state["errors"]:
                    if "No Go project detected" in final_state["errors"]:
                        yield {
                            "type": "completed",
                            "results": {
                                "repository_url": repository_url,
                                "vulnerability_scan": {
                                    "status": "skipped",
                                    "reason": "No Go project detected"
                                },
                                "summary": "Vulnerability audit completed - no Go project found"
                            }
                        }
                    elif "govulncheck not available" in str(final_state["errors"]):
                        yield {
                            "type": "completed",
                            "results": {
                                "repository_url": repository_url,
                                "vulnerability_scan": {
                                    "status": "skipped",
                                    "reason": "govulncheck not available or failed"
                                },
                                "summary": "Vulnerability audit completed - vulnerability scanner unavailable"
                            }
                        }
                    else:
                        yield {
                            "type": "error",
                            "error": "; ".join(final_state["errors"])
                        }
                elif final_state["vulnerabilities_found"] == 0:
                    yield {
                        "type": "completed",
                        "results": {
                            "repository_url": repository_url,
                            "vulnerability_scan": {
                                "status": "completed",
                                "vulnerabilities_found": 0,
                                "raw_output": final_state.get("govulncheck_output", "")
                            },
                            "github_pr": {
                                "success": True,
                                "action": "none_needed",
                                "message": "No vulnerabilities found - no PR needed",
                                "vulnerabilities_fixed": 0
                            },
                            "summary": "Vulnerability audit completed - no vulnerabilities found"
                        }
                    }
                else:
                    yield {
                        "type": "completed",
                        "results": {
                            "repository_url": repository_url,
                            "vulnerability_scan": {
                                "status": "completed",
                                "raw_output": final_state.get("govulncheck_output", ""),
                                "vulnerabilities_found": final_state["vulnerabilities_found"],
                                "ai_fixes_generated": True,
                                "ai_fix_explanation": final_state["fix_result"].fix_explanation if final_state["fix_result"] else ""
                            },
                            "build_validation": {
                                "success": final_state["build_result"].success if final_state["build_result"] else False,
                                "duration": final_state["build_result"].duration if final_state["build_result"] else 0,
                                "build_output": final_state["build_result"].build_output if final_state["build_result"] else ""
                            },
                            "github_pr": final_state.get("pr_result", {}),
                            "summary": f"Vulnerability audit completed - {final_state['vulnerabilities_found']} vulnerabilities found, AI fixes generated, build validated, and PR {'simulated' if settings.GITHUB_DRY_RUN else 'created'}"
                        }
                    }
                    
        except Exception as e:
            logger.error(f"Vulnerability audit failed: {e}")
            yield {
                "type": "error",
                "error": f"Vulnerability audit failed: {str(e)}"
            }
        finally:
            if hasattr(self, 'temp_dir') and self.temp_dir and os.path.exists(self.temp_dir):
                cleanup_success = repository_service.cleanup_directory(self.temp_dir)
                if not cleanup_success:
                    repository_service.schedule_delayed_cleanup(self.temp_dir)
                logger.info(f"Cleaned up temp directory: {self.temp_dir}")
                self.temp_dir = None 
