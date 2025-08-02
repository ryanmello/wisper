import os
import subprocess
import shutil
from typing import Dict, Optional
from dataclasses import dataclass
from config.settings import settings
from utils.logging_config import get_logger

logger = get_logger(__name__)

@dataclass
class BuildResult:
    success: bool
    build_output: str
    error_message: Optional[str] = None
    duration: float = 0.0
    updated_go_sum: Optional[str] = None

class BuildValidator:
    """Service for validating fixes by running go build."""
    
    def __init__(self):
        self.timeout = 120
    
    def validate_fixes(self, repo_path: str, updated_files: Dict[str, str]) -> BuildResult:
        """
        Validate fixes by applying them to the repository and running go build.
        
        Args:
            repo_path: Path to the repository
            updated_files: Dictionary of file_path -> new_content
            
        Returns:
            BuildResult indicating success/failure
        """
        backup_files = {}
        try:
            logger.info(f"Validating fixes in repository: {repo_path}")
            
            # Create backup of files we're about to modify
            for file_path in updated_files.keys():
                full_path = os.path.join(repo_path, file_path)
                if os.path.exists(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            backup_files[file_path] = f.read()
                        logger.debug(f"Backed up original content of {file_path}")
                    except Exception as e:
                        logger.warning(f"Could not backup {file_path}: {e}")
            
            # Always backup go.sum if it exists (go mod tidy may modify it)
            original_go_sum = None
            go_sum_path = os.path.join(repo_path, "go.sum")
            if os.path.exists(go_sum_path):
                try:
                    with open(go_sum_path, 'r', encoding='utf-8') as f:
                        original_go_sum = f.read()
                        # Add to backup_files so it gets restored on failure
                        if "go.sum" not in backup_files:
                            backup_files["go.sum"] = original_go_sum
                            logger.debug("Backed up original go.sum for restoration")
                except Exception as e:
                    logger.warning(f"Could not read original go.sum: {e}")
            
            # Apply the fixes to the repository
            self._apply_fixes(repo_path, updated_files)
            
            # Run go mod tidy first
            tidy_result = self._run_go_mod_tidy(repo_path)
            if not tidy_result.success:
                # Restore backups on failure
                self._restore_backups(repo_path, backup_files)
                return BuildResult(
                    success=False,
                    build_output=tidy_result.build_output,
                    error_message=f"go mod tidy failed: {tidy_result.error_message}"
                )
            
            # Run go build
            build_result = self._run_go_build(repo_path)
            
            # If validation failed, restore backups
            if not build_result.success:
                self._restore_backups(repo_path, backup_files)
                return build_result
            
            # If validation succeeded, capture updated go.sum content if it changed
            if os.path.exists(go_sum_path):
                try:
                    with open(go_sum_path, 'r', encoding='utf-8') as f:
                        updated_go_sum = f.read()
                    
                    if updated_go_sum != original_go_sum:
                        build_result.updated_go_sum = updated_go_sum
                        if original_go_sum is None:
                            logger.info("Captured newly created go.sum content")
                        else:
                            logger.info("Captured updated go.sum content")
                except Exception as e:
                    logger.warning(f"Could not capture updated go.sum: {e}")
            
            logger.info(f"Build validation {'succeeded' if build_result.success else 'failed'}")
            return build_result
            
        except Exception as e:
            logger.error(f"Build validation failed with exception: {e}")
            # Restore backups on exception
            self._restore_backups(repo_path, backup_files)
            return BuildResult(
                success=False,
                build_output="",
                error_message=f"Validation exception: {str(e)}"
            )
    
    def _restore_backups(self, repo_path: str, backup_files: Dict[str, str]):
        """Restore backed up files in case of validation failure."""
        if not backup_files:
            return
            
        logger.info(f"Restoring {len(backup_files)} backed up files")
        for file_path, original_content in backup_files.items():
            try:
                full_path = os.path.join(repo_path, file_path)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                logger.debug(f"Restored original content of {file_path}")
            except Exception as e:
                logger.error(f"Failed to restore backup of {file_path}: {e}")
    
    def _apply_fixes(self, repo_path: str, updated_files: Dict[str, str]):
        """Apply fixes to the repository."""
        logger.info(f"Applying {len(updated_files)} file updates")
        
        for file_path, new_content in updated_files.items():
            full_path = os.path.join(repo_path, file_path)
            
            # Create directory if it doesn't exist
            dir_path = os.path.dirname(full_path)
            if dir_path and not os.path.exists(dir_path):
                os.makedirs(dir_path, exist_ok=True)
            
            # Write the updated content
            try:
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                logger.debug(f"Applied fix to: {file_path}")
            except Exception as e:
                logger.error(f"Failed to apply fix to {file_path}: {e}")
                raise
    
    def _run_go_mod_tidy(self, repo_path: str) -> BuildResult:
        """Run go mod tidy to clean up dependencies."""
        logger.info("Running go mod tidy")
        
        try:
            import time
            start_time = time.time()
            
            result = subprocess.run(
                ["go", "mod", "tidy"],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=self.timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"go mod tidy completed successfully in {duration:.2f}s")
                return BuildResult(
                    success=True,
                    build_output=result.stdout,
                    duration=duration
                )
            else:
                logger.warning(f"go mod tidy failed: {result.stderr}")
                return BuildResult(
                    success=False,
                    build_output=result.stdout + "\n" + result.stderr,
                    error_message=result.stderr,
                    duration=duration
                )
                
        except subprocess.TimeoutExpired:
            error_msg = "go mod tidy timed out"
            logger.error(error_msg)
            return BuildResult(
                success=False,
                build_output="",
                error_message=error_msg
            )
        except FileNotFoundError:
            error_msg = "go command not found"
            logger.error(error_msg)
            return BuildResult(
                success=False,
                build_output="",
                error_message=error_msg
            )
        except Exception as e:
            error_msg = f"go mod tidy failed: {str(e)}"
            logger.error(error_msg)
            return BuildResult(
                success=False,
                build_output="",
                error_message=error_msg
            )
    
    def _run_go_build(self, repo_path: str) -> BuildResult:
        """Run go build to validate the fixes."""
        logger.info("Running go build ./...")
        
        try:
            import time
            start_time = time.time()
            
            result = subprocess.run(
                ["go", "build", "./..."],
                cwd=repo_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                timeout=self.timeout
            )
            
            duration = time.time() - start_time
            
            if result.returncode == 0:
                logger.info(f"go build completed successfully in {duration:.2f}s")
                return BuildResult(
                    success=True,
                    build_output=result.stdout,
                    duration=duration
                )
            else:
                logger.warning(f"go build failed: {result.stderr}")
                return BuildResult(
                    success=False,
                    build_output=result.stdout + "\n" + result.stderr,
                    error_message=result.stderr,
                    duration=duration
                )
                
        except subprocess.TimeoutExpired:
            error_msg = "go build timed out"
            logger.error(error_msg)
            return BuildResult(
                success=False,
                build_output="",
                error_message=error_msg
            )
        except FileNotFoundError:
            error_msg = "go command not found"
            logger.error(error_msg)
            return BuildResult(
                success=False,
                build_output="",
                error_message=error_msg
            )
        except Exception as e:
            error_msg = f"go build failed: {str(e)}"
            logger.error(error_msg)
            return BuildResult(
                success=False,
                build_output="",
                error_message=error_msg
            ) 
                