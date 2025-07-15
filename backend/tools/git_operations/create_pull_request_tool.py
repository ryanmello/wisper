import os
import time
from datetime import datetime
from langchain_core.tools import tool
from git import Repo
from utils.logging_config import get_logger
from services.github_service import github_service
from config.settings import settings
from models.api_models import StandardToolResponse, StandardMetrics, StandardError

logger = get_logger(__name__)

@tool
def create_pull_request(repository_path: str, branch_name: str, title: str, description: str, commit_message: str) -> StandardToolResponse:
    """Create a pull request for already-modified files in the repository.
    
    This tool creates a new branch, commits existing changes, and opens a pull request on the original repository. 
    It assumes files have already been modified by other tools (typically apply_fixes tool) and focuses on the 
    git operations: commit → push → create PR.
    
    Prerequisites: Repository must be cloned; files should already be modified by other tools
    Common workflow: analyze_issues → apply_fixes → create_pull_request
    
    Args:
        repository_path: Path to the cloned repository with modified files
        branch_name: Name for the new branch containing the changes
        title: Title for the pull request
        description: Detailed description of the changes and their purpose
        commit_message: Descriptive commit message for the changes
        
    Returns:
        StandardToolResponse with pull request URL, status, and details of the created PR
    """
    start_time = time.time()
    logger.info(f"Creating pull request for {repository_path}")
    
    try:
        if not os.path.exists(repository_path):
            execution_time_ms = int((time.time() - start_time) * 1000)
            return StandardToolResponse(
                status="error",
                tool_name="create_pull_request",
                data={
                    "action": "validation_failed",
                    "repository_path": repository_path,
                    "branch_name": branch_name
                },
                error=StandardError(
                    message=f"Repository path does not exist: {repository_path}",
                    details="The specified repository path could not be found",
                    error_type="path_not_found_error"
                ),
                summary="Pull request creation failed - repository path not found",
                metrics=StandardMetrics(
                    execution_time_ms=execution_time_ms
                )
            )
        
        # Check if running in dry run mode
        if settings.GITHUB_DRY_RUN:
            execution_time_ms = int((time.time() - start_time) * 1000)
            logger.info("Running in GitHub dry run mode")
            
            # Create unique branch name with timestamp for dry run too
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            unique_branch_name = f"{branch_name}-{timestamp}"
            
            return StandardToolResponse(
                status="success",
                tool_name="create_pull_request", 
                data={
                    "action": "dry_run",
                    "simulated_pr": {
                        "title": title,
                        "branch": unique_branch_name,
                        "original_branch_name": branch_name,
                        "commit_message": commit_message,
                        "description": description,
                        "timestamp_used": timestamp
                    }
                },
                summary="GitHub dry run mode - PR creation simulated successfully",
                metrics=StandardMetrics(
                    items_processed=1,
                    execution_time_ms=execution_time_ms
                ),
                warnings=["Running in dry run mode - no actual PR was created"]
            )
        
        try:
            repo = Repo(repository_path)
            remote_url = repo.remote('origin').url
        except Exception as e:
            execution_time_ms = int((time.time() - start_time) * 1000)
            return StandardToolResponse(
                status="error",
                tool_name="create_pull_request",
                data={
                    "action": "git_error",
                    "repository_path": repository_path
                },
                error=StandardError(
                    message=f"Failed to get remote URL from repository",
                    details=f"Git operation failed: {str(e)}",
                    error_type="git_repository_error"
                ),
                summary="Pull request creation failed - could not access git repository",
                metrics=StandardMetrics(
                    execution_time_ms=execution_time_ms
                )
            )
        
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_branch_name = f"{branch_name}-{timestamp}"
        logger.info(f"Using timestamped branch name: {unique_branch_name}")
        
        pr_result = github_service.create_pull_request(
            repo_url=remote_url,
            branch_name=unique_branch_name,
            title=title,
            description=description,
            clone_path=repository_path,
            commit_message=commit_message
        )
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        if pr_result.get("status") == "success":
            logger.info(f"Successfully created pull request: {pr_result.get('pr_url')}")
            
            return StandardToolResponse(
                status="success",
                tool_name="create_pull_request",
                data={
                    "action": "created",
                    "pr_url": pr_result.get("pr_url"),
                    "pr_number": pr_result.get("pr_number"),
                    "branch": unique_branch_name,
                    "base_branch": pr_result.get("base_branch"),
                    "commit_message": commit_message,
                    "title": title,
                    "description": description,
                    "original_branch_name": branch_name,
                    "timestamp_used": timestamp
                },
                summary=f"Successfully created pull request #{pr_result.get('pr_number')}: {title}",
                metrics=StandardMetrics(
                    items_processed=1,
                    execution_time_ms=execution_time_ms
                )
            )
        else:
            logger.error(f"Failed to create pull request: {pr_result.get('error')}")
            
            return StandardToolResponse(
                status="error",
                tool_name="create_pull_request",
                data={
                    "action": "creation_failed",
                    "branch_name": unique_branch_name,
                    "original_branch_name": branch_name,
                    "title": title
                },
                error=StandardError(
                    message="Pull request creation failed",
                    details=pr_result.get("error", "Unknown error occurred during PR creation"),
                    error_type="pr_creation_error"
                ),
                summary="Pull request creation failed",
                metrics=StandardMetrics(
                    execution_time_ms=execution_time_ms
                )
            )
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Failed to create pull request: {e}")
        
        # Create unique branch name for error reporting (if not already created)
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        unique_branch_name = f"{branch_name}-{timestamp}"
        
        return StandardToolResponse(
            status="error",
            tool_name="create_pull_request",
            data={
                "action": "unexpected_error",
                "branch_name": unique_branch_name,
                "original_branch_name": branch_name,
                "title": title
            },
            error=StandardError(
                message=f"Unexpected error during pull request creation: {str(e)}",
                details=f"An unexpected error occurred while creating pull request for branch '{unique_branch_name}'",
                error_type="unexpected_error"
            ),
            summary="Pull request creation failed with unexpected error",
            metrics=StandardMetrics(
                execution_time_ms=execution_time_ms
            )
        )
