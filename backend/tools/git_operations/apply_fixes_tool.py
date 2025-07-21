import os
import re
import time
import json
from typing import Dict
from langchain_core.messages import SystemMessage, HumanMessage
from utils.async_tool_decorator import async_tool
from utils.logging_config import get_logger
from models.api_models import StandardToolResponse, StandardMetrics, StandardError
from config.settings import settings
from langchain_openai import ChatOpenAI

logger = get_logger(__name__)

@async_tool
async def apply_fixes(repository_path: str, prompt: str) -> StandardToolResponse:
    """Apply file changes to Go repository based on human-readable prompt using AI analysis.
    
    This tool takes a human-readable description of desired changes and uses AI to analyze 
    the repository context and implement the requested modifications. It handles any type 
    of Go repository changes including dependency updates, code modifications, and vulnerability fixes.
    
    Prerequisites: Repository must be cloned locally (Go repository)
    Often followed by: create_pull_request to commit and submit the applied changes
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
        
        # Read relevant files for AI context
        file_contents = _read_go_repository_files(repository_path)
        logger.info(f"Read {len(file_contents)} files for AI context")
        
        # Send to AI for analysis
        ai_response = await _send_to_ai(prompt, file_contents)
        logger.info("Received AI analysis response")
        logger.debug(f"Raw AI response: {ai_response}")
        
        # Parse AI response
        fix_result = _parse_ai_response(ai_response)
        
        if not fix_result.success:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return StandardToolResponse(
                status="error",
                tool_name="apply_fixes",
                data={
                    "action": "ai_analysis_failed",
                    "files_modified": 0,
                    "files_failed": 0,
                    "ai_explanation": fix_result.fix_explanation
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
                    "build_error": build_result.error_message
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
            "build_validation": {
                "success": build_result.success,
                "duration": build_result.duration,
                "build_output": build_result.build_output,
                "go_sum_updated": build_result.updated_go_sum is not None
            }
        }
        
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
    """Read relevant Go repository files for AI analysis."""
    files_to_read = []
    file_contents = {}
    
    # Only include Go module files
    essential_files = ["go.mod", "go.sum"]
    
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
        model="gpt-4", 
        temperature=0, 
        api_key=settings.OPENAI_API_KEY
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

