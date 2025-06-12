"""
Repository Service - Handles repository cloning, cleanup, and analysis operations
"""

import os
import tempfile
import subprocess
import threading
import time
import shutil
import stat
import logging
from typing import Dict, Any, Optional
from pathlib import Path
from collections import Counter

# Git imports with error handling
try:
    from git import Repo, GitCommandError
    GIT_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Git integration not available - {e}")
    print("Install GitPython with: pip install GitPython==3.1.40")
    GIT_AVAILABLE = False
    class Repo: pass
    class GitCommandError(Exception): pass

from utils.logging_config import get_logger

logger = get_logger(__name__)

class RepositoryService:
    """
    Service for repository operations including cloning, cleanup, and language detection.
    
    Handles Git repository operations without any GitHub-specific logic.
    """
    
    def __init__(self):
        self.temp_dirs_to_cleanup = []
        
        # Check if Git is available
        if not GIT_AVAILABLE:
            logger.warning("Git dependencies not available. Repository operations will be limited.")
    
    def is_available(self) -> bool:
        """Check if repository service is available."""
        return GIT_AVAILABLE
    
    def clone_repository(self, repo_url: str) -> Dict[str, Any]:
        """
        Clone a repository to a temporary directory for analysis.
        
        Args:
            repo_url: Repository URL (GitHub, GitLab, etc.)
            
        Returns:
            Dictionary with clone results including status, path, and metadata
        """
        if not GIT_AVAILABLE:
            return {
                "status": "error",
                "error": "Git not available - install GitPython",
                "clone_path": None
            }
        
        temp_dir = None
        try:
            temp_dir = tempfile.mkdtemp(prefix="whisper_analysis_")
            self.temp_dirs_to_cleanup.append(temp_dir)
            
            # Clean URL and clone
            clean_url = self._normalize_repo_url(repo_url)
            
            repo = Repo.clone_from(clean_url, temp_dir)
            
            return {
                "status": "success",
                "clone_path": temp_dir,
                "repository_name": Path(clean_url).name.replace('.git', ''),
                "branch": repo.active_branch.name,
                "commit_count": len(list(repo.iter_commits())),
                "last_commit": repo.head.commit.hexsha[:8]
            }
            
        except Exception as e:
            # Clean up on error
            if temp_dir and os.path.exists(temp_dir):
                self.cleanup_directory(temp_dir)
            return {
                "status": "error",
                "error": str(e),
                "clone_path": None
            }
    
    def _normalize_repo_url(self, repo_url: str) -> str:
        """Normalize repository URL to standard format."""
        if repo_url.startswith('https://github.com/'):
            return repo_url
        elif repo_url.startswith('https://'):
            # Already a full URL for other providers
            return repo_url
        else:
            # Assume it's a GitHub shorthand like "owner/repo"
            return f"https://github.com/{repo_url.replace('https://github.com/', '')}"
    
    def cleanup_directory(self, directory_path: str) -> bool:
        """
        Safely clean up a directory, handling Windows read-only files.
        
        Args:
            directory_path: Path to directory to clean up
            
        Returns:
            True if cleanup was successful, False otherwise
        """
        if not os.path.exists(directory_path):
            return True
        
        def handle_remove_readonly(func, path, exc):
            """Handle read-only files on Windows."""
            try:
                # Make the file/directory writable
                os.chmod(path, stat.S_IWRITE)
                # For directories, also make all contents writable
                if os.path.isdir(path):
                    for root, dirs, files in os.walk(path):
                        for d in dirs:
                            try:
                                os.chmod(os.path.join(root, d), stat.S_IWRITE)
                            except:
                                pass
                        for f in files:
                            try:
                                os.chmod(os.path.join(root, f), stat.S_IWRITE)
                            except:
                                pass
                func(path)
            except Exception:
                pass
        
        # Method 1: Try shutil.rmtree with error handler
        try:
            shutil.rmtree(directory_path, onerror=handle_remove_readonly)
            if not os.path.exists(directory_path):
                return True
        except Exception:
            pass
        
        # Method 2: Try to make everything writable first, then delete
        try:
            for root, dirs, files in os.walk(directory_path):
                for d in dirs:
                    try:
                        os.chmod(os.path.join(root, d), stat.S_IWRITE)
                    except:
                        pass
                for f in files:
                    try:
                        os.chmod(os.path.join(root, f), stat.S_IWRITE)
                    except:
                        pass
            
            # Small delay to let Windows release file handles
            time.sleep(0.1)
            shutil.rmtree(directory_path)
            return True
        except Exception:
            pass
        
        # Method 3: Try Windows-specific rmdir command
        try:
            result = subprocess.run(['rmdir', '/s', '/q', directory_path], 
                                  shell=True, check=False, capture_output=True, text=True)
            if not os.path.exists(directory_path):
                return True
        except Exception:
            pass
        
        # Method 4: Try PowerShell Remove-Item (more powerful than rmdir)
        try:
            ps_command = f'Remove-Item -Path "{directory_path}" -Recurse -Force -ErrorAction SilentlyContinue'
            result = subprocess.run(['powershell', '-Command', ps_command], 
                                  check=False, capture_output=True, text=True)
            if not os.path.exists(directory_path):
                return True
        except Exception:
            pass
        
        # If all methods fail, return False but don't crash
        logger.warning(f"Failed to cleanup directory: {directory_path}")
        return False
    
    def schedule_delayed_cleanup(self, directory_path: str):
        """
        Schedule cleanup for later - common on Windows due to file locking.
        
        Args:
            directory_path: Path to directory to clean up later
        """
        def delayed_cleanup():
            # Wait a bit for file handles to be released
            time.sleep(2)
            
            # Try cleanup again
            for attempt in range(3):
                if self.cleanup_directory(directory_path):
                    logger.debug(f"Delayed cleanup successful for: {directory_path}")
                    return
                time.sleep(1)
            
            # If still can't clean up, it's likely Windows Temp cleanup will handle it
            logger.debug(f"Delayed cleanup failed for: {directory_path} (normal on Windows)")
        
        # Run cleanup in background thread
        cleanup_thread = threading.Thread(target=delayed_cleanup, daemon=True)
        cleanup_thread.start()
    
    def detect_primary_language(self, root_path: str) -> str:
        """
        Detect the primary programming language of the repository.
        
        Args:
            root_path: Path to repository root
            
        Returns:
            Primary language name or "Unknown"
        """
        languages = Counter()
        
        # Language detection by file extension
        language_map = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
            '.jsx': 'React JSX', '.tsx': 'TypeScript React',
            '.java': 'Java', '.cpp': 'C++', '.c': 'C',
            '.go': 'Go', '.rs': 'Rust', '.php': 'PHP',
            '.rb': 'Ruby', '.swift': 'Swift', '.kt': 'Kotlin',
            '.cs': 'C#', '.scala': 'Scala', '.clj': 'Clojure'
        }
        
        for root, dirs, files in os.walk(root_path):
            # Skip common directories that don't need analysis
            dirs[:] = [d for d in dirs if d not in {
                '.git', '__pycache__', 'node_modules', '.next', 'dist', 'build',
                '.vscode', '.idea', 'coverage', '.pytest_cache', 'venv', 'env'
            }]
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in language_map:
                    languages[language_map[ext]] += 1
        
        return languages.most_common(1)[0][0] if languages else "Unknown"
    
    def get_repository_info(self, repo_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a cloned repository.
        
        Args:
            repo_path: Path to cloned repository
            
        Returns:
            Dictionary with repository information
        """
        if not GIT_AVAILABLE or not os.path.exists(repo_path):
            return {}
        
        try:
            repo = Repo(repo_path)
            
            return {
                "current_branch": repo.active_branch.name,
                "remote_url": repo.remote().url,
                "last_commit": {
                    "hash": repo.head.commit.hexsha,
                    "message": repo.head.commit.message.strip(),
                    "author": str(repo.head.commit.author),
                    "date": repo.head.commit.committed_datetime.isoformat()
                },
                "total_commits": len(list(repo.iter_commits())),
                "branches": [branch.name for branch in repo.branches],
                "is_dirty": repo.is_dirty(),
                "untracked_files": repo.untracked_files
            }
        except Exception as e:
            logger.warning(f"Failed to get repository info: {e}")
            return {}
    
    def cleanup_all_temp_directories(self):
        """Clean up all temporary directories created during this session."""
        for temp_dir in self.temp_dirs_to_cleanup:
            if os.path.exists(temp_dir):
                success = self.cleanup_directory(temp_dir)
                if not success:
                    self.schedule_delayed_cleanup(temp_dir)
        
        self.temp_dirs_to_cleanup.clear()
        logger.debug("Cleaned up all temporary directories")


# Create singleton instance for application use
repository_service = RepositoryService()
