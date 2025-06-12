"""
Minimized GitHub Service for Pull Request Creation
"""

import os
import subprocess
import tempfile
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass

from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
from git import Repo

from config.settings import settings
from utils.go_mod_parser import DependencyUpdate, GoModParser
from utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class PRCreationResult:
    """Simplified result of pull request creation."""
    success: bool
    pr_url: Optional[str] = None
    pr_number: Optional[int] = None
    branch_name: Optional[str] = None
    files_changed: List[str] = None
    vulnerabilities_fixed: int = 0
    error_message: Optional[str] = None
    
    def __post_init__(self):
        if self.files_changed is None:
            self.files_changed = []


class GitHubService2:
    """
    Minimized GitHub Service - focuses on core PR creation functionality.
    
    Simplified approach:
    - Assumes you have proper access to repos
    - Uses context managers for cleanup
    - Minimal error handling - let exceptions bubble up
    - No complex permission checking or fork handling
    """
    
    def __init__(self):
        self.github_client = self._get_github_client()
    
    def _get_github_client(self) -> Github:
        """Get authenticated GitHub client or raise exception."""
        if not settings.GITHUB_TOKEN:
            raise ValueError("GITHUB_TOKEN not configured")
        
        try:
            client = Github(settings.GITHUB_TOKEN)
            # Test authentication
            user = client.get_user()
            logger.info(f"GitHub authenticated as: {user.login}")
            return client
        except Exception as e:
            raise ValueError(f"GitHub authentication failed: {e}")
    
    def create_security_pr(
        self,
        repo_url: str,
        vulnerability_results: Dict[str, Any],
        dependency_updates: Optional[List[DependencyUpdate]] = None
    ) -> PRCreationResult:
        """
        Create a security PR - simplified version.
        
        Args:
            repo_url: GitHub repository URL  
            vulnerability_results: Vulnerability scan results
            dependency_updates: Optional pre-processed updates
            
        Returns:
            PRCreationResult with status and details
        """
        try:
            # Generate dependency updates if not provided
            if dependency_updates is None:
                dependency_updates = self._process_vulnerabilities(vulnerability_results)
            
            if not dependency_updates:
                return PRCreationResult(
                    success=True,
                    error_message="No vulnerability fixes needed"
                )
            
            # Extract repo info
            repo_path = self._extract_repo_path(repo_url)
            repo = self.github_client.get_repo(repo_path)
            
            # Create PR using temporary directory
            with tempfile.TemporaryDirectory(prefix="github_pr_") as temp_dir:
                logger.info(f"Cloning repository to {temp_dir}")
                
                # Clone repository
                git_repo = Repo.clone_from(repo_url, temp_dir)
                
                # Apply dependency updates
                files_changed = self._apply_updates(temp_dir, dependency_updates)
                
                if not files_changed:
                    return PRCreationResult(
                        success=False,
                        error_message="No files were updated"
                    )
                
                # Create branch and commit
                branch_name = self._create_branch_and_commit(
                    git_repo, dependency_updates, files_changed
                )
                
                # Push branch
                origin = git_repo.remote('origin')
                origin.push(branch_name)
                
                # Create PR
                pr = self._create_pull_request(
                    repo, branch_name, dependency_updates, vulnerability_results
                )
                
                logger.info(f"Created PR #{pr.number}: {pr.html_url}")
                
                return PRCreationResult(
                    success=True,
                    pr_url=pr.html_url,
                    pr_number=pr.number,
                    branch_name=branch_name,
                    files_changed=files_changed,
                    vulnerabilities_fixed=len(dependency_updates)
                )
                
        except Exception as e:
            logger.error(f"Failed to create security PR: {e}")
            return PRCreationResult(
                success=False,
                error_message=str(e)
            )
    
    def _process_vulnerabilities(self, vulnerability_results: Dict[str, Any]) -> List[DependencyUpdate]:
        """Process vulnerability results into dependency updates."""
        from services.dependency_updater import DependencyUpdater
        
        updater = DependencyUpdater()
        updates = updater.analyze_vulnerabilities_from_scan_results(vulnerability_results)
        
        logger.info(f"Generated {len(updates)} dependency updates")
        return updates
    
    def _extract_repo_path(self, repo_url: str) -> str:
        """Extract owner/repo from GitHub URL."""
        if repo_url.startswith('https://github.com/'):
            path = repo_url.replace('https://github.com/', '').rstrip('/')
            if path.endswith('.git'):
                path = path[:-4]
            return path
        raise ValueError(f"Invalid GitHub URL: {repo_url}")
    
    def _apply_updates(self, repo_path: str, updates: List[DependencyUpdate]) -> List[str]:
        """Apply dependency updates to go.mod files."""
        parser = GoModParser()
        files_changed = []
        
        # Find and update go.mod files
        go_mod_files = parser.find_go_mod_files(repo_path)
        
        for go_mod_path in go_mod_files:
            try:
                # Parse and update go.mod
                go_mod_file = parser.parse_go_mod(go_mod_path)
                
                # Filter relevant updates
                relevant_updates = [
                    update for update in updates 
                    if go_mod_file.get_dependency(update.module_path)
                ]
                
                if relevant_updates:
                    # Apply updates
                    updated_content = parser.update_dependencies(go_mod_file, relevant_updates)
                    
                    # Write updated content
                    with open(go_mod_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    files_changed.append(os.path.relpath(go_mod_path, repo_path))
                    logger.info(f"Updated {go_mod_path}")
                    
            except Exception as e:
                logger.warning(f"Failed to update {go_mod_path}: {e}")
        
        # Run go mod tidy
        if files_changed:
            try:
                subprocess.run(
                    ['go', 'mod', 'tidy'],
                    cwd=repo_path,
                    check=True,
                    capture_output=True,
                    timeout=60
                )
                # Add go.sum if it was modified
                go_sum_path = os.path.join(repo_path, 'go.sum')
                if os.path.exists(go_sum_path):
                    files_changed.append('go.sum')
            except Exception as e:
                logger.warning(f"go mod tidy failed: {e}")
        
        return files_changed
    
    def _create_branch_and_commit(
        self, 
        repo: Repo, 
        updates: List[DependencyUpdate], 
        files_changed: List[str]
    ) -> str:
        """Create branch and commit changes."""
        # Create branch
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
        branch_name = f"security/fix-dependencies-{timestamp}"
        
        new_branch = repo.create_head(branch_name)
        new_branch.checkout()
        
        # Stage and commit
        repo.index.add(files_changed)
        
        # Simple commit message
        commit_msg = f"security: fix {len(updates)} vulnerabilities in dependencies"
        repo.index.commit(commit_msg)
        
        return branch_name
    
    def _create_pull_request(
        self,
        repo,
        branch_name: str,
        updates: List[DependencyUpdate],
        vulnerability_results: Dict[str, Any]
    ):
        """Create the GitHub pull request."""
        # Simple title and description
        title = f"Security: Fix {len(updates)} vulnerabilities"
        
        description = f"""## Security Update

This PR fixes **{len(updates)}** security vulnerabilities in Go dependencies.

### Changes:
"""
        for update in updates:
            description += f"- `{update.module_path}`: {update.current_version} → {update.updated_version}\n"
        
        description += "\n### Files Modified:\n- go.mod\n- go.sum\n"
        description += "\n*Automatically generated by Whisper Security Scanner*"
        
        # Create PR
        pr = repo.create_pull(
            title=title,
            body=description,
            head=branch_name,
            base="main"  # Assume main branch
        )
        
        # Add security label
        try:
            pr.add_to_labels("security")
        except:
            pass  # Label might not exist
        
        return pr


# Global instance
github_service_2 = GitHubService2() 
