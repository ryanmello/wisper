import os
import shutil
import stat
import time
import subprocess
from langchain_core.tools import tool
from utils.logging_config import get_logger
from utils.tool_metadata_decorator import tool_category
from utils.response_builder import create_tool_response_builder
from models.api_models import StandardToolResponse

logger = get_logger(__name__)

@tool_category("repository")
@tool
def cleanup_repository(repository_path: str) -> StandardToolResponse:
    """Clean up cloned repository.
    
    Clean up temporary repository files and directories of cloned repository.

    This tool removes the temporary directory containing the cloned repository 
    and should always be the last tool used if you cloned the repository.
        
    Args:
        repository_path: Path to the temporary repository directory to clean up
        
    Returns:
        StandardToolResponse with cleanup status
    """
    response_builder = create_tool_response_builder("cleanup_repository")
    
    if not repository_path or not os.path.exists(repository_path):
        return response_builder.build_success(
            data={
                "path": repository_path,
                "already_cleaned": True,
                "freed_space_bytes": 0
            },
            summary="Repository path does not exist or already cleaned"
        )
    
    logger.info(f"Cleaning up repository at {repository_path}")
    
    # Calculate directory size before cleanup for metrics
    initial_size = 0
    try:
        for dirpath, dirnames, filenames in os.walk(repository_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    initial_size += os.path.getsize(fp)
                except (OSError, IOError):
                    pass
    except Exception:
        initial_size = 0
    
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
    
    cleanup_method = None
    warnings = []
    
    # Method 1: Try shutil.rmtree with error handler
    try:
        shutil.rmtree(repository_path, onerror=handle_remove_readonly)
        if not os.path.exists(repository_path):
            cleanup_method = "shutil.rmtree"
            logger.info(f"Successfully cleaned up repository at {repository_path}")
            
            return response_builder.build_success(
                data={
                    "path": repository_path,
                    "cleanup_method": cleanup_method,
                    "freed_space_bytes": initial_size,
                    "freed_space_mb": round(initial_size / (1024 * 1024), 2)
                },
                summary=f"Repository cleaned up successfully using {cleanup_method} (freed {round(initial_size / (1024 * 1024), 2)} MB)",
                metrics={
                    "items_processed": 1,
                    "files_analyzed": 0  # This is cleanup, not analysis
                }
            )
    except Exception as e:
        warnings.append(f"Initial cleanup attempt failed: {e}")
        logger.warning(f"Initial cleanup attempt failed: {e}")
    
    # Method 2: Try to make everything writable first, then delete
    try:
        for root, dirs, files in os.walk(repository_path):
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
        shutil.rmtree(repository_path)
        
        if not os.path.exists(repository_path):
            cleanup_method = "chmod + shutil.rmtree"
            logger.info(f"Successfully cleaned up repository at {repository_path} (second attempt)")
            
            return response_builder.build_success(
                data={
                    "path": repository_path,
                    "cleanup_method": cleanup_method,
                    "freed_space_bytes": initial_size,
                    "freed_space_mb": round(initial_size / (1024 * 1024), 2)
                },
                summary=f"Repository cleaned up successfully using {cleanup_method} (freed {round(initial_size / (1024 * 1024), 2)} MB)",
                metrics={
                    "items_processed": 1,
                    "files_analyzed": 0
                },
                warnings=warnings
            )
    except Exception as e:
        warnings.append(f"Second cleanup attempt failed: {e}")
        logger.warning(f"Second cleanup attempt failed: {e}")
    
    # Method 3: Try Windows-specific rmdir command
    try:
        result = subprocess.run(['rmdir', '/s', '/q', repository_path], 
                              shell=True, check=False, capture_output=True, text=True)
        if not os.path.exists(repository_path):
            cleanup_method = "Windows rmdir"
            logger.info(f"Successfully cleaned up repository at {repository_path} (rmdir)")
            
            return response_builder.build_success(
                data={
                    "path": repository_path,
                    "cleanup_method": cleanup_method,
                    "freed_space_bytes": initial_size,
                    "freed_space_mb": round(initial_size / (1024 * 1024), 2)
                },
                summary=f"Repository cleaned up successfully using {cleanup_method} (freed {round(initial_size / (1024 * 1024), 2)} MB)",
                metrics={
                    "items_processed": 1,
                    "files_analyzed": 0
                },
                warnings=warnings
            )
    except Exception as e:
        warnings.append(f"rmdir cleanup attempt failed: {e}")
        logger.warning(f"rmdir cleanup attempt failed: {e}")
    
    # Method 4: Try PowerShell Remove-Item (more powerful than rmdir)
    try:
        ps_command = f'Remove-Item -Path "{repository_path}" -Recurse -Force -ErrorAction SilentlyContinue'
        result = subprocess.run(['powershell', '-Command', ps_command], 
                              check=False, capture_output=True, text=True)
        if not os.path.exists(repository_path):
            cleanup_method = "PowerShell Remove-Item"
            logger.info(f"Successfully cleaned up repository at {repository_path} (PowerShell)")
            
            return response_builder.build_success(
                data={
                    "path": repository_path,
                    "cleanup_method": cleanup_method,
                    "freed_space_bytes": initial_size,
                    "freed_space_mb": round(initial_size / (1024 * 1024), 2)
                },
                summary=f"Repository cleaned up successfully using {cleanup_method} (freed {round(initial_size / (1024 * 1024), 2)} MB)",
                metrics={
                    "items_processed": 1,
                    "files_analyzed": 0
                },
                warnings=warnings
            )
    except Exception as e:
        warnings.append(f"PowerShell cleanup attempt failed: {e}")
        logger.warning(f"PowerShell cleanup attempt failed: {e}")
    
    # If all methods fail, return partial success or error
    if os.path.exists(repository_path):
        logger.warning(f"Could not fully cleanup directory: {repository_path}")
        
        # Check if directory is smaller (partial cleanup)
        remaining_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(repository_path):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    try:
                        remaining_size += os.path.getsize(fp)
                    except (OSError, IOError):
                        pass
        except Exception:
            remaining_size = initial_size
        
        freed_space = initial_size - remaining_size
        
        if freed_space > 0:
            # Partial success - some files were deleted
            return response_builder.build_partial_success(
                data={
                    "path": repository_path,
                    "cleanup_method": "partial",
                    "freed_space_bytes": freed_space,
                    "freed_space_mb": round(freed_space / (1024 * 1024), 2),
                    "remaining_size_bytes": remaining_size,
                    "remaining_size_mb": round(remaining_size / (1024 * 1024), 2)
                },
                error_message="Repository cleanup partially completed",
                summary=f"Partial cleanup completed (freed {round(freed_space / (1024 * 1024), 2)} MB, {round(remaining_size / (1024 * 1024), 2)} MB remaining)",
                metrics={
                    "items_processed": 1,
                    "files_analyzed": 0
                },
                warnings=warnings,
                error_details="Some files could not be deleted due to permissions or locks"
            )
        else:
            # Complete failure
            return response_builder.build_error(
                error_message="Failed to cleanup repository directory",
                error_details=f"All cleanup methods failed. Warnings: {'; '.join(warnings)}",
                error_type="cleanup_failure",
                data={
                    "path": repository_path,
                    "initial_size_bytes": initial_size,
                    "initial_size_mb": round(initial_size / (1024 * 1024), 2),
                    "warnings": warnings
                }
            )
    else:
        # This shouldn't happen but handle gracefully
        return response_builder.build_success(
            data={
                "path": repository_path,
                "cleanup_method": "unknown",
                "freed_space_bytes": initial_size,
                "freed_space_mb": round(initial_size / (1024 * 1024), 2)
            },
            summary=f"Repository cleanup completed (freed {round(initial_size / (1024 * 1024), 2)} MB)",
            metrics={
                "items_processed": 1,
                "files_analyzed": 0
            },
            warnings=warnings
        ) 
