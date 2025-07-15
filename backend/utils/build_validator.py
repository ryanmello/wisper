import os
import subprocess
import tempfile
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
        Validate fixes by applying them and running go build.
        
        Args:
            repo_path: Path to the repository
            updated_files: Dictionary of file_path -> new_content
            
        Returns:
            BuildResult indicating success/failure
        """
        temp_dir = None
        try:
            # Create a temporary copy of the repository
            temp_dir = tempfile.mkdtemp(prefix=f"{settings.PROJECT_NAME}_build_validation_")
            logger.info(f"Created temporary directory for build validation: {temp_dir}")
            
            # Copy repository to temp directory
            self._copy_repository(repo_path, temp_dir)
            
            # Apply the fixes to the temporary copy
            self._apply_fixes(temp_dir, updated_files)
            
            # Run go mod tidy first
            tidy_result = self._run_go_mod_tidy(temp_dir)
            if not tidy_result.success:
                return BuildResult(
                    success=False,
                    build_output=tidy_result.build_output,
                    error_message=f"go mod tidy failed: {tidy_result.error_message}"
                )
            
            # Run go build
            build_result = self._run_go_build(temp_dir)
            
            # If validation succeeded, capture updated go.sum content
            if build_result.success:
                go_sum_path = os.path.join(temp_dir, "go.sum")
                if os.path.exists(go_sum_path):
                    try:
                        with open(go_sum_path, 'r', encoding='utf-8') as f:
                            updated_go_sum = f.read()
                        
                        # Check if go.sum actually changed by comparing with original
                        original_go_sum_path = os.path.join(repo_path, "go.sum")
                        if os.path.exists(original_go_sum_path):
                            with open(original_go_sum_path, 'r', encoding='utf-8') as f:
                                original_go_sum = f.read()
                            if updated_go_sum != original_go_sum:
                                build_result.updated_go_sum = updated_go_sum
                                logger.info("Captured updated go.sum content")
                        else:
                            # go.sum was created new by go mod tidy
                            build_result.updated_go_sum = updated_go_sum  
                            logger.info("Captured newly created go.sum content")
                    except Exception as e:
                        logger.warning(f"Could not capture updated go.sum: {e}")
            
            logger.info(f"Build validation {'succeeded' if build_result.success else 'failed'}")
            return build_result
            
        except Exception as e:
            logger.error(f"Build validation failed with exception: {e}")
            return BuildResult(
                success=False,
                build_output="",
                error_message=f"Validation exception: {str(e)}"
            )
        finally:
            # Clean up temporary directory
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    logger.debug(f"Cleaned up temporary directory: {temp_dir}")
                except Exception as e:
                    logger.warning(f"Failed to clean up temporary directory: {e}")
    
    def _copy_repository(self, source_path: str, dest_path: str):
        """Copy repository to temporary directory."""
        logger.debug(f"Copying repository from {source_path} to {dest_path}")
        
        # Copy all files except common ignore patterns
        ignore_patterns = {
            '.git', '__pycache__', 'node_modules', '.vscode', '.idea',
            'vendor', 'dist', 'build', '.next', 'coverage'
        }
        
        for item in os.listdir(source_path):
            if item not in ignore_patterns:
                source_item = os.path.join(source_path, item)
                dest_item = os.path.join(dest_path, item)
                
                if os.path.isdir(source_item):
                    shutil.copytree(source_item, dest_item)
                else:
                    shutil.copy2(source_item, dest_item)
    
    def _apply_fixes(self, repo_path: str, updated_files: Dict[str, str]):
        """Apply fixes to the repository copy."""
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
                