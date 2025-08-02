import os
import re
import time
import json
from typing import Dict, List
from dataclasses import dataclass
from langchain_core.messages import SystemMessage, HumanMessage
from utils.async_tool_decorator import async_tool
from utils.tool_metadata_decorator import tool_category
from utils.logging_config import get_logger
from models.api_models import StandardToolResponse, StandardMetrics, StandardError
from config.settings import settings
from langchain_openai import ChatOpenAI

logger = get_logger(__name__)

@dataclass
class VulnerabilityInfo:
    """Represents a parsed vulnerability from govulncheck output."""
    vuln_id: str
    description: str
    module_name: str
    current_version: str
    fixed_version: str
    is_standard_library: bool = False
    
    def __str__(self):
        return f"{self.vuln_id}: {self.module_name}@{self.current_version} → {self.fixed_version}"

@dataclass
class GovulncheckResult:
    """Result of parsing govulncheck output."""
    is_govulncheck: bool
    vulnerabilities: List[VulnerabilityInfo]
    original_prompt: str
    
class GovulncheckParser:
    """Parser for govulncheck command output to extract structured vulnerability information."""
    
    # Regex patterns for detecting govulncheck output
    VULN_HEADER_PATTERN = re.compile(r'Vulnerability #(\d+): (GO-\d+-\d+)')
    FOUND_IN_PATTERN = re.compile(r'Found in:\s+(.+?)@(.+?)(?:\s|$)')
    FIXED_IN_PATTERN = re.compile(r'Fixed in:\s+(.+?)@(.+?)(?:\s|$)')
    STANDARD_LIB_PATTERN = re.compile(r'Standard library')
    
    @classmethod
    def detect_govulncheck_output(cls, prompt: str) -> bool:
        """Detect if the input appears to be govulncheck output."""
        # Look for key govulncheck indicators
        has_vulnerability_header = "Vulnerability #" in prompt
        has_found_fixed_pattern = "Found in:" in prompt and "Fixed in:" in prompt
        has_vuln_id = "GO-20" in prompt  # Vulnerability ID pattern like GO-2025-3770
        
        # Need at least 2 indicators to confidently identify govulncheck output
        indicators = [has_vulnerability_header, has_found_fixed_pattern, has_vuln_id]
        return sum(indicators) >= 2
    
    @classmethod
    def parse_govulncheck_output(cls, prompt: str) -> GovulncheckResult:
        """Parse govulncheck output into structured vulnerability information."""
        if not cls.detect_govulncheck_output(prompt):
            return GovulncheckResult(
                is_govulncheck=False,
                vulnerabilities=[],
                original_prompt=prompt
            )
        
        vulnerabilities = []
        lines = prompt.split('\n')
        current_vuln = None
        current_description = ""
        is_standard_lib = False
        
        for line in lines:
            line = line.strip()
            
            # Check for vulnerability header (e.g., "Vulnerability #1: GO-2025-3770")
            vuln_match = cls.VULN_HEADER_PATTERN.search(line)
            if vuln_match:
                # Save previous vulnerability if exists
                if current_vuln:
                    vulnerabilities.append(current_vuln)
                
                vuln_id = vuln_match.group(2)
                # Extract description from the rest of the line
                desc_start = line.find(vuln_id) + len(vuln_id)
                current_description = line[desc_start:].strip()
                current_vuln = None
                is_standard_lib = False
                continue
            
            # Check for standard library indicator
            if cls.STANDARD_LIB_PATTERN.search(line):
                is_standard_lib = True
                continue
            
            # Look for Found in and Fixed in patterns
            found_match = cls.FOUND_IN_PATTERN.search(line)
            fixed_match = cls.FIXED_IN_PATTERN.search(line)
            
            if found_match and fixed_match:
                # Both patterns in same line
                module_name = found_match.group(1)
                current_version = found_match.group(2)
                fixed_version = fixed_match.group(2)
                
                current_vuln = VulnerabilityInfo(
                    vuln_id=vuln_id,
                    description=current_description,
                    module_name=module_name,
                    current_version=current_version,
                    fixed_version=fixed_version,
                    is_standard_library=is_standard_lib
                )
            elif found_match:
                # Only found pattern, look for fixed in subsequent lines
                module_name = found_match.group(1)
                current_version = found_match.group(2)
                
                # Look ahead for Fixed in pattern
                current_line_index = lines.index(line)
                for next_line in lines[current_line_index+1:current_line_index+5]:
                    fixed_match = cls.FIXED_IN_PATTERN.search(next_line.strip())
                    if fixed_match:
                        fixed_version = fixed_match.group(2)
                        current_vuln = VulnerabilityInfo(
                            vuln_id=vuln_id,
                            description=current_description,
                            module_name=module_name,
                            current_version=current_version,
                            fixed_version=fixed_version,
                            is_standard_library=is_standard_lib
                        )
                        break
        
        # Add the last vulnerability if exists
        if current_vuln:
            vulnerabilities.append(current_vuln)
        
        logger.info(f"Parsed {len(vulnerabilities)} vulnerabilities from govulncheck output")
        for vuln in vulnerabilities:
            logger.info(f"  - {vuln}")
        
        return GovulncheckResult(
            is_govulncheck=True,
            vulnerabilities=vulnerabilities,
            original_prompt=prompt
        )

@tool_category("git_operations")
@async_tool
async def apply_fixes(repository_path: str, prompt: str) -> StandardToolResponse:
    """Apply file changes to a repository.
        
    This tool takes a human-readable description of desired changes and uses AI to analyze 
    the repository context and implement the requested modifications. It handles any type 
    of Go repository changes including dependency updates, code modifications, and vulnerability fixes.
    
    Prerequisites: Repository must be cloned locally
    Compatible with: Human-readable prompts from Veda or raw govulncheck output
    
    Args:
        repository_path: Path to the cloned Go repository where changes should be applied
        prompt: Human-readable description of desired changes, such as:
               - "Update golang.org/x/net package from v0.34.0 to v0.42.0"
               - "Fix the vulnerability in the authentication handler"
               - Raw govulncheck output describing security issues
                
    Returns:
        StandardToolResponse with applied changes status, files modified, and summary of operations
    """
    start_time = time.time()
    logger.info(f"Applying changes to Go repository: {repository_path}")
    logger.info(f"User prompt: {prompt}")
    
    try:
        # Always use AI analysis to process the human-readable prompt
        logger.info("Processing prompt with AI analysis to generate fixes...")
        return await _handle_go_changes_with_ai(repository_path, prompt, start_time)
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Failed to apply changes: {e}")
        
        return StandardToolResponse(
            status="error",
            tool_name="apply_fixes",
            data={
                "action": "unexpected_error",
                "files_modified": 0,
                "files_failed": 0
            },
            error=StandardError(
                message=f"Unexpected error during change application: {str(e)}",
                details=f"An unexpected error occurred while applying changes to {repository_path}",
                error_type="unexpected_error"
            ),
            summary="Change application failed with unexpected error",
            metrics=StandardMetrics(
                execution_time_ms=execution_time_ms
            )
        )

async def _handle_go_changes_with_ai(repository_path: str, prompt: str, start_time: float) -> StandardToolResponse:
    """Handle Go repository changes using AI analysis."""
    try:
        logger.info("Starting AI-based Go repository analysis and modification")
        
        # Check if this is govulncheck output and parse it
        govulncheck_result = GovulncheckParser.parse_govulncheck_output(prompt)
        
        # Read relevant files for AI context
        file_contents = _read_go_repository_files(repository_path)
        logger.info(f"Read {len(file_contents)} files for AI context")
        
        # Send to AI for analysis using appropriate prompt strategy
        if govulncheck_result.is_govulncheck:
            logger.info(f"Detected govulncheck output with {len(govulncheck_result.vulnerabilities)} vulnerabilities")
            ai_response = await _send_structured_vulnerabilities_to_ai(govulncheck_result, file_contents)
        else:
            logger.info("Processing as human-readable prompt")
            ai_response = await _send_to_ai(prompt, file_contents)
        
        logger.info("Received AI analysis response")
        logger.debug(f"Raw AI response: {ai_response}")
        
        # Parse AI response
        fix_result = _parse_ai_response(ai_response)
        
        # Additional validation for govulncheck-based fixes
        if govulncheck_result.is_govulncheck:
            validation_result = _validate_govulncheck_fixes(govulncheck_result.vulnerabilities, fix_result)
            if not validation_result.success:
                logger.warning(f"Govulncheck fix validation failed: {validation_result.message}")
                # Add validation warning to fix explanation
                fix_result.fix_explanation = f"{fix_result.fix_explanation}\n\nValidation Warning: {validation_result.message}"
        
        if not fix_result.success:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return StandardToolResponse(
                status="error",
                tool_name="apply_fixes",
                data={
                    "action": "ai_analysis_failed",
                    "files_modified": 0,
                    "files_failed": 0,
                    "ai_explanation": fix_result.fix_explanation,
                    "govulncheck_detected": govulncheck_result.is_govulncheck,
                    "vulnerabilities_found": len(govulncheck_result.vulnerabilities) if govulncheck_result.is_govulncheck else 0
                },
                error=StandardError(
                    message="AI could not generate safe repository changes",
                    details=fix_result.fix_explanation,
                    error_type="ai_analysis_error"
                ),
                summary="Go repository modification failed - AI could not generate safe changes",
                metrics=StandardMetrics(execution_time_ms=execution_time_ms)
            )
        
        # Validate fixes with go build before applying permanently
        logger.info("Validating AI-generated fixes with go build...")
        from utils.build_validator import BuildValidator
        
        build_validator = BuildValidator()
        build_result = build_validator.validate_fixes(repository_path, fix_result.updated_files)
        
        if not build_result.success:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return StandardToolResponse(
                status="error",
                tool_name="apply_fixes",
                data={
                    "action": "build_validation_failed",
                    "files_modified": 0,
                    "files_failed": 0,
                    "ai_explanation": fix_result.fix_explanation,
                    "build_output": build_result.build_output,
                    "build_error": build_result.error_message,
                    "govulncheck_detected": govulncheck_result.is_govulncheck,
                    "vulnerabilities_found": len(govulncheck_result.vulnerabilities) if govulncheck_result.is_govulncheck else 0
                },
                error=StandardError(
                    message="AI-generated changes failed build validation",
                    details=f"Build validation failed: {build_result.error_message}",
                    error_type="build_validation_error"
                ),
                summary="Go repository modification failed - changes would break the build",
                metrics=StandardMetrics(execution_time_ms=execution_time_ms)
            )
        
        logger.info(f"Build validation passed in {build_result.duration:.2f}s")
        
        # If build validation captured an updated go.sum, include it in the fixes
        if build_result.updated_go_sum and "go.sum" not in fix_result.updated_files:
            fix_result.updated_files["go.sum"] = build_result.updated_go_sum
            logger.info("Added updated go.sum from build validation to fixes")
        
        # Apply the AI-generated fixes
        applied_files = []
        failed_files = []
        
        for file_path, content in fix_result.updated_files.items():
            try:
                full_path = os.path.join(repository_path, file_path)
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write updated content
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                applied_files.append({
                    "file": file_path,
                    "action": "ai_generated_fix",
                    "status": "success"
                })
                logger.info(f"Applied AI-generated fix to {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to apply AI fix to {file_path}: {e}")
                failed_files.append({
                    "file": file_path,
                    "action": "ai_generated_fix",
                    "error": str(e)
                })
        
        # Calculate execution time and create response
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Determine status
        if failed_files and applied_files:
            status = "partial_success"
        elif failed_files:
            status = "error"
        else:
            status = "success"
        
        # Create summary message
        if applied_files and not failed_files:
            if govulncheck_result.is_govulncheck:
                summary = f"Successfully applied fixes for {len(govulncheck_result.vulnerabilities)} vulnerabilities to {len(applied_files)} files"
            else:
                summary = f"Successfully applied AI-generated Go repository changes to {len(applied_files)} files"
        elif applied_files and failed_files:
            summary = f"Applied changes to {len(applied_files)} files, {len(failed_files)} files failed"
        else:
            summary = f"Failed to apply AI-generated changes - {len(failed_files)} files failed"
        
        # Prepare response data
        response_data = {
            "action": "applied_ai_repository_changes",
            "files_modified": len(applied_files),
            "files_failed": len(failed_files),
            "changes_made": fix_result.changes_made,
            "applied_files": applied_files,
            "failed_files": failed_files,
            "fix_explanation": fix_result.fix_explanation,
            "govulncheck_detected": govulncheck_result.is_govulncheck,
            "vulnerabilities_addressed": len(govulncheck_result.vulnerabilities) if govulncheck_result.is_govulncheck else 0,
            "build_validation": {
                "success": build_result.success,
                "duration": build_result.duration,
                "build_output": build_result.build_output,
                "go_sum_updated": build_result.updated_go_sum is not None
            }
        }
        
        # Add vulnerability details if this was govulncheck output
        if govulncheck_result.is_govulncheck:
            response_data["vulnerabilities"] = [
                {
                    "vuln_id": vuln.vuln_id,
                    "description": vuln.description,
                    "module": vuln.module_name,
                    "current_version": vuln.current_version,
                    "fixed_version": vuln.fixed_version,
                    "is_standard_library": vuln.is_standard_library
                }
                for vuln in govulncheck_result.vulnerabilities
            ]
        
        # Add error information if there were failures
        error_info = None
        if failed_files:
            error_details = f"Failed to apply AI fixes to {len(failed_files)} files"
            error_info = StandardError(
                message="Some AI-generated fixes failed to apply",
                details=error_details,
                error_type="ai_fix_application_error"
            )
        
        return StandardToolResponse(
            status=status,
            tool_name="apply_fixes",
            data=response_data,
            error=error_info,
            summary=summary,
            metrics=StandardMetrics(
                items_processed=fix_result.changes_made,
                files_analyzed=len(applied_files) + len(failed_files),
                execution_time_ms=execution_time_ms
            )
        )
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Failed to handle Go vulnerabilities with AI: {e}")
        
        return StandardToolResponse(
            status="error",
            tool_name="apply_fixes",
            data={"action": "ai_processing_error", "files_modified": 0, "files_failed": 0},
            error=StandardError(
                message=f"AI repository processing failed: {str(e)}",
                details="An error occurred while using AI to process the prompt and apply changes",
                error_type="ai_processing_error"
            ),
            summary="AI-based Go repository modification failed",
            metrics=StandardMetrics(execution_time_ms=execution_time_ms)
        )

def _read_go_repository_files(repository_path: str) -> Dict[str, str]:
    """Read go.mod file for AI analysis. go.sum will be regenerated by go mod tidy."""
    files_to_read = []
    file_contents = {}
    
    # Only include go.mod - go.sum will be regenerated automatically
    essential_files = ["go.mod"]
    
    for file_path in essential_files:
        full_path = os.path.join(repository_path, file_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    file_contents[file_path] = content
                    files_to_read.append(file_path)
                    logger.info(f"Read file {file_path} ({len(content)} chars)")
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
                continue
    
    logger.info(f"Successfully read {len(file_contents)} files: {files_to_read}")
    return file_contents

async def _send_to_ai(prompt: str, file_contents: Dict[str, str]) -> str:
    """Send prompt and repository context to AI for analysis and change generation."""
    files_section = ""
    for file_path, content in file_contents.items():
        files_section += f"\n--- {file_path} ---\n{content}\n"
    
    system_prompt = """You are a Go development expert specializing in repository modifications.

    CRITICAL: YOU MUST PRESERVE ALL EXISTING DEPENDENCIES - NEVER REMOVE ANY require ENTRIES!

    CORE RULES:
    1. PRESERVE ALL existing dependencies (never remove require entries) - THIS IS MANDATORY
    2. Make minimal, targeted changes that fulfill the user's request
    3. For dependency updates: modify go.mod safely without removing other dependencies
    4. For code changes: modify only the necessary files and functions
    5. Always provide complete file content for any file you modify
    6. Be conservative - prefer safe, minimal changes

    GO.MOD REQUIREMENTS (when modifying go.mod):
    - PRESERVE ALL existing dependencies (never remove require entries) - CRITICAL
    - Provide COMPLETE go.mod structure (module, go version, require blocks)
    - Update versions in require sections (avoid replace directives)
    - Maintain proper formatting and indentation
    - Include ALL dependencies from the original file, even if not being updated

    TYPES OF CHANGES YOU CAN HANDLE:
    - Dependency updates (update specific packages in go.mod)
    - Security vulnerability fixes (update vulnerable dependencies)
    - Code modifications (add/modify/fix Go source code)
    - Configuration changes (update Go version, add new dependencies)
    - Bug fixes and feature implementations

    OUTPUT: Return valid JSON only, no extra text.

    Success format:
    ```json
    {
        "success": true,
        "updated_files": {
            "filename.go": "package main\\n\\nfunc main() {\\n\\t// updated code\\n}",
            "go.mod": "module example\\n\\ngo 1.24.4\\n\\nrequire (\\n\\tgithub.com/existing/dep1 v1.2.3\\n\\tgolang.org/x/net v0.38.0\\n\\tgithub.com/another/dep v1.0.0\\n)"
        },
        "fix_explanation": "Brief explanation of changes made",
        "changes_made": 2
    }
    ```

    Failure format:
    ```json
    {
        "success": false,
        "updated_files": {},
        "fix_explanation": "Why changes cannot be applied safely",
        "changes_made": 0
    }
    ```"""

    human_prompt = f"""Please analyze the user's request and implement the requested changes:

    USER REQUEST:
    {prompt}

    CURRENT REPOSITORY FILES:
    {files_section}
    
    Please implement the requested changes following the conservative approach outlined in the system prompt. 
    Focus on making minimal, safe changes that fulfill the user's request.
    
    If this is a dependency update request, modify go.mod while preserving all existing dependencies.
    If this is a code change request, modify only the necessary source files.
    If this is govulncheck output, treat it as a security vulnerability fix request.

    Please provide the changes following the JSON format specified in the system prompt."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ]
    
    logger.info("Sending vulnerability data to AI for analysis")
    
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0, 
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL
    )
    
    response = await llm.ainvoke(messages)
    return response.content

async def _send_structured_vulnerabilities_to_ai(govulncheck_result: GovulncheckResult, file_contents: Dict[str, str]) -> str:
    """Send structured vulnerability information to AI for analysis and change generation."""
    files_section = ""
    for file_path, content in file_contents.items():
        files_section += f"\n--- {file_path} ---\n{content}\n"
    
    # Create structured vulnerability summary
    vuln_summary = []
    go_version_updates = []
    dependency_updates = []
    
    for vuln in govulncheck_result.vulnerabilities:
        if vuln.is_standard_library:
            # Standard library vulnerability - need Go version update
            # Convert "go1.24.2" to "go 1.24.2" format to match go.mod
            current_formatted = vuln.current_version.replace("go", "go ", 1) if vuln.current_version.startswith("go") else vuln.current_version
            fixed_formatted = vuln.fixed_version.replace("go", "go ", 1) if vuln.fixed_version.startswith("go") else vuln.fixed_version
            go_version_updates.append(f"  - Update Go version from {current_formatted} to {fixed_formatted} (fixes {vuln.vuln_id})")
        else:
            # Third-party dependency update
            dependency_updates.append(f"  - Update {vuln.module_name} from {vuln.current_version} to {vuln.fixed_version} (fixes {vuln.vuln_id})")
    
    if go_version_updates:
        vuln_summary.append("STANDARD LIBRARY UPDATES NEEDED:")
        vuln_summary.extend(go_version_updates)
        vuln_summary.append("")
    
    if dependency_updates:
        vuln_summary.append("DEPENDENCY UPDATES NEEDED:")
        vuln_summary.extend(dependency_updates)
        vuln_summary.append("")
    
    vuln_text = "\n".join(vuln_summary)
    
    system_prompt = """You are a Go development expert specializing in security vulnerability fixes.

    CRITICAL: YOU MUST PRESERVE ALL EXISTING DEPENDENCIES - NEVER REMOVE ANY require ENTRIES!

    SECURITY FIX STRATEGY:
    1. PRESERVE ALL existing dependencies (never remove require entries) - THIS IS MANDATORY
    2. Update ONLY the vulnerable dependencies to their fixed versions
    3. For standard library vulnerabilities: Update the Go version in go.mod
    4. For dependency vulnerabilities: Update the specific module version in the require block
    5. Always provide complete file content for any file you modify
    6. Be conservative - make only the minimal changes needed to fix vulnerabilities

    GO.MOD MODIFICATION RULES:
    - PRESERVE ALL existing dependencies (never remove require entries) - CRITICAL
    - Provide COMPLETE go.mod structure (module, go version, require blocks)
    - Update ONLY the vulnerable module versions as specified
    - Update Go version if standard library vulnerabilities are present
    - Maintain proper formatting and indentation
    - Include ALL dependencies from the original file, even if not being updated

    EXAMPLES OF CORRECT FIXES:
    
    Example 1 - Third-party dependency update:
    Original: github.com/go-chi/chi/v5 v5.2.1
    Required: github.com/go-chi/chi/v5 v5.2.2
    
    Example 2 - Standard library fix (Go version update):
    Original: go 1.24.2
    Required: go 1.24.4 (to fix crypto/x509 and syscall vulnerabilities)
    
    Example 3 - Mixed updates:
    - Update go 1.24.2 → go 1.24.4 (fixes standard library vulns)
    - Update golang.org/x/net v0.34.0 → v0.38.0 (fixes dependency vuln)

    OUTPUT: Return valid JSON only, no extra text.

    Success format:
    ```json
    {
        "success": true,
        "updated_files": {
            "go.mod": "module example\\n\\ngo 1.24.4\\n\\nrequire (\\n\\tgithub.com/existing/dep1 v1.2.3\\n\\tgolang.org/x/net v0.38.0\\n\\tgithub.com/go-chi/chi/v5 v5.2.2\\n\\tgithub.com/another/dep v1.0.0\\n)"
        },
        "fix_explanation": "Updated Go version to 1.24.4 to fix standard library vulnerabilities and updated vulnerable dependencies to their fixed versions",
        "changes_made": 3
    }
    ```

    Failure format:
    ```json
    {
        "success": false,
        "updated_files": {},
        "fix_explanation": "Why changes cannot be applied safely",
        "changes_made": 0
    }
    ```"""

    human_prompt = f"""Please fix the following security vulnerabilities by updating the vulnerable dependencies:

    {vuln_text}

    CURRENT REPOSITORY FILES:
    {files_section}
    
    Please implement the EXACT vulnerability fixes specified above. For each vulnerability:
    1. Update the vulnerable module to its fixed version
    2. If standard library vulnerabilities are present, update the Go version accordingly
    3. Preserve ALL other existing dependencies unchanged
    
    Provide the complete updated go.mod file with all dependencies preserved and only the vulnerable ones updated to their fixed versions.

    Return your response in the JSON format specified in the system prompt."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=human_prompt)
    ]
    
    logger.info("Sending structured vulnerability data to AI for analysis")
    logger.info(f"Vulnerability summary: {len(govulncheck_result.vulnerabilities)} vulnerabilities")
    for vuln in govulncheck_result.vulnerabilities:
        logger.info(f"  - {vuln}")
    
    llm = ChatOpenAI(
        model=settings.OPENAI_MODEL,
        temperature=0, 
        api_key=settings.OPENAI_API_KEY,
        base_url=settings.OPENAI_BASE_URL
    )
    
    response = await llm.ainvoke(messages)
    return response.content

class FixResult:
    """Result of AI repository change analysis."""
    def __init__(self, success: bool, updated_files: Dict[str, str], fix_explanation: str, 
                changes_made: int, error_message: str = None):
        self.success = success
        self.updated_files = updated_files
        self.fix_explanation = fix_explanation
        self.changes_made = changes_made
        self.error_message = error_message

def _parse_ai_response(ai_response: str) -> FixResult:
    """Parse AI response and return FixResult."""
    try:
        # Look for JSON in code blocks first
        json_match = re.search(r'```json\s*\n(.*?)\n```', ai_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Try the entire response as JSON
            json_str = ai_response.strip()
        
        data = json.loads(json_str)
        
        return FixResult(
            success=data.get("success", False),
            updated_files=data.get("updated_files", {}),
            fix_explanation=data.get("fix_explanation", ""),
            changes_made=data.get("changes_made", 0)
        )
        
    except Exception as e:
        logger.error(f"Failed to parse AI response: {e}")
        logger.debug(f"AI response was: {ai_response}")
        
        return FixResult(
            success=False,
            updated_files={},
            fix_explanation=f"Failed to parse AI response: {str(e)}",
            changes_made=0,
            error_message=str(e)
        )

def _validate_govulncheck_fixes(vulnerabilities: List[VulnerabilityInfo], fix_result: FixResult) -> FixResult:
    """Validate if the AI-generated fixes are reasonable for the govulncheck output."""
    if not fix_result.success:
        return FixResult(
            success=False, 
            updated_files={}, 
            fix_explanation="AI failed to generate fixes.", 
            changes_made=0
        )

    # Basic validation: ensure go.mod is being updated for dependency fixes
    if not fix_result.updated_files.get("go.mod"):
        return FixResult(
            success=False,
            updated_files={},
            fix_explanation="Expected go.mod updates for vulnerability fixes, but none provided.",
            changes_made=0
        )

    # If we reach here, assume the AI did a reasonable job
    # More sophisticated validation could be added later if needed
    return FixResult(
        success=True, 
        updated_files=fix_result.updated_files, 
        fix_explanation="Vulnerability fixes appear reasonable.", 
        changes_made=fix_result.changes_made
    )

