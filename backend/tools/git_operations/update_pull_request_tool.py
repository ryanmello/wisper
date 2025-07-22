import os
import time
from typing import Dict, Optional
from utils.async_tool_decorator import async_tool
from utils.tool_metadata_decorator import tool_category
from utils.logging_config import get_logger
from models.api_models import StandardToolResponse, StandardMetrics, StandardError
from config.settings import settings

logger = get_logger(__name__)

@tool_category("git_operations")
@async_tool
async def update_pull_request(
    repository_path: str,
    pr_id: int,
    repo_owner: str,
    repo_name: str,
    commit_message: str,
    pr_comment: Optional[str] = None,
    update_title: Optional[str] = None,
    update_description: Optional[str] = None
) -> StandardToolResponse:
    """Update an existing GitHub pull request with new commits and/or comments.
    
    This tool handles GitHub pull request operations after files have been modified
    by other tools (like apply_fixes). It commits changes to the PR branch and
    optionally adds comments or updates PR metadata.
    
    Prerequisites: Repository must be cloned locally and files modified by apply_fixes
    Compatible with: apply_fixes tool output - use this after applying file changes
    
    Args:
        repository_path: Path to the cloned repository with modified files
        pr_id: Pull request number/ID to update
        repo_owner: Repository owner (GitHub username/organization)
        repo_name: Repository name
        commit_message: Message for the new commit
        pr_comment: Optional comment to add to the PR discussion
        update_title: Optional new title for the PR
        update_description: Optional new description for the PR
        
    Returns:
        StandardToolResponse with PR update status, commit info, and operation summary
    """
    start_time = time.time()
    logger.info(f"Updating pull request #{pr_id} in {repo_owner}/{repo_name}")
    logger.info(f"Repository path: {repository_path}")
    logger.info(f"Commit message: {commit_message}")
    logger.info(f"PR comment: {pr_comment}")
    logger.info(f"Repository path exists: {os.path.exists(repository_path) if repository_path else 'No path provided'}")
    
    try:
        # Validate inputs
        if not os.path.exists(repository_path):
            execution_time_ms = int((time.time() - start_time) * 1000)
            return StandardToolResponse(
                status="error",
                tool_name="update_pull_request",
                data={"action": "validation_failed", "pr_id": pr_id},
                error=StandardError(
                    message="Invalid repository path",
                    details=f"Repository path does not exist: {repository_path}",
                    error_type="validation_error"
                ),
                summary="PR update failed - invalid repository path",
                metrics=StandardMetrics(execution_time_ms=execution_time_ms)
            )
        
        operations_performed = []
        
        # Update PR metadata if requested
        if update_title or update_description:
            try:
                metadata_result = await _update_pr_metadata(
                    repo_owner, repo_name, pr_id, update_title, update_description
                )
                operations_performed.append(metadata_result)
                logger.info(f"Updated PR #{pr_id} metadata")
            except Exception as e:
                logger.error(f"Failed to update PR metadata: {e}")
                operations_performed.append({
                    "operation": "update_metadata",
                    "status": "failed",
                    "error": str(e)
                })
        
        # Commit and push changes to PR branch
        logger.info("About to call _commit_and_push_changes")
        try:
            commit_result = await _commit_and_push_changes(
                repository_path, repo_owner, repo_name, pr_id, commit_message
            )
            logger.info(f"_commit_and_push_changes returned: {commit_result}")
            operations_performed.append(commit_result)
        except Exception as e:
            logger.error(f"Exception in _commit_and_push_changes: {e}")
            commit_result = {
                "operation": "commit_and_push",
                "status": "failed", 
                "error": str(e)
            }
            operations_performed.append(commit_result)
        
        # Add comment to PR if requested
        if pr_comment:
            try:
                comment_result = await _add_pr_comment(
                    repo_owner, repo_name, pr_id, pr_comment
                )
                operations_performed.append(comment_result)
                logger.info(f"Added comment to PR #{pr_id}")
            except Exception as e:
                logger.error(f"Failed to add PR comment: {e}")
                operations_performed.append({
                    "operation": "add_comment",
                    "status": "failed",
                    "error": str(e)
                })
        
        # Determine overall status
        failed_operations = [op for op in operations_performed if op.get("status") == "failed"]
        successful_operations = [op for op in operations_performed if op.get("status") == "success"]
        
        if failed_operations and successful_operations:
            status = "partial_success"
        elif failed_operations:
            status = "error"
        else:
            status = "success"
        
        execution_time_ms = int((time.time() - start_time) * 1000)
        
        # Create summary
        if status == "success":
            summary = f"Successfully updated PR #{pr_id} with {len(successful_operations)} operations"
        elif status == "partial_success":
            summary = f"Partially updated PR #{pr_id}: {len(successful_operations)} succeeded, {len(failed_operations)} failed"
        else:
            summary = f"Failed to update PR #{pr_id}: {len(failed_operations)} operations failed"
        
        # Prepare response data
        response_data = {
            "action": "updated_pull_request",
            "pr_id": pr_id,
            "repository": f"{repo_owner}/{repo_name}",
            "operations_performed": operations_performed,
            "successful_operations": len(successful_operations),
            "failed_operations": len(failed_operations)
        }
        
        # Add error info if there were failures
        error_info = None
        if failed_operations:
            error_details = f"{len(failed_operations)} operations failed: {', '.join([op['operation'] for op in failed_operations])}"
            error_info = StandardError(
                message="Some PR update operations failed",
                details=error_details,
                error_type="pr_update_error"
            )
        
        return StandardToolResponse(
            status=status,
            tool_name="update_pull_request",
            data=response_data,
            error=error_info,
            summary=summary,
            metrics=StandardMetrics(
                items_processed=len(operations_performed),
                execution_time_ms=execution_time_ms
            )
        )
        
    except Exception as e:
        execution_time_ms = int((time.time() - start_time) * 1000)
        logger.error(f"Failed to update pull request: {e}")
        
        return StandardToolResponse(
            status="error",
            tool_name="update_pull_request",
            data={"action": "unexpected_error", "pr_id": pr_id},
            error=StandardError(
                message=f"Unexpected error during PR update: {str(e)}",
                details=f"An unexpected error occurred while updating PR #{pr_id}",
                error_type="unexpected_error"
            ),
            summary="PR update failed with unexpected error",
            metrics=StandardMetrics(execution_time_ms=execution_time_ms)
        )

async def _update_pr_metadata(repo_owner: str, repo_name: str, pr_id: int, title: Optional[str], description: Optional[str]) -> Dict:
    """Update PR title and/or description"""
    import httpx
    
    if not settings.GITHUB_TOKEN:
        raise Exception("GitHub token not configured")
    
    headers = {
        "Authorization": f"token {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    update_data = {}
    if title:
        update_data["title"] = title
    if description:
        update_data["body"] = description
    
    async with httpx.AsyncClient() as client:
        url = f"{settings.GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/pulls/{pr_id}"
        response = await client.patch(url, headers=headers, json=update_data)
        
        if response.status_code != 200:
            raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
    
    return {
        "operation": "update_metadata",
        "status": "success",
        "updates": update_data
    }

async def _commit_and_push_changes(repository_path: str, repo_owner: str, repo_name: str, pr_id: int, commit_message: str) -> Dict:
    """Commit changes and push to PR branch"""
    from git import Repo, GitCommandError
    import httpx
    
    logger.info(f"_commit_and_push_changes called with repository_path: {repository_path}")
    
    # Check if repository still exists (in case cleanup ran early)
    if not os.path.exists(repository_path):
        logger.error(f"Repository path no longer exists: {repository_path}")
        return {
            "operation": "commit_and_push",
            "status": "failed",
            "error": f"Repository path no longer exists: {repository_path}"
        }
    
    try:
        # Get PR branch name from GitHub API
        if not settings.GITHUB_TOKEN:
            raise Exception("GitHub token not configured")
        
        headers = {
            "Authorization": f"token {settings.GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient() as client:
            url = f"{settings.GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/pulls/{pr_id}"
            response = await client.get(url, headers=headers)
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch PR info: {response.status_code}")
            
            pr_data = response.json()
            branch_name = pr_data["head"]["ref"]
        
        # Initialize git repo
        local_repo = Repo(repository_path)
        
        # Switch to PR branch
        try:
            local_repo.git.fetch()
            
            # Check if there are uncommitted changes that need to be stashed
            if local_repo.is_dirty() or local_repo.untracked_files:
                logger.info(f"Stashing uncommitted changes before checkout to branch '{branch_name}'")
                local_repo.git.stash('push', '-u', '-m', f'Temporary stash for PR branch checkout')
                stashed_changes = True
            else:
                stashed_changes = False
            
            # Checkout the PR branch
            local_repo.git.checkout(branch_name)
            
            # Pop stashed changes if we stashed them
            if stashed_changes:
                logger.info(f"Applying stashed changes after checkout to branch '{branch_name}'")
                local_repo.git.stash('pop')
                
        except GitCommandError as e:
            raise Exception(f"Failed to checkout PR branch '{branch_name}': {str(e)}")
        
        # Check if there are changes to commit
        logger.info(f"Checking for changes in repository: {repository_path}")
        logger.info(f"Repository is_dirty: {local_repo.is_dirty()}")
        logger.info(f"Untracked files: {local_repo.untracked_files}")
        
        if local_repo.is_dirty():
            logger.info(f"Modified files detected: {[item.a_path for item in local_repo.index.diff(None)]}")
        
        if not local_repo.is_dirty() and not local_repo.untracked_files:
            logger.warning(f"No changes detected in {repository_path} on branch {branch_name}")
            return {
                "operation": "commit_and_push",
                "status": "success",
                "message": "No changes to commit",
                "branch": branch_name,
                "commit_hash": None
            }
        
        # Stage and commit changes
        local_repo.git.add(A=True)
        commit = local_repo.index.commit(commit_message)
        
        # Push to remote
        local_repo.git.push('origin', branch_name)
        
        return {
            "operation": "commit_and_push",
            "status": "success",
            "message": f"Committed and pushed changes to branch '{branch_name}'",
            "branch": branch_name,
            "commit_hash": commit.hexsha[:8],
            "commit_message": commit_message
        }
        
    except Exception as e:
        return {
            "operation": "commit_and_push",
            "status": "failed",
            "error": str(e)
        }

async def _add_pr_comment(repo_owner: str, repo_name: str, pr_id: int, comment: str) -> Dict:
    """Add a comment to the PR"""
    import httpx
    
    if not settings.GITHUB_TOKEN:
        raise Exception("GitHub token not configured")
    
    headers = {
        "Authorization": f"token {settings.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json"
    }
    
    comment_data = {"body": comment}
    
    async with httpx.AsyncClient() as client:
        url = f"{settings.GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/issues/{pr_id}/comments"
        response = await client.post(url, headers=headers, json=comment_data)
        
        if response.status_code != 201:
            raise Exception(f"GitHub API error: {response.status_code} - {response.text}")
        
        comment_response = response.json()
    
    return {
        "operation": "add_comment",
        "status": "success",
        "comment_id": comment_response["id"],
        "comment_url": comment_response["html_url"]
    } 
