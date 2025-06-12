"""
GitHub Service for Pull Request Creation and Repository Management
"""

import os
import tempfile
import subprocess
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timezone
from dataclasses import dataclass
from pathlib import Path
import github
from github import Github
from github.Repository import Repository
from github.PullRequest import PullRequest
from git import Repo, GitCommandError

from config.settings import settings
from utils.go_mod_parser import DependencyUpdate
from utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class PRCreationResult:
    """Result of pull request creation."""
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

@dataclass
class RepositoryAccess:
    """Information about repository access permissions."""
    has_write_access: bool
    can_create_prs: bool
    is_fork_required: bool
    fork_url: Optional[str] = None

class GitHubService:
    """
    Service for GitHub API interactions and repository management.
    
    Handles authentication, repository operations, and pull request creation
    with comprehensive error handling and security considerations.
    """
    
    def __init__(self, config=None):
        # Use global settings directly - no need for wrapper config
        self.temp_dirs_to_cleanup = []
        self.github_client = self._initialize_github_client()
    
    def _initialize_github_client(self) -> Optional[Github]:            
        if settings.GITHUB_TOKEN:
            try:
                client = Github(settings.GITHUB_TOKEN)
                # Test authentication
                user = client.get_user()
                logger.info(f"GitHub authenticated as: {user.login}")
                return client
            except Exception as e:
                logger.error(f"GitHub token authentication failed: {e}")
                return None
        
        logger.warning("No GitHub authentication configured")
        return None
    
    def validate_repository_access(self, repo_url: str) -> RepositoryAccess:
        """
        Validate access permissions for a repository.
        
        Args:
            repo_url: GitHub repository URL
            
        Returns:
            RepositoryAccess with permission information
        """
        if not self.github_client:
            return RepositoryAccess(
                has_write_access=False,
                can_create_prs=False,
                is_fork_required=True
            )
        
        try:
            repo_path = self._extract_repo_path(repo_url)
            repo = self.github_client.get_repo(repo_path)
            
            # Check permissions
            permissions = repo.permissions
            has_write_access = permissions.push or permissions.admin
            can_create_prs = permissions.pull or permissions.push or permissions.admin
            
            # If no write access, check if we can fork
            fork_url = None
            is_fork_required = not has_write_access
            
            if is_fork_required and can_create_prs:
                # Check if we already have a fork
                try:
                    authenticated_user = self.github_client.get_user()
                    fork_name = f"{authenticated_user.login}/{repo.name}"
                    fork_repo = self.github_client.get_repo(fork_name)
                    fork_url = fork_repo.clone_url
                except github.UnknownObjectException:
                    # Fork doesn't exist, we'd need to create one
                    fork_url = f"https://github.com/{authenticated_user.login}/{repo.name}"
            
            return RepositoryAccess(
                has_write_access=has_write_access,
                can_create_prs=can_create_prs,
                is_fork_required=is_fork_required,
                fork_url=fork_url
            )
            
        except github.UnknownObjectException:
            return RepositoryAccess(
                has_write_access=False,
                can_create_prs=False,
                is_fork_required=True
            )
        except Exception as e:
            logger.error(f"Error validating repository access: {e}")
            return RepositoryAccess(
                has_write_access=False,
                can_create_prs=False,
                is_fork_required=True
            )
    
    def create_security_pr(
        self,
        repo_url: str,
        vulnerability_results: Dict[str, Any],
        dependency_updates: Optional[List[DependencyUpdate]] = None
    ) -> PRCreationResult:
        """
        Create a pull request to fix security vulnerabilities.
        
        Args:
            repo_url: GitHub repository URL
            vulnerability_results: Raw vulnerability scan results
            dependency_updates: Optional pre-processed dependency updates (if None, will be generated from vulnerability_results)
            
        Returns:
            PRCreationResult with creation status and details
        """
        # Process vulnerability results if dependency updates not provided
        if dependency_updates is None:
            try:
                from services.dependency_updater import DependencyUpdater
                dependency_updater = DependencyUpdater()
                dependency_updates = dependency_updater.analyze_vulnerabilities_from_scan_results(
                    vulnerability_results
                )
                logger.info(f"Generated {len(dependency_updates)} dependency updates from vulnerability results")
                
                if not dependency_updates:
                    logger.warning("No dependency updates generated from vulnerabilities")
                    return PRCreationResult(
                        success=True,
                        error_message="No vulnerability fixes needed - no dependency updates required"
                    )
                
                # Log the updates we're about to create
                for update in dependency_updates:
                    logger.info(f"  - {update.module_path}: {update.current_version} -> {update.updated_version} (severity: {update.severity})")
                    
            except ImportError as e:
                logger.error(f"DependencyUpdater not available: {e}")
                return PRCreationResult(
                    success=False,
                    error_message=f"Dependency analysis not available: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Error processing vulnerability results: {e}")
                return PRCreationResult(
                    success=False,
                    error_message=f"Failed to process vulnerabilities: {str(e)}"
                )
        
        if settings.GITHUB_DRY_RUN:
            logger.info("Dry run mode - would create PR with updates:")
            for update in dependency_updates:
                logger.info(f"  {update.module_path}: {update.current_version} -> {update.updated_version}")
            return PRCreationResult(
                success=True,
                pr_url="DRY_RUN_MODE",
                branch_name="dry-run-branch",
                files_changed=["go.mod", "go.sum"],
                vulnerabilities_fixed=len(dependency_updates)
            )
        
        try:
            # Validate repository access
            access = self.validate_repository_access(repo_url)
            if not access.can_create_prs:
                return PRCreationResult(
                    success=False,
                    error_message="No permission to create pull requests for this repository"
                )
            
            # Clone repository to temporary location
            temp_dir = self._clone_repository_for_pr(repo_url, access)
            if not temp_dir:
                return PRCreationResult(
                    success=False,
                    error_message="Failed to clone repository"
                )
            
            # Apply dependency updates
            files_changed = self._apply_dependency_updates(temp_dir, dependency_updates)
            if not files_changed:
                return PRCreationResult(
                    success=False,
                    error_message="No files were updated"
                )
            
            # Create branch and commit changes
            branch_name = self._create_and_commit_changes(
                temp_dir, dependency_updates, files_changed
            )
            if not branch_name:
                return PRCreationResult(
                    success=False,
                    error_message="Failed to create branch and commit changes"
                )
            
            # Push branch to GitHub
            push_success = self._push_branch(temp_dir, branch_name, access)
            if not push_success:
                return PRCreationResult(
                    success=False,
                    error_message="Failed to push branch to GitHub"
                )
            
            # Create pull request
            pr_result = self._create_pull_request(
                repo_url, branch_name, dependency_updates, vulnerability_results, 
                access
            )
            
            return PRCreationResult(
                success=True,
                pr_url=pr_result.get('pr_url'),
                pr_number=pr_result.get('pr_number'),
                branch_name=branch_name,
                files_changed=files_changed,
                vulnerabilities_fixed=len(dependency_updates)
            )
            
        except Exception as e:
            logger.error(f"Error creating security PR: {e}")
            return PRCreationResult(
                success=False,
                error_message=str(e)
            )
        finally:
            self._cleanup_temp_directories()
    
    def _extract_repo_path(self, repo_url: str) -> str:
        """Extract owner/repo from GitHub URL."""
        # Handle various GitHub URL formats
        if repo_url.startswith('https://github.com/'):
            path = repo_url.replace('https://github.com/', '').rstrip('/')
            if path.endswith('.git'):
                path = path[:-4]
            return path
        else:
            raise ValueError(f"Invalid GitHub URL format: {repo_url}")
    
    def _clone_repository_for_pr(self, repo_url: str, access: RepositoryAccess) -> Optional[str]:
        """Clone repository to temporary directory for PR creation."""
        temp_dir = tempfile.mkdtemp(prefix="whisper_pr_")
        self.temp_dirs_to_cleanup.append(temp_dir)
        
        try:
            # Determine which URL to clone from
            clone_url = repo_url
            if access.is_fork_required and access.fork_url:
                # TODO: Handle fork creation if needed
                clone_url = access.fork_url
            
            # Clone repository
            repo = Repo.clone_from(clone_url, temp_dir)
            logger.info(f"Repository cloned to: {temp_dir}")
            return temp_dir
            
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            return None
    
    def _apply_dependency_updates(
        self, 
        repo_path: str, 
        dependency_updates: List[DependencyUpdate]
    ) -> List[str]:
        """Apply dependency updates to go.mod files."""
        from utils.go_mod_parser import GoModParser
        
        parser = GoModParser()
        files_changed = []
        
        # Find all go.mod files
        go_mod_files = parser.find_go_mod_files(repo_path)
        
        for go_mod_path in go_mod_files:
            try:
                # Parse current go.mod
                go_mod_file = parser.parse_go_mod(go_mod_path)
                
                # Filter updates relevant to this go.mod
                relevant_updates = []
                for update in dependency_updates:
                    if go_mod_file.get_dependency(update.module_path):
                        relevant_updates.append(update)
                
                if not relevant_updates:
                    continue
                
                # Apply updates
                updated_content = parser.update_dependencies(go_mod_file, relevant_updates)
                
                # Validate syntax
                is_valid, error_msg = parser.validate_go_mod_syntax(updated_content, repo_path)
                if not is_valid:
                    logger.warning(f"Invalid go.mod syntax after update: {error_msg}")
                    continue
                
                # Write updated content
                with open(go_mod_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                
                files_changed.append(os.path.relpath(go_mod_path, repo_path))
                logger.info(f"Updated {go_mod_path} with {len(relevant_updates)} dependency fixes")
                
            except Exception as e:
                logger.error(f"Error updating {go_mod_path}: {e}")
                continue
        
        # Run go mod tidy to update go.sum
        if files_changed:
            try:
                result = subprocess.run(
                    ['go', 'mod', 'tidy'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    # Check if go.sum was modified
                    go_sum_files = [f for f in os.listdir(repo_path) if f == 'go.sum']
                    for go_sum_file in go_sum_files:
                        if go_sum_file not in files_changed:
                            files_changed.append(go_sum_file)
                else:
                    logger.warning(f"go mod tidy failed: {result.stderr}")
                    
            except Exception as e:
                logger.warning(f"Failed to run go mod tidy: {e}")
        
        return files_changed
    
    def _create_and_commit_changes(
        self,
        repo_path: str,
        dependency_updates: List[DependencyUpdate],
        files_changed: List[str]
    ) -> Optional[str]:
        """Create branch and commit dependency updates."""
        try:
            repo = Repo(repo_path)
            
            # Create new branch
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            branch_name = f"security/fix-dependencies-{timestamp}"
            
            # Create and checkout new branch
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            
            # Stage changed files
            for file_path in files_changed:
                repo.index.add([file_path])
            
            # Create commit message
            commit_message = self._generate_commit_message(dependency_updates, files_changed)
            
            # Commit changes
            repo.index.commit(commit_message)
            
            logger.info(f"Created branch '{branch_name}' and committed changes")
            return branch_name
            
        except Exception as e:
            logger.error(f"Error creating branch and committing: {e}")
            return None
    
    def _push_branch(self, repo_path: str, branch_name: str, access: RepositoryAccess) -> bool:
        """Push branch to GitHub."""
        try:
            repo = Repo(repo_path)
            
            # Push to origin
            origin = repo.remote('origin')
            origin.push(branch_name)
            
            logger.info(f"Pushed branch '{branch_name}' to GitHub")
            return True
            
        except Exception as e:
            logger.error(f"Error pushing branch: {e}")
            return False
    
    def _create_pull_request(
        self,
        repo_url: str,
        branch_name: str,
        dependency_updates: List[DependencyUpdate],
        vulnerability_results: Dict[str, Any],
        access: RepositoryAccess
    ) -> Dict[str, Any]:
        """Create the actual pull request on GitHub."""
        repo_path = self._extract_repo_path(repo_url)
        repo = self.github_client.get_repo(repo_path)
        
        # Generate PR title and description
        title = self._generate_pr_title(dependency_updates)
        description = self._generate_pr_description(
            dependency_updates, vulnerability_results, branch_name
        )
        
        # Set PR options - hardcoded sensible defaults
        base_branch = "main"
        draft = False
        
        # Create pull request
        pr = repo.create_pull(
            title=title,
            body=description,
            head=branch_name,
            base=base_branch,
            draft=draft
        )
        
        # Add labels - hardcoded sensible defaults
        labels = ["security", "dependencies"]
        pr.add_to_labels(*labels)
        
        # Reviewers are configured in GitHub repository settings, not here
        
        logger.info(f"Created pull request #{pr.number}: {pr.html_url}")
        
        return {
            'pr_url': pr.html_url,
            'pr_number': pr.number,
            'pr_id': pr.id
        }
    
    def _generate_commit_message(
        self, 
        dependency_updates: List[DependencyUpdate],
        files_changed: List[str]
    ) -> str:
        """Generate commit message for dependency updates."""
        vuln_count = len(dependency_updates)
        
        if vuln_count == 1:
            update = dependency_updates[0]
            message = f"security: update {update.module_path} to {update.updated_version}"
        else:
            message = f"security: fix {vuln_count} vulnerabilities in Go dependencies"
        
        # Add details about changes
        details = []
        for update in dependency_updates:
            details.append(f"- {update.module_path}: {update.current_version} -> {update.updated_version}")
        
        if details:
            message += "\n\n" + "\n".join(details)
        
        # Add files changed
        if files_changed:
            message += f"\n\nFiles modified: {', '.join(files_changed)}"
        
        return message
    
    def _generate_pr_title(self, dependency_updates: List[DependencyUpdate]) -> str:
        """Generate pull request title."""
        vuln_count = len(dependency_updates)
        
        return f"Security: Fix {vuln_count} vulnerabilities in Go dependencies"
    
    def _generate_pr_description(
        self,
        dependency_updates: List[DependencyUpdate],
        vulnerability_results: Dict[str, Any],
        branch_name: str
    ) -> str:
        """Generate detailed pull request description."""
        description_parts = []
        
        # Summary
        vuln_count = len(dependency_updates)
        description_parts.append(f"## Security Update")
        description_parts.append(f"This PR fixes **{vuln_count}** security vulnerabilities in Go dependencies.")
        description_parts.append("")
        
        # Vulnerability details
        if dependency_updates:
            description_parts.append("## Vulnerabilities Fixed")
            description_parts.append("")
            
            for i, update in enumerate(dependency_updates, 1):
                description_parts.append(f"### {i}. {update.module_path}")
                description_parts.append(f"- **Current Version**: `{update.current_version}`")
                description_parts.append(f"- **Updated Version**: `{update.updated_version}`")
                description_parts.append(f"- **Severity**: {update.severity.title()}")
                
                if update.vulnerability_ids:
                    description_parts.append(f"- **CVE IDs**: {', '.join(update.vulnerability_ids)}")
                
                description_parts.append(f"- **Reasoning**: {update.reasoning}")
                description_parts.append("")
        
        # Changes made
        description_parts.append("## Changes Made")
        description_parts.append("- Updated vulnerable dependencies in `go.mod`")
        description_parts.append("- Ran `go mod tidy` to update `go.sum`")
        description_parts.append("- Verified go.mod syntax")
        description_parts.append("")
        
        # Testing recommendation
        description_parts.append("## Testing Recommendations")
        description_parts.append("- [ ] Run existing test suite")
        description_parts.append("- [ ] Verify application builds successfully")
        description_parts.append("- [ ] Test critical functionality")
        description_parts.append("- [ ] Run security scan to confirm fixes")
        description_parts.append("")
        
        # Metadata
        description_parts.append("---")
        description_parts.append(f"*This PR was automatically generated by Whisper Analysis Agent*")
        description_parts.append(f"*Branch: `{branch_name}`*")
        
        return "\n".join(description_parts)
    
    def _cleanup_temp_directories(self):
        """Clean up temporary directories created during PR process."""
        for temp_dir in self.temp_dirs_to_cleanup:
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(f"Failed to cleanup {temp_dir}: {e}")
        
        self.temp_dirs_to_cleanup.clear()


# Global service instance
github_service = GitHubService() 
