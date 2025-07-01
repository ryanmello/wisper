"""
Cleanup Repository Tool - Clean up temporary repository files and directories
"""

import os
import shutil
import stat
import time
import subprocess
from typing import Dict, Any
from langchain_core.tools import tool

from utils.logging_config import get_logger

logger = get_logger(__name__)

@tool
def cleanup_repository(repository_path: str) -> Dict[str, Any]:
    """Clean up temporary repository files and directories after analysis is complete.
    
    This tool removes the temporary directory containing the cloned repository to free up disk space. 
    Use this tool only AFTER all analysis is completely finished, as the repository files will be permanently 
    deleted and no further analysis will be possible. This is typically the final step in the analysis workflow.
    
    Prerequisites: Repository analysis must be complete
    Warning: This permanently deletes the repository files - use only when done
    
    Args:
        repository_path: Path to the temporary repository directory to clean up
        
    Returns:
        Dictionary with cleanup status and freed space information
    """
    if not repository_path or not os.path.exists(repository_path):
        return {
            "status": "success",
            "message": "Repository path does not exist or already cleaned",
            "path": repository_path
        }
    
    logger.info(f"Cleaning up repository at {repository_path}")
    
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
        shutil.rmtree(repository_path, onerror=handle_remove_readonly)
        if not os.path.exists(repository_path):
            logger.info(f"Successfully cleaned up repository at {repository_path}")
            return {
                "status": "success",
                "message": "Repository cleaned up successfully",
                "path": repository_path
            }
    except Exception as e:
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
            logger.info(f"Successfully cleaned up repository at {repository_path} (second attempt)")
            return {
                "status": "success",
                "message": "Repository cleaned up successfully (second attempt)",
                "path": repository_path
            }
    except Exception as e:
        logger.warning(f"Second cleanup attempt failed: {e}")
    
    # Method 3: Try Windows-specific rmdir command
    try:
        result = subprocess.run(['rmdir', '/s', '/q', repository_path], 
                              shell=True, check=False, capture_output=True, text=True)
        if not os.path.exists(repository_path):
            logger.info(f"Successfully cleaned up repository at {repository_path} (rmdir)")
            return {
                "status": "success",
                "message": "Repository cleaned up successfully (rmdir)",
                "path": repository_path
            }
    except Exception as e:
        logger.warning(f"rmdir cleanup attempt failed: {e}")
    
    # Method 4: Try PowerShell Remove-Item (more powerful than rmdir)
    try:
        ps_command = f'Remove-Item -Path "{repository_path}" -Recurse -Force -ErrorAction SilentlyContinue'
        result = subprocess.run(['powershell', '-Command', ps_command], 
                              check=False, capture_output=True, text=True)
        if not os.path.exists(repository_path):
            logger.info(f"Successfully cleaned up repository at {repository_path} (PowerShell)")
            return {
                "status": "success",
                "message": "Repository cleaned up successfully (PowerShell)",
                "path": repository_path
            }
    except Exception as e:
        logger.warning(f"PowerShell cleanup attempt failed: {e}")
    
    # If all methods fail, return partial success
    logger.warning(f"Could not fully cleanup directory: {repository_path}")
    return {
        "status": "partial_success",
        "message": "Repository cleanup had issues but continued",
        "path": repository_path
    } 