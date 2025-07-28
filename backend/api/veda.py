from fastapi import APIRouter, HTTPException
import uuid
import httpx
from utils.logging_config import get_logger
from models.api_models import VedaRequest, VedaResponse
from services.analysis_service import analysis_service
from config.settings import settings

logger = get_logger(__name__)
router = APIRouter()

@router.post("/analyze_comment", response_model=VedaResponse)
async def analyze_comment(request: VedaRequest):
    """
    Analyze a user comment for a pull request and prepare for AI processing
    """
    try:
        # Generate a unique task ID for this analysis
        task_id = str(uuid.uuid4())
        
        # Log the request details for debugging
        logger.info("Veda analyze comment request received:")
        logger.info(f"Task ID: {task_id}")
        logger.info(f"PR ID: {request.pr_id}")
        logger.info(f"Repository: {request.repo_owner}/{request.repo_name}")
        logger.info(f"User: {request.user_login}")
        logger.info(f"Comment: {request.user_comment}")
        
        # Fetch PR files and metadata from GitHub
        try:
            pr_context = await _fetch_pr_context(request.repo_owner, request.repo_name, request.pr_id)
            logger.info(f"Successfully fetched PR context with {len(pr_context['files'])} files")
        except Exception as e:
            logger.error(f"Failed to fetch PR context: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to fetch pull request data: {str(e)}")
        
        # Create repository URL for the orchestrator
        repository_url = f"https://github.com/{request.repo_owner}/{request.repo_name}"
        
        # Create enhanced prompt with PR context
        enhanced_prompt = _create_pr_analysis_prompt(request.user_comment, pr_context)
        
        # Start Veda analysis task
        await analysis_service.start_analysis(
            task_id=task_id,
            repository_url=repository_url,
            prompt=enhanced_prompt,
            pr_context=pr_context
        )
        
        # Return response with WebSocket URL
        websocket_url = f"ws://{settings.HOST}:{settings.PORT}/ws/veda/{task_id}"
        
        return VedaResponse(
            task_id=task_id,
            status="analysis_started",
            message=f"Veda is analyzing your request for PR #{request.pr_id}. Connect to WebSocket for real-time updates.",
            analysis_started=True,
            estimated_completion_time="2-3 minutes",
            websocket_url=websocket_url
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in analyze_comment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

async def _fetch_pr_context(repo_owner: str, repo_name: str, pr_id: int) -> dict:
    """Fetch pull request files and metadata from GitHub API"""
    if not settings.GITHUB_TOKEN:
        raise Exception("GitHub token not configured")
    
    token = settings.GITHUB_TOKEN
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }
    
    async with httpx.AsyncClient() as client:
        # Fetch PR metadata
        pr_url = f"{settings.GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/pulls/{pr_id}"
        pr_response = await client.get(pr_url, headers=headers)
        
        if pr_response.status_code != 200:
            raise Exception(f"Failed to fetch PR metadata: {pr_response.status_code}")
        
        pr_data = pr_response.json()
        
        # Fetch PR files
        files_url = f"{settings.GITHUB_API_URL}/repos/{repo_owner}/{repo_name}/pulls/{pr_id}/files"
        files_response = await client.get(files_url, headers=headers)
        
        if files_response.status_code != 200:
            raise Exception(f"Failed to fetch PR files: {files_response.status_code}")
        
        files_data = files_response.json()
        
        return {
            "pr_metadata": {
                "id": pr_data["number"],
                "title": pr_data["title"],
                "description": pr_data.get("body", ""),
                "state": pr_data["state"],
                "author": pr_data["user"]["login"],
                "branch": pr_data["head"]["ref"],
                "base_branch": pr_data["base"]["ref"],
                "url": pr_data["html_url"]
            },
            "files": files_data,
            "repository": {
                "owner": repo_owner,
                "name": repo_name,
                "full_name": f"{repo_owner}/{repo_name}"
            }
        }

def _create_pr_analysis_prompt(user_comment: str, pr_context: dict) -> str:
    """Create an enhanced prompt with PR context for the orchestrator"""
    pr_meta = pr_context["pr_metadata"]
    files = pr_context["files"]
    
    files_summary = []
    for file in files:
        files_summary.append(f"- {file['filename']} ({file['status']}: +{file['additions']} -{file['deletions']})")
    
    prompt = f"""PULL REQUEST ANALYSIS REQUEST

    You are analyzing Pull Request #{pr_meta['id']} in repository {pr_context['repository']['full_name']}.

    Pull Request Details:
    - PR ID: {pr_meta['id']}
    - Title: {pr_meta['title']}
    - Description: {pr_meta['description']}
    - Author: {pr_meta['author']}
    - Repository: {pr_context['repository']['owner']}/{pr_context['repository']['name']}
    - Base Branch: {pr_meta['base_branch']} (the main branch where changes will be merged)
    - PR Branch: {pr_meta['branch']} (the feature branch containing the proposed changes)
    - State: {pr_meta['state']}
    - URL: {pr_meta['url']}

    FILES CHANGED IN THIS PR:
    {chr(10).join(files_summary)}

    USER REQUEST/PROMPT:
    {user_comment}

    INSTRUCTIONS:
    The user wants to make changes to this pull request based on their comment above. 
    Analyze the current PR changes and implement the user's requested modifications.
    Use available tools to modify files as needed, and then update the pull request with your changes.
    Focus on making targeted changes that address the user's specific request while maintaining the existing PR's purpose.
    """
    
    return prompt
