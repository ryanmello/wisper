import os
import re
from typing import Dict, Any, Optional
from github import Github
from git import Repo, GitCommandError
from config.settings import settings
from utils.logging_config import get_logger

logger = get_logger(__name__)

class GitHubService:    
    def __init__(self):
        self.github_client: Optional[Github] = None
        self._authenticated = False
        self._auth_attempted = False
        
    @property
    def client(self) -> Optional[Github]:
        """Lazy initialization of GitHub client with authentication."""
        if not self._authenticated and not self._auth_attempted:
            self._auth_attempted = True
            if settings.GITHUB_TOKEN:
                try:
                    self.github_client = Github(settings.GITHUB_TOKEN)
                    # Test authentication by getting user info
                    self.github_client.get_user()
                    self._authenticated = True
                    logger.info(f"GitHub authenticated as: {self.github_client.get_user().login}")
                except Exception as e:
                    logger.warning(f"GitHub authentication failed: {e}")
                    logger.info("GitHub features will be unavailable - continuing without authentication")
            else:
                logger.warning("GitHub token not provided - GitHub features will be unavailable")
        return self.github_client if self._authenticated else None
    
    def is_available(self) -> bool:
        """Check if GitHub features are available."""
        return self.client is not None
    
    def create_pull_request(
        self, 
        repo_url: str, 
        branch_name: str, 
        title: str, 
        description: str, 
        clone_path: str,
        commit_message: str
    ) -> Dict[str, Any]:
        """
        Create a pull request for already-modified files in a repository.
        
        Assumes files have already been modified by other tools (e.g., apply_fixes_tool).
        Handles git operations only: commit changes → push branch → create PR.
        
        Args:
            repo_url: GitHub repository URL (e.g., https://github.com/owner/repo)
            branch_name: Name of the branch to create and push changes to
            title: PR title
            description: PR description
            clone_path: Path to cloned repository directory with modified files
            commit_message: Descriptive commit message for the changes
            
        Returns:
            Dictionary with PR creation results including PR URL and metadata
        """
        try:
            if not self.is_available():
                return {
                    "status": "error",
                    "action": "failed",
                    "error": "GitHub authentication required but not available. Please configure a valid GITHUB_TOKEN."
                }
                
            if settings.GITHUB_DRY_RUN:
                logger.info("Running in GitHub dry run mode")
                return {
                    "status": "simulated",
                    "action": "dry_run", 
                    "message": "GitHub dry run mode - PR creation simulated",
                    "simulated_pr": {
                        "title": title,
                        "branch": branch_name,
                        "commit_message": commit_message
                    }
                }
            
            if not clone_path or not os.path.exists(clone_path):
                return {
                    "status": "error",
                    "action": "failed",
                    "error": "Invalid clone path"
                }
             
            local_repo = Repo(clone_path)
            logger.info(f"Initialized local git repository at {clone_path}")
            
            repo_path = self.extract_github_repo_path(repo_url)
            if not repo_path:
                return {
                    "status": "error",
                    "action": "failed",
                    "error": "Invalid GitHub repository URL format"
                }
            
            github_repo = self.client.get_repo(repo_path)
            base_branch = github_repo.default_branch
            logger.info(f"Using base branch: {base_branch}")
            
            try:
                local_repo.remotes.origin.fetch()
                existing_branches = [ref.name.split('/')[-1] for ref in local_repo.refs]
                
                if branch_name in existing_branches:
                    try:
                        local_repo.git.checkout(branch_name)
                        logger.info(f"Switched to existing branch: {branch_name}")
                    except GitCommandError as e:
                        return {
                            "status": "error",
                            "action": "failed",
                            "error": f"Failed to checkout existing branch '{branch_name}': {str(e)}"
                        }
                else:
                    try:
                        local_repo.git.checkout(f"origin/{base_branch}")
                        local_repo.git.checkout('-b', branch_name)
                        logger.info(f"Created new branch '{branch_name}' from '{base_branch}'")
                    except GitCommandError as e:
                        return {
                            "status": "error",
                            "action": "failed", 
                            "error": f"Failed to create branch '{branch_name}': {str(e)}"
                        }
                        
            except Exception as e:
                return {
                    "status": "error",
                    "action": "failed",
                    "error": f"Failed to manage git branches: {str(e)}"
                }
            
            try:
                local_repo.git.add(A=True)
                
                if local_repo.is_dirty() or local_repo.untracked_files:
                    local_repo.index.commit(commit_message)
                    logger.info(f"Committed changes with message: {commit_message}")
                else:
                    return {
                        "status": "error",
                        "action": "failed", 
                        "error": "No changes detected to commit"
                    }
                    
            except Exception as e:
                return {
                    "status": "error",
                    "action": "failed",
                    "error": f"Failed to commit changes: {str(e)}"
                }
            
            try:
                local_repo.git.push('--set-upstream', 'origin', branch_name)
                logger.info(f"Pushed branch '{branch_name}' to remote")
                
            except GitCommandError as e:
                return {
                    "status": "error",
                    "action": "failed",
                    "error": f"Failed to push branch to remote: {str(e)}"
                }
            except Exception as e:
                return {
                    "status": "error",
                    "action": "failed", 
                    "error": f"Unexpected error during push: {str(e)}"
                }
            
            pull_request = github_repo.create_pull(
                title=title,
                body=description,
                head=branch_name,
                base=base_branch,
                draft=False
            )

            pull_request.add_to_labels("ai-generated")
            
            logger.info(f"Created pull request #{pull_request.number}: {pull_request.html_url}")
            
            return {
                "status": "success",
                "action": "created",
                "pr_url": pull_request.html_url,
                "pr_number": pull_request.number,
                "branch": branch_name,
                "base_branch": base_branch,
                "message": f"Pull request created successfully: {title}"
            }
            
        except Exception as e:
            logger.error(f"Failed to create pull request: {e}")
            return {
                "status": "error",
                "action": "failed",
                "error": str(e)
            }
        
    def extract_github_repo_path(self, repo_url: str) -> Optional[str]:
        """Extract owner/repo path from various GitHub URL formats.
        
        Args:
            repo_url: GitHub repository URL in various formats
            
        Returns:
            String in format "owner/repo" or None if invalid
        """
        if not repo_url or not isinstance(repo_url, str):
            return None
        
        patterns = [
            r'https?://github\.com/([^/]+/[^/]+?)(?:\.git)?/?$', # HTTPS formats
            r'git@github\.com:([^/]+/[^/]+?)(?:\.git)?/?$', # SSH format
            r'(?:www\.)?github\.com/([^/]+/[^/]+?)(?:\.git)?/?$', # Plain github.com (without protocol)
        ]
        
        for pattern in patterns:
            match = re.search(pattern, repo_url.strip())
            if match:
                repo_path = match.group(1)
                # Ensure we have owner/repo format
                if '/' in repo_path and len(repo_path.split('/')) == 2:
                    return repo_path
        
        return None

github_service = GitHubService() 
