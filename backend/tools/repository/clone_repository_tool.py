import tempfile
from langchain_core.tools import tool
from git import Repo
from pathlib import Path
from config.settings import settings
from utils.logging_config import get_logger
from utils.response_builder import create_tool_response_builder
from models.api_models import StandardToolResponse

logger = get_logger(__name__)

@tool
def clone_repository(repository_url: str, branch: str = None) -> StandardToolResponse:
    """Clone a Git repository to local temporary storage for analysis.
    
    This tool downloads the entire repository codebase to a temporary directory where it can be analyzed by other tools. 
    This is typically the first step in any repository analysis workflow since most other analysis tools require 
    local access to the code files. The tool returns a clone_path that other tools can use to access the repository files.
    
    Prerequisites: None - this is a foundational tool
    Provides: clone_path for use by other analysis tools
    
    Args:
        repository_url: The GitHub repository URL to clone
        branch: Optional specific branch to checkout after cloning (e.g., "feature-branch", "security-fixes-123")
        
    Returns:
        StandardToolResponse with clone_path, repository_name, branch, and metadata
    """
    response_builder = create_tool_response_builder("clone_repository")
    temp_dir = None
    
    try:
        # Create temporary directory
        temp_dir = tempfile.mkdtemp(prefix=settings.TEMP_DIR_PREFIX)
        logger.info(f"Cloning repository {repository_url} to {temp_dir}")
        
        # Clone repository with specific branch if requested
        if branch:
            try:
                logger.info(f"Cloning repository with specific branch: {branch}")
                repo = Repo.clone_from(repository_url, temp_dir, branch=branch)
                final_branch = branch
                logger.info(f"Successfully cloned directly to branch: {branch}")
            except Exception as e:
                logger.warning(f"Failed to clone branch {branch}: {e}")
                logger.info(f"Falling back to default branch clone")
                repo = Repo.clone_from(repository_url, temp_dir)
                final_branch = repo.active_branch.name
        else:
            logger.info(f"Cloning repository with default branch")
            repo = Repo.clone_from(repository_url, temp_dir)
            final_branch = repo.active_branch.name
            
        logger.info(f"Clone completed on branch: {final_branch}")
        
        # Prepare successful response data
        clone_data = {
            "clone_path": temp_dir,
            "repository_name": Path(repository_url).name.replace('.git', ''),
            "branch": final_branch,
            "requested_branch": branch,
            "commit_count": len(list(repo.iter_commits())),
            "last_commit": repo.head.commit.hexsha[:8],
            "repository_url": repository_url
        }
        
        # Generate summary
        if branch and final_branch == branch:
            summary = f"Successfully cloned {clone_data['repository_name']} on branch '{final_branch}' ({clone_data['commit_count']} commits) to temporary directory"
        elif branch and final_branch != branch:
            summary = f"Successfully cloned {clone_data['repository_name']} on default branch '{final_branch}' (requested branch '{branch}' not found, {clone_data['commit_count']} commits) to temporary directory"
        else:
            summary = f"Successfully cloned {clone_data['repository_name']} on default branch '{final_branch}' ({clone_data['commit_count']} commits) to temporary directory"
        
        # Create metrics
        metrics = {
            "items_processed": 1,  # One repository cloned
            "files_analyzed": 0    # Will be updated by subsequent tools
        }
        
        logger.info(f"Successfully cloned repository to {temp_dir}")
        
        return response_builder.build_success(
            data=clone_data,
            summary=summary,
            metrics=metrics
        )
        
    except Exception as e:
        logger.error(f"Failed to clone repository {repository_url}: {e}")
        
        # Cleanup on failure
        if temp_dir:
            try:
                import shutil
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up failed clone directory: {temp_dir}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup directory {temp_dir}: {cleanup_error}")
        
        # Return standardized error response
        return response_builder.build_error(
            error_message=f"Failed to clone repository: {str(e)}",
            error_details=f"Repository URL: {repository_url}, Error: {str(e)}",
            error_type="clone_failure",
            data={
                "repository_url": repository_url,
                "clone_path": None,
                "attempted_temp_dir": temp_dir
            }
        ) 
