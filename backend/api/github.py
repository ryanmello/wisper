from fastapi import APIRouter, HTTPException
from utils.logging_config import get_logger
from config.settings import settings
from models.api_models import (
    GetRepositoriesRequest, GetRepositoriesResponse, GitHubRepository,
    GetPullRequestsRequest, GetPullRequestsResponse, GitHubPullRequest,
    GetPullRequestFilesRequest, GetPullRequestFilesResponse, GitHubFileChange,
    GetPullRequestCommentsRequest, GetPullRequestCommentsResponse, GitHubComment,
    PostPullRequestCommentRequest, PostPullRequestCommentResponse,
    GitHubUser, GitHubLabel, GetUserRequest
)
import httpx
from config.settings import settings

logger = get_logger(__name__)
router = APIRouter()

@router.post("/user", response_model=GitHubUser)
async def get_user(request: GetUserRequest):
    try:
        if not request.token:
            raise HTTPException(status_code=400, detail="GitHub token is required")
        
        token = request.token
        url = f"{settings.GITHUB_API_URL}/user"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid GitHub token")
            elif response.status_code != 200:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch user")
            
            user_data = response.json()
            return GitHubUser(
                login=user_data["login"],
                avatar_url=user_data["avatar_url"],
                name=user_data.get("name")
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching repositories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/repositories", response_model=GetRepositoriesResponse)
async def get_user_repositories(request: GetRepositoriesRequest):
    """
    Get authenticated user's repositories using GitHub token from settings
    """
    try:
        # Use token from settings
        if not settings.GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GitHub token not configured")
        
        token = settings.GITHUB_TOKEN
        logger.info(token)
        
        # GitHub API endpoint for user repositories
        url = f"{settings.GITHUB_API_URL}/user/repos"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Parameters for the repositories endpoint
        params = {
            "visibility": "all",  # Include both public and private repos
            "affiliation": "owner,collaborator",  # Include owned and collaborated repos
            "sort": request.sort,
            "direction": request.direction,
            "page": request.page,
            "per_page": request.per_page
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code == 401:
                raise HTTPException(status_code=401, detail="Invalid GitHub token")
            elif response.status_code != 200:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch repositories")
            
            repositories_data = response.json()
            
            # Transform the response to include relevant repository information
            repositories = []
            for repo in repositories_data:
                repo_data = GitHubRepository(
                    id=repo["id"],
                    name=repo["name"],
                    full_name=repo["full_name"],
                    description=repo.get("description"),
                    language=repo.get("language"),
                    stargazers_count=repo["stargazers_count"],
                    forks_count=repo["forks_count"],
                    updated_at=repo["updated_at"],
                    private=repo["private"]
                )
                repositories.append(repo_data)
            
            return GetRepositoriesResponse(
                total_count=len(repositories),
                repositories=repositories,
                page=request.page,
                per_page=request.per_page
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching repositories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/pull_requests", response_model=GetPullRequestsResponse)
async def get_pull_requests(request: GetPullRequestsRequest):
    """
    Get pull requests for a repository using GitHub token from settings
    """
    try:
        # Use token from settings
        if not settings.GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GitHub token not configured")
        
        token = settings.GITHUB_TOKEN
        
        # GitHub API endpoint for repository pull requests
        url = f"{settings.GITHUB_API_URL}/repos/{request.repo_owner}/{request.repo_name}/pulls"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Parameters for the pulls endpoint
        params = {
            "state": request.state,
            "sort": "updated",
            "direction": "desc",
            "page": request.page,
            "per_page": request.per_page
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Repository not found")
            elif response.status_code != 200:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch pull requests")
            
            pull_requests_data = response.json()
            
            # Transform the response to include relevant PR information
            pull_requests = []
            for pr in pull_requests_data:
                pr_data = GitHubPullRequest(
                    id=pr["number"],
                    title=pr["title"],
                    state=pr["state"],
                    repository={
                        "name": pr["base"]["repo"]["name"],
                        "full_name": pr["base"]["repo"]["full_name"],
                        "owner": pr["base"]["repo"]["owner"]["login"]
                    },
                    created_at=pr["created_at"],
                    updated_at=pr["updated_at"],
                    html_url=pr["html_url"],
                    user=GitHubUser(
                        login=pr["user"]["login"],
                        avatar_url=pr["user"]["avatar_url"],
                        name=pr["user"].get("name")
                    ),
                    comments=pr.get("comments", 0),
                    labels=[GitHubLabel(name=label["name"], color=label["color"]) for label in pr.get("labels", [])]
                )
                pull_requests.append(pr_data)
            
            return GetPullRequestsResponse(
                total_count=len(pull_requests),
                items=pull_requests,
                page=request.page,
                per_page=request.per_page
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pull requests: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/pull_requests/files", response_model=GetPullRequestFilesResponse)
async def get_pull_request_files(request: GetPullRequestFilesRequest):
    """
    Get file changes for a specific pull request
    """
    try:
        # Use token from settings
        if not settings.GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GitHub token not configured")
        
        token = settings.GITHUB_TOKEN
        
        # GitHub API endpoint for PR files
        url = f"{settings.GITHUB_API_URL}/repos/{request.repo_owner}/{request.repo_name}/pulls/{request.pr_id}/files"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Pull request not found")
            elif response.status_code != 200:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch PR files")
            
            files = response.json()
            
            # Transform the response to include relevant file information
            file_changes = []
            for file in files:
                file_data = GitHubFileChange(
                    filename=file["filename"],
                    status=file["status"],
                    additions=file["additions"],
                    deletions=file["deletions"],
                    changes=file["changes"],
                    patch=file.get("patch", ""),
                    previous_filename=file.get("previous_filename"),
                    blob_url=file["blob_url"],
                    raw_url=file["raw_url"]
                )
                file_changes.append(file_data)
            
            return GetPullRequestFilesResponse(
                pr_id=request.pr_id,
                repository=f"{request.repo_owner}/{request.repo_name}",
                files=file_changes,
                total_files=len(file_changes)
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching PR files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/pull_requests/comments", response_model=GetPullRequestCommentsResponse)
async def get_pull_request_comments(request: GetPullRequestCommentsRequest):
    """
    Get comments for a specific pull request
    """
    try:
        # Use token from settings
        if not settings.GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GitHub token not configured")
        
        token = settings.GITHUB_TOKEN
        
        # GitHub API endpoint for PR comments
        url = f"{settings.GITHUB_API_URL}/repos/{request.repo_owner}/{request.repo_name}/issues/{request.pr_id}/comments"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        params = {
            "page": request.page,
            "per_page": request.per_page
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, params=params)
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Pull request not found")
            elif response.status_code != 200:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to fetch PR comments")
            
            comments = response.json()
            
            # Transform the response to include relevant comment information
            comment_data = []
            for comment in comments:
                comment_info = GitHubComment(
                    id=comment["id"],
                    body=comment["body"],
                    user=GitHubUser(
                        login=comment["user"]["login"],
                        avatar_url=comment["user"]["avatar_url"],
                        name=comment["user"].get("name")
                    ),
                    created_at=comment["created_at"],
                    updated_at=comment["updated_at"],
                    html_url=comment["html_url"]
                )
                comment_data.append(comment_info)
            
            return GetPullRequestCommentsResponse(
                pr_id=request.pr_id,
                repository=f"{request.repo_owner}/{request.repo_name}",
                comments=comment_data,
                page=request.page,
                per_page=request.per_page
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching PR comments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/pull_requests/comments/create", response_model=PostPullRequestCommentResponse)
async def post_pull_request_comment(request: PostPullRequestCommentRequest):
    """
    Post a comment to a specific pull request
    """
    try:
        # Use token from settings
        if not settings.GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GitHub token not configured")
        
        token = settings.GITHUB_TOKEN
        
        # GitHub API endpoint for posting PR comments
        url = f"{settings.GITHUB_API_URL}/repos/{request.repo_owner}/{request.repo_name}/issues/{request.pr_id}/comments"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "body": request.body
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Pull request not found")
            elif response.status_code != 201:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to post comment")
            
            comment = response.json()
            
            comment_info = GitHubComment(
                id=comment["id"],
                body=comment["body"],
                user=GitHubUser(
                    login=comment["user"]["login"],
                    avatar_url=comment["user"]["avatar_url"],
                    name=comment["user"].get("name")
                ),
                created_at=comment["created_at"],
                updated_at=comment["updated_at"],
                html_url=comment["html_url"]
            )
            
            return PostPullRequestCommentResponse(
                comment=comment_info
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error posting PR comment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
