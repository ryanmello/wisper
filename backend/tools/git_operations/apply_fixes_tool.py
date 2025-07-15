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
async def apply_fixes(repository_path: str, changes: str) -> StandardToolResponse:
    """Apply file changes to repository based on analysis results and fix recommendations.
    
    This tool applies structured changes to repository files. It handles both complete file 
    operations (create/modify/delete), text-based modifications, and raw govulncheck output
    for automatic Go vulnerability fixes using AI analysis.
    
    Prerequisites: Repository must be cloned locally
    Often followed by: create_pull_request to commit and submit the applied changes
    Compatible with: scan_go_vulnerabilities tool output can be passed directly as changes parameter
    
    Args:
        repository_path: Path to the cloned repository where changes should be applied
        changes: Either:
                1. Raw govulncheck output string (detected automatically and processed by AI)
                2. JSON string describing changes to apply:
                   {"files": [{"path": "file.py", "action": "create|modify|delete", "content": "..."}]}
                
    Returns:
        StandardToolResponse with applied changes status, files modified, and summary of operations
    """
    start_time = time.time()
    logger.info(f"Applying changes to repository: {repository_path}")
    
    try:
        # Check if input is govulncheck output
        if isinstance(changes, str) and _is_govulncheck_output(changes):
            logger.info("Detected govulncheck output, using AI analysis to generate fixes...")
            return await _handle_go_vulnerabilities_with_ai(repository_path, changes, start_time)
        
        # Handle structured changes (JSON format)
        if isinstance(changes, str):
            try:
                changes = json.loads(changes)
            except json.JSONDecodeError:
                execution_time_ms = int((time.time() - start_time) * 1000)
                return StandardToolResponse(
                    status="error",
                    tool_name="apply_fixes",
                    data={"action": "validation_failed", "files_modified": 0, "files_failed": 0},
                    error=StandardError(
                        message="Invalid input format",
                        details="Input must be either govulncheck output or valid JSON with change information",
                        error_type="validation_error"
                    ),
                    summary="Change application failed - invalid input format",
                    metrics=StandardMetrics(execution_time_ms=execution_time_ms)
                )
        
        # Apply structured changes
        return _apply_structured_changes(repository_path, changes, start_time)
        
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

def _is_govulncheck_output(text: str) -> bool:
    """Detect if the input text is govulncheck output."""
    patterns = [
        r"Vulnerability #\d+:",
        r"Found in:.*@",
        r"Fixed in:.*@",
        r"Your code is affected by \d+ vulnerabilities",
        r"More info: https://pkg\.go\.dev/vuln/"
    ]
    
    for pattern in patterns:
        if re.search(pattern, text):
            return True
    return False

async def _handle_go_vulnerabilities_with_ai(repository_path: str, govulncheck_output: str, start_time: float) -> StandardToolResponse:
    """Handle Go vulnerability fixes using AI analysis."""
    try:
        logger.info("Starting AI-based Go vulnerability analysis and fixing")
        
        # Read relevant files for AI context
        file_contents = _read_relevant_files(repository_path, govulncheck_output)
        logger.info(f"Read {len(file_contents)} files for AI context")
        
        # Send to AI for analysis
        ai_response = await _send_to_ai(govulncheck_output, file_contents)
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
                    message="AI could not generate safe vulnerability fixes",
                    details=fix_result.fix_explanation,
                    error_type="ai_analysis_error"
                ),
                summary="Go vulnerability fixing failed - AI could not generate safe fixes",
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
                    message="AI-generated fixes failed build validation",
                    details=f"Build validation failed: {build_result.error_message}",
                    error_type="build_validation_error"
                ),
                summary="Go vulnerability fixing failed - fixes would break the build",
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
            summary = f"Successfully applied AI-generated Go vulnerability fixes to {len(applied_files)} files"
        elif applied_files and failed_files:
            summary = f"Applied fixes to {len(applied_files)} files, {len(failed_files)} files failed"
        else:
            summary = f"Failed to apply AI-generated fixes - {len(failed_files)} files failed"
        
        # Prepare response data
        response_data = {
            "action": "applied_ai_vulnerability_fixes",
            "files_modified": len(applied_files),
            "files_failed": len(failed_files),
            "vulnerabilities_addressed": fix_result.vulnerabilities_addressed,
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
                items_processed=fix_result.vulnerabilities_addressed,
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
            data={"action": "ai_vulnerability_error", "files_modified": 0, "files_failed": 0},
            error=StandardError(
                message=f"AI vulnerability processing failed: {str(e)}",
                details="An error occurred while using AI to process govulncheck output and apply fixes",
                error_type="ai_vulnerability_processing_error"
            ),
            summary="AI-based Go vulnerability fix application failed",
            metrics=StandardMetrics(execution_time_ms=execution_time_ms)
        )

def _read_relevant_files(repository_path: str, govulncheck_output: str) -> Dict[str, str]:
    """Read files that are relevant for AI analysis of Go vulnerabilities."""
    files_to_read = []
    file_contents = {}
    
    files = ["go.mod", "go.sum"]
    
    for file_path in files:
        full_path = os.path.join(repository_path, file_path)
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Limit file size to prevent token overflow
                    if len(content) > 10000:  # Limit to ~10KB per file
                        content = content[:10000] + "\n... [truncated due to size] ..."
                    file_contents[file_path] = content
                    files_to_read.append(file_path)
                    logger.info(f"Read file {file_path} ({len(content)} chars)")
            except Exception as e:
                logger.warning(f"Failed to read {file_path}: {e}")
                continue
    
    logger.info(f"Successfully read {len(file_contents)} files: {files_to_read}")
    return file_contents

async def _send_to_ai(govulncheck_output: str, file_contents: Dict[str, str]) -> str:
    """Send vulnerability data to AI for analysis and fix generation."""
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
    6. If some vulnerabilities cannot be safely fixed, explain why

    You can fix these types of vulnerabilities:

    1. **STANDARD LIBRARY vulnerabilities** (syscall, crypto/x509, net/http, etc.):
    - Fix by updating the Go version in go.mod (e.g., "go 1.24.4")
    - Example: syscall@go1.24.2 → Fixed in: syscall@go1.24.4 means update to "go 1.24.4"

    2. **MODULE DEPENDENCY vulnerabilities** (golang.org/x/net, etc.):
    - Fix by updating dependency versions in the require section
    - Example: golang.org/x/net@v0.34.0 → Fixed in: v0.38.0 means update to "golang.org/x/net v0.38.0"

    GO MODULE NOTES:
    - When updating dependencies in go.mod, the system will automatically run 'go mod tidy' if needed to resolve go.sum entries
    - This means you can safely update go.mod dependencies and the build validation will handle go.sum updates
    - Focus on providing clean, minimal go.mod updates

    IMPORTANT: Only apply fixes that you are confident are safe and won't break the build.
    ALWAYS return valid JSON - no extra text outside the JSON block

    Output Format - MUST be valid JSON:
    ```json
    {
        "success": true,
        "updated_files": {
            "go.mod": "module example.com/myapp\\n\\ngo 1.24.4\\n\\nrequire (\\n\\tgolang.org/x/net v0.38.0\\n\\tother-dependency v1.2.3\\n)"
        },
        "fix_explanation": "Updated Go version to 1.24.4 to fix syscall and crypto/x509 vulnerabilities. Updated golang.org/x/net to v0.38.0 to fix HTML injection vulnerability. All 3 vulnerabilities have been addressed.",
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

    Please provide safe fixes following the conservative approach outlined in the system prompt. Focus on dependency updates in go.mod when possible, and only modify other files if absolutely necessary for the fix.

    Please provide fixes following the JSON format specified in the system prompt."""

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
    """Result of AI vulnerability fix analysis."""
    def __init__(self, success: bool, updated_files: Dict[str, str], fix_explanation: str, 
                 vulnerabilities_addressed: int, error_message: str = None):
        self.success = success
        self.updated_files = updated_files
        self.fix_explanation = fix_explanation
        self.vulnerabilities_addressed = vulnerabilities_addressed
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

def _apply_structured_changes(repository_path: str, changes: dict, start_time: float) -> StandardToolResponse:
    """Apply structured changes from JSON format."""
    applied_files = []
    failed_files = []
    
    # Validate changes structure
    if not changes or not isinstance(changes, dict) or "files" not in changes:
        execution_time_ms = int((time.time() - start_time) * 1000)
        return StandardToolResponse(
            status="error",
            tool_name="apply_fixes",
            data={"action": "validation_failed", "files_modified": 0, "files_failed": 0},
            error=StandardError(
                message="Invalid changes format",
                details="Changes must be a dictionary with 'files' key containing file operations",
                error_type="validation_error"
            ),
            summary="Change application failed - invalid format",
            metrics=StandardMetrics(execution_time_ms=execution_time_ms)
        )
    
    # Handle file operations
    logger.info(f"Processing {len(changes['files'])} file operations")
    
    for file_change in changes["files"]:
        file_path = file_change["path"]
        action = file_change["action"]
        
        try:
            full_path = os.path.join(repository_path, file_path)
            
            if action in ["create", "modify"]:
                # Ensure directory exists
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                
                # Write new content
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(file_change["content"])
                
                applied_files.append({
                    "file": file_path,
                    "action": action,
                    "status": "success"
                })
                logger.info(f"Applied {action} to {file_path}")
                
            elif action == "delete":
                if os.path.exists(full_path):
                    os.remove(full_path)
                    applied_files.append({
                        "file": file_path,
                        "action": "delete",
                        "status": "success"
                    })
                    logger.info(f"Deleted {file_path}")
                else:
                    logger.warning(f"File {file_path} does not exist, skipping deletion")
            
        except Exception as e:
            logger.error(f"Failed to apply {action} to {file_path}: {e}")
            failed_files.append({
                "file": file_path,
                "action": action,
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
        summary = f"Successfully applied changes to {len(applied_files)} files"
    elif applied_files and failed_files:
        summary = f"Applied changes to {len(applied_files)} files, {len(failed_files)} files failed"
    else:
        summary = f"Failed to apply changes - {len(failed_files)} files failed"
    
    # Prepare response data
    response_data = {
        "action": "applied_structured_changes",
        "files_modified": len(applied_files),
        "files_failed": len(failed_files),
        "applied_files": applied_files,
        "failed_files": failed_files
    }
    
    # Add error information if there were failures
    error_info = None
    if failed_files:
        error_details = f"Failed to apply changes to {len(failed_files)} files"
        error_info = StandardError(
            message="Some file changes failed to apply",
            details=error_details,
            error_type="file_operation_error"
        )
    
    return StandardToolResponse(
        status=status,
        tool_name="apply_fixes",
        data=response_data,
        error=error_info,
        summary=summary,
        metrics=StandardMetrics(
            items_processed=len(applied_files) + len(failed_files),
            files_analyzed=len(applied_files) + len(failed_files),
            execution_time_ms=execution_time_ms
        )
    ) 
