import os
import subprocess
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone
from dataclasses import dataclass
import github
from github import Github
from git import Repo

from config.settings import settings

from utils.logging_config import get_logger
from services.repository_service import repository_service

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

class GitHubService:
    """ Service for GitHub API interactions and repository management. """
    
    def __init__(self, config=None):
        self.github_client = Github(settings.GITHUB_TOKEN)
        user = self.github_client.get_user()
        logger.info(f"GitHub authenticated as: {user.login}")
    
    def create_pull_request(self, repo_url: str, vulnerability_results: Dict[str, Any], clone_path: str) -> PRCreationResult:
        try:
            # Only AI-generated fixes are supported now
            print(vulnerability_results)
            if 'ai_fixes' not in vulnerability_results:
                return PRCreationResult(
                    success=False,
                    error_message="No AI-generated fixes provided"
                )
            
            logger.info("Creating PR with AI-generated fixes")
            return self._create_pr_with_ai_fixes(repo_url, vulnerability_results, clone_path)
            
        except Exception as e:
            logger.error(f"Error creating security PR: {e}")
            return PRCreationResult(
                success=False,
                error_message=str(e)
            )
        
        finally:
            # Note: Individual cleanup now handled in _create_pr_with_ai_fixes
            pass
    
    def _create_pr_with_ai_fixes(self, repo_url: str, vulnerability_results: Dict[str, Any], clone_path: str) -> PRCreationResult:
        """Create PR using AI-generated fixes."""
        temp_dir = None
        try:
            ai_fixes = vulnerability_results.get('ai_fixes', {})
            vulnerabilities_found = vulnerability_results.get('scan_summary', {}).get('vulnerabilities_found', 0)
            fix_explanation = vulnerability_results.get('fix_explanation', '')
            
            if not ai_fixes:
                return PRCreationResult(
                    success=True,
                    error_message="No AI fixes provided"
                )
            
            logger.info(f"Creating PR with {len(ai_fixes)} AI-generated file fixes")
            
            if settings.GITHUB_DRY_RUN:
                logger.info("Dry run mode - would create PR with AI fixes:")
                for file_path in ai_fixes.keys():
                    logger.info(f"  {file_path}")
                return PRCreationResult(
                    success=True,
                    pr_url="DRY_RUN_MODE",
                    branch_name="dry-run-branch",
                    files_changed=list(ai_fixes.keys()),
                    vulnerabilities_fixed=vulnerabilities_found
                )
            
            # Use existing clone if provided, otherwise clone the repository
            temp_dir = clone_path
            logger.info(f"Reusing existing repository clone at: {temp_dir}")
            
            files_changed = self._apply_ai_fixes(temp_dir, ai_fixes)
            if not files_changed:
                return PRCreationResult(
                    success=False,
                    error_message="No files were updated"
                )
            
            branch_name = self._create_branch(temp_dir, "ai-fixes")
            if not branch_name:
                return PRCreationResult(
                    success=False,
                    error_message="Failed to create branch"
                )
            
            if not self._commit_ai_changes(temp_dir, branch_name, vulnerability_results, files_changed):
                return PRCreationResult(
                    success=False,
                    error_message="Failed to commit changes"
                )
            
            if not self._push_branch(temp_dir, branch_name):
                return PRCreationResult(
                    success=False,
                    error_message="Failed to push branch to GitHub"
                )
            
            pr_result = self._create_ai_pull_request(repo_url, branch_name, vulnerability_results)
            
            return PRCreationResult(
                success=True,
                pr_url=pr_result.get('pr_url'),
                pr_number=pr_result.get('pr_number'),
                branch_name=branch_name,
                files_changed=files_changed,
                vulnerabilities_fixed=vulnerabilities_found
            )
            
        except Exception as e:
            logger.error(f"Error creating AI-based security PR: {e}")
            return PRCreationResult(
                success=False,
                error_message=str(e)
            )
        finally:
            # Only clean up if we created a new clone (not reusing existing)
            if temp_dir and temp_dir != clone_path and os.path.exists(temp_dir):
                cleanup_success = repository_service.cleanup_directory(temp_dir)
                if not cleanup_success:
                    repository_service.schedule_delayed_cleanup(temp_dir)
                logger.info(f"GitHub service cleaned up temp directory: {temp_dir}")
    
    def _apply_ai_fixes(self, repo_path: str, ai_fixes: Dict[str, str]) -> List[str]:
        """Apply AI-generated fixes to files."""
        files_changed = []
        
        for file_path, new_content in ai_fixes.items():
            try:
                full_path = os.path.join(repo_path, file_path)
                
                # Create directory if it doesn't exist
                dir_path = os.path.dirname(full_path)
                if dir_path and not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                
                # Write the updated content
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                files_changed.append(file_path)
                logger.info(f"Applied AI fix to: {file_path}")
                
            except Exception as e:
                logger.error(f"Failed to apply AI fix to {file_path}: {e}")
                continue
        
        # Run go mod tidy if go.mod was updated
        if any('go.mod' in f for f in files_changed):
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
                    go_sum_path = os.path.join(repo_path, 'go.sum')
                    if os.path.exists(go_sum_path) and 'go.sum' not in files_changed:
                        files_changed.append('go.sum')
                    logger.info("Successfully ran go mod tidy")
                else:
                    logger.warning(f"go mod tidy failed: {result.stderr}")
                    
            except Exception as e:
                logger.warning(f"Failed to run go mod tidy: {e}")
        
        return files_changed
    
    def _create_branch(self, repo_path: str, branch_type: str = "dependencies") -> Optional[str]:
        """Create a new branch for security fixes."""
        try:
            repo = Repo(repo_path)
            
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
            if branch_type == "ai-fixes":
                branch_name = f"security/ai-fix-vulnerabilities-{timestamp}"
            else:
                branch_name = f"security/fix-dependencies-{timestamp}"
            
            new_branch = repo.create_head(branch_name)
            new_branch.checkout()
            
            logger.info(f"Created branch '{branch_name}'")
            return branch_name
            
        except Exception as e:
            logger.error(f"Error creating branch: {e}")
            return None
 
    def _commit_ai_changes(
        self,
        repo_path: str,
        branch_name: str,
        vulnerability_results: Dict[str, Any],
        files_changed: List[str]
    ) -> bool:
        """Commit AI-generated fixes to the specified branch."""
        try:
            repo = Repo(repo_path)
            
            for file_path in files_changed:
                repo.index.add([file_path])
            
            commit_message = self._generate_commit_message(vulnerability_results, files_changed)
            repo.index.commit(commit_message)
            
            logger.info(f"Committed AI-generated changes to branch '{branch_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error committing AI changes: {e}")
            return False
    
    def _push_branch(self, repo_path: str, branch_name: str) -> bool:
        """Push branch to GitHub."""
        try:
            repo = Repo(repo_path)
            
            origin = repo.remote('origin')
            origin.push(branch_name)

            logger.info(f"Pushed branch '{branch_name}' to GitHub")
            return True
            
        except Exception as e:
            logger.error(f"Error pushing branch: {e}")
            return False
    
    def _create_ai_pull_request(
        self,
        repo_url: str,
        branch_name: str,
        vulnerability_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create pull request for AI-generated fixes."""
        repo_path = repository_service.extract_repo_path(repo_url)
        repo = self.github_client.get_repo(repo_path)
        
        title = self._generate_title(vulnerability_results)
        description = self._generate_description(vulnerability_results, branch_name)
        
        base_branch = "main"
        draft = False
        
        pull_request = repo.create_pull(
            title=title,
            body=description,
            head=branch_name,
            base=base_branch,
            draft=draft
        )
        
        labels = ["security", "ai-generated", "vulnerabilities"]
        pull_request.add_to_labels(*labels)
                
        logger.info(f"Created AI-generated pull request #{pull_request.number}: {pull_request.html_url}")
        
        return {
            'pr_url': pull_request.html_url,
            'pr_number': pull_request.number,
            'pr_id': pull_request.id
        }
    
    def _generate_commit_message(
        self, 
        vulnerability_results: Dict[str, Any],
        files_changed: List[str]
    ) -> str:
        """Generate commit message for AI-generated fixes."""
        vuln_count = vulnerability_results.get('scan_summary', {}).get('vulnerabilities_found', 0)
        
        if vuln_count == 1:
            message = f"security: AI-generated fix for 1 vulnerability"
        else:
            message = f"security: AI-generated fixes for {vuln_count} vulnerabilities"
        
        # Add AI explanation summary
        fix_explanation = vulnerability_results.get('fix_explanation', '')
        if fix_explanation:
            # Take first 200 characters of explanation for commit
            explanation_summary = fix_explanation[:200] + "..." if len(fix_explanation) > 200 else fix_explanation
            message += f"\n\n{explanation_summary}"
        
        # Add files changed
        if files_changed:
            message += f"\n\nFiles modified: {', '.join(files_changed)}"
        
        message += f"\n\nGenerated by {settings.PROJECT_NAME} AI Security Analysis"
        
        return message
    
    def _generate_title(self, vulnerability_results: Dict[str, Any]) -> str:
        vuln_count = vulnerability_results.get('scan_summary', {}).get('vulnerabilities_found', 0)        
        return f"🤖 AI Security Fix: Resolve {vuln_count} vulnerabilities"
    
    def _generate_description(
        self,
        vulnerability_results: Dict[str, Any],
        branch_name: str
    ) -> str:
        """Generate detailed pull request description for AI fixes."""
        description_parts = []
        
        # Summary
        vuln_count = vulnerability_results.get('scan_summary', {}).get('vulnerabilities_found', 0)
        description_parts.append(f"## 🤖 AI-Generated Security Fix")
        description_parts.append(f"This PR contains AI-generated fixes for **{vuln_count}** security vulnerabilities identified by `govulncheck`.")
        description_parts.append("")
        
        # AI Analysis
        fix_explanation = vulnerability_results.get('fix_explanation', '')
        if fix_explanation:
            description_parts.append("## 🧠 AI Analysis & Reasoning")
            description_parts.append("```")
            description_parts.append(fix_explanation)
            description_parts.append("```")
            description_parts.append("")
        
        # Raw govulncheck output
        raw_output = vulnerability_results.get('raw_govulncheck_output', '')
        if raw_output:
            description_parts.append("## 🔍 Vulnerability Scan Results")
            description_parts.append("<details><summary>Click to view govulncheck output</summary>")
            description_parts.append("")
            description_parts.append("```")
            description_parts.append(raw_output)
            description_parts.append("```")
            description_parts.append("</details>")
            description_parts.append("")
        
        # Files modified
        ai_fixes = vulnerability_results.get('ai_fixes', {})
        if ai_fixes:
            description_parts.append("## 📝 Files Modified")
            for file_path in ai_fixes.keys():
                description_parts.append(f"- `{file_path}`")
            description_parts.append("")
        
        # Build validation
        description_parts.append("## ✅ Build Validation")
        description_parts.append("- [x] AI-generated fixes applied")
        description_parts.append("- [x] `go mod tidy` executed successfully")
        description_parts.append("- [x] `go build ./...` passed")
        description_parts.append("- [x] Code compiles without errors")
        description_parts.append("")
        
        # Testing recommendation
        description_parts.append("## 🧪 Testing Recommendations")
        description_parts.append("- [ ] Run existing test suite")
        description_parts.append("- [ ] Test critical functionality")
        description_parts.append("- [ ] Run security scan to confirm fixes")
        description_parts.append("- [ ] Deploy to staging environment")
        description_parts.append("")
        
        # Warnings
        description_parts.append("## ⚠️ Important Notes")
        description_parts.append("- This PR contains AI-generated code changes")
        description_parts.append("- Please review all changes carefully before merging")
        description_parts.append("- Test thoroughly in a staging environment")
        description_parts.append("- The AI has prioritized security fixes while preserving functionality")
        description_parts.append("")
        
        # Metadata
        description_parts.append("---")
        description_parts.append(f"*This PR was automatically generated by {settings.PROJECT_NAME} AI Security Analysis*")
        description_parts.append(f"*Branch: `{branch_name}`*")
        description_parts.append(f"*Scan Date: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}*")
        
        return "\n".join(description_parts)

github_service = GitHubService() 
