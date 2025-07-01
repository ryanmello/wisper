"""
Clone Repository Tool - Clone Git repositories to local temporary storage
"""

import tempfile
from typing import Dict, Any
from langchain_core.tools import tool
from git import Repo
from pathlib import Path

from config.settings import settings
from utils.logging_config import get_logger

logger = get_logger(__name__)

@tool
def clone_repository(repository_url: str) -> Dict[str, Any]:
    """Clone a Git repository to local temporary storage for analysis.
    
    This tool downloads the entire repository codebase to a temporary directory where it can be analyzed by other tools. 
    This is typically the first step in any repository analysis workflow since most other analysis tools require 
    local access to the code files. The tool returns a clone_path that other tools can use to access the repository files.
    
    Prerequisites: None - this is a foundational tool
    Provides: clone_path for use by other analysis tools
    
    Args:
        repository_url: The GitHub repository URL to clone
        
    Returns:
        Dictionary with clone_path, repository_name, branch, and metadata
    """
    temp_dir = None
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=settings.TEMP_DIR_PREFIX)
        logger.info(f"Cloning repository {repository_url} to {temp_dir}")
        
        # Clone repository
        repo = Repo.clone_from(repository_url, temp_dir)
        
        result = {
            "status": "success",
            "clone_path": temp_dir,
            "repository_name": Path(repository_url).name.replace('.git', ''),
            "branch": repo.active_branch.name,
            "commit_count": len(list(repo.iter_commits())),
            "last_commit": repo.head.commit.hexsha[:8],
            # Tool metadata for result compilation
            "_tool_metadata": {
                "category": "infrastructure",
                "result_type": "setup",
                "output_keys": ["clone_path", "repository_name", "branch"],
                "priority": 1  # High priority for setup tools
            }
        }
        
        logger.info(f"Successfully cloned repository to {temp_dir}")
        return result
        
    except Exception as e:
        logger.error(f"Failed to clone repository {repository_url}: {e}")
        
        # Cleanup on failure
        if temp_dir:
            try:
                import shutil
                shutil.rmtree(temp_dir)
            except:
                pass
        
        return {
            "status": "error",
            "error": str(e),
            "clone_path": None,
            "_tool_metadata": {
                "category": "infrastructure",
                "result_type": "setup",
                "output_keys": [],
                "priority": 1
            }
        } 