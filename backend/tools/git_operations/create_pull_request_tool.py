"""
Create Pull Request Tool - Create GitHub pull requests with specified changes
"""

import os
from typing import Dict, Any
from langchain_core.tools import tool

from utils.logging_config import get_logger

logger = get_logger(__name__)

@tool
def create_pull_request(repository_path: str, branch_name: str, title: str, description: str, changes_summary: Dict[str, Any]) -> Dict[str, Any]:
    """Create a pull request with specified changes after applying fixes to the repository.
    
    This tool creates a new branch, commits changes, and opens a pull request on the original repository. 
    It's typically used after the apply_fixes tool has made modifications to the codebase, allowing you to 
    submit the improvements back to the original repository for review and integration.
    
    Prerequisites: Repository must be cloned; changes should have been applied (often via apply_fixes tool)
    Common workflow: analyze_issues → apply_fixes → create_pull_request
    
    Args:
        repository_path: Path to the cloned repository with applied changes
        branch_name: Name for the new branch containing the changes
        title: Title for the pull request
        description: Detailed description of the changes and their purpose
        changes_summary: Summary of changes that were applied
        
    Returns:
        Dictionary with pull request URL, status, and details of the created PR
    """
    logger.info(f"Creating pull request for {repository_path}")
    
    try:
        from services.github_service import github_service
        from config.settings import settings
        
        # Check if GitHub service is available
        if not github_service.is_available():
            logger.warning("GitHub service not available - running in dry run mode")
            return {
                "status": "simulated",
                "action": "dry_run",
                "message": "GitHub service not available - PR creation simulated",
                "simulated_pr": {
                    "title": title,
                    "branch": branch_name,
                    "changes_summary": changes_summary
                }
            }
        
        # Check if running in dry run mode
        if settings.GITHUB_DRY_RUN:
            logger.info("Running in GitHub dry run mode")
            return {
                "status": "simulated",
                "action": "dry_run",
                "message": "GitHub dry run mode - PR creation simulated",
                "simulated_pr": {
                    "title": title,
                    "branch": branch_name,
                    "changes_summary": changes_summary
                }
            }
        
        # Extract owner and repo from URL
        repo_path = _extract_repo_path(repository_path)
        if not repo_path:
            return {
                "status": "error",
                "error": "Invalid repository path format"
            }
        
        owner, repo = repo_path.split('/')
        
        # Create pull request using GitHub service
        pr_result = github_service.create_pull_request(
            owner=owner,
            repo=repo,
            branch_name=branch_name,
            title=title,
            description=description,
            changes_summary=changes_summary
        )
        
        if pr_result.get("success"):
            logger.info(f"Successfully created pull request: {pr_result.get('pr_url')}")
            return {
                "status": "success",
                "action": "created",
                "pr_url": pr_result.get("pr_url"),
                "pr_number": pr_result.get("pr_number"),
                "branch": branch_name,
                "changes_summary": changes_summary,
                "message": f"Pull request created successfully: {title}"
            }
        else:
            logger.error(f"Failed to create pull request: {pr_result.get('error')}")
            return {
                "status": "error",
                "error": pr_result.get("error", "Unknown error"),
                "action": "failed"
            }
        
    except Exception as e:
        logger.error(f"Failed to create pull request: {e}")
        return {
            "status": "error",
            "error": str(e),
            "action": "failed"
        }

def _extract_repo_path(repository_path: str) -> str:
    """Extract owner/repo from GitHub URL."""
    import re
    
    # Handle various GitHub URL formats
    patterns = [
        r'github\.com/([^/]+/[^/]+?)(?:\.git)?/?$',
        r'github\.com:([^/]+/[^/]+?)(?:\.git)?/?$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, repository_path)
        if match:
            return match.group(1)
    
    return None 