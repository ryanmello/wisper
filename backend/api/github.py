from fastapi import APIRouter, HTTPException, Header, Query
from typing import Optional, List
from utils.logging_config import get_logger
from services.github_service import github_service
from config.settings import settings
import httpx
import json

logger = get_logger(__name__)
router = APIRouter()

@router.get("/repositories")
async def get_user_repositories(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    per_page: int = Query(30, ge=1, le=100, description="Number of repositories per page"),
    sort: str = Query("updated", description="Sort by: created, updated, pushed, full_name"),
    direction: str = Query("desc", description="Sort direction: asc or desc")
):
    """
    Get authenticated user's repositories using GitHub token from settings
    """
    try:
        # Use token from settings
        if not settings.GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GitHub token not configured")
        
        token = settings.GITHUB_TOKEN
        
        # GitHub API endpoint for user repositories
        url = "https://api.github.com/user/repos"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Parameters for the repositories endpoint
        params = {
            "visibility": "all",  # Include both public and private repos
            "affiliation": "owner,collaborator",  # Include owned and collaborated repos
            "sort": sort,
            "direction": direction,
            "page": page,
            "per_page": per_page
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
                repo_data = {
                    "id": repo["id"],
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "description": repo.get("description"),
                    "language": repo.get("language"),
                    "stargazers_count": repo["stargazers_count"],
                    "forks_count": repo["forks_count"],
                    "updated_at": repo["updated_at"],
                    "private": repo["private"]
                }
                repositories.append(repo_data)
            
            return {
                "total_count": len(repositories),
                "repositories": repositories,
                "page": page,
                "per_page": per_page
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching repositories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/pullrequests")
async def get_user_pull_requests(
    page: int = Query(1, ge=1, description="Page number for pagination"),
    per_page: int = Query(30, ge=1, le=100, description="Number of PRs per page"),
    state: str = Query("open", description="State of PRs: open, closed, or all"),
    repo_owner: str = Query(None, description="Repository owner to filter by"),
    repo_name: str = Query(None, description="Repository name to filter by")
):
    """
    Get user's pull requests using GitHub token from settings
    """
    try:
        # Use token from settings
        if not settings.GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GitHub token not configured")
        
        token = settings.GITHUB_TOKEN
        
        # Require repository parameters for direct PR endpoint
        if not repo_owner or not repo_name:
            raise HTTPException(status_code=400, detail="repo_owner and repo_name are required")
        
        # GitHub API endpoint for repository pull requests
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Parameters for the pulls endpoint
        params = {
            "state": state,
            "sort": "updated",
            "direction": "desc",
            "page": page,
            "per_page": per_page
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
                pr_data = {
                    "id": pr["number"],
                    "title": pr["title"],
                    "state": pr["state"],
                    "repository": {
                        "name": pr["base"]["repo"]["name"],
                        "full_name": pr["base"]["repo"]["full_name"],
                        "owner": pr["base"]["repo"]["owner"]["login"]
                    },
                    "created_at": pr["created_at"],
                    "updated_at": pr["updated_at"],
                    "html_url": pr["html_url"],
                    "user": {
                        "login": pr["user"]["login"],
                        "avatar_url": pr["user"]["avatar_url"]
                    },
                    "comments": pr.get("comments", 0),
                    "labels": [{"name": label["name"], "color": label["color"]} for label in pr.get("labels", [])]
                }
                pull_requests.append(pr_data)
            
            return {
                "total_count": len(pull_requests),
                "items": pull_requests,
                "page": page,
                "per_page": per_page
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching pull requests: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/pullrequests/{pr_id}/files")
async def get_pull_request_files(
    pr_id: int,
    repo_owner: str = Query(..., description="Repository owner"),
    repo_name: str = Query(..., description="Repository name")
):
    """
    Get file changes for a specific pull request
    """
    try:
        # Use token from settings
        if not settings.GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GitHub token not configured")
        
        token = settings.GITHUB_TOKEN
        
        # GitHub API endpoint for PR files
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_id}/files"
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
                file_data = {
                    "filename": file["filename"],
                    "status": file["status"],  # added, modified, removed, renamed
                    "additions": file["additions"],
                    "deletions": file["deletions"],
                    "changes": file["changes"],
                    "patch": file.get("patch", ""),
                    "previous_filename": file.get("previous_filename"),
                    "blob_url": file["blob_url"],
                    "raw_url": file["raw_url"]
                }
                file_changes.append(file_data)
            
            return {
                "pr_id": pr_id,
                "repository": f"{repo_owner}/{repo_name}",
                "files": file_changes,
                "total_files": len(file_changes)
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching PR files: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/pullrequests/{pr_id}/comments")
async def get_pull_request_comments(
    pr_id: int,
    repo_owner: str = Query(..., description="Repository owner"),
    repo_name: str = Query(..., description="Repository name"),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    per_page: int = Query(30, ge=1, le=100, description="Number of comments per page")
):
    """
    Get comments for a specific pull request
    """
    try:
        # Use token from settings
        if not settings.GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GitHub token not configured")
        
        token = settings.GITHUB_TOKEN
        
        # GitHub API endpoint for PR comments
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_id}/comments"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        params = {
            "page": page,
            "per_page": per_page
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
                comment_info = {
                    "id": comment["id"],
                    "body": comment["body"],
                    "user": {
                        "login": comment["user"]["login"],
                        "avatar_url": comment["user"]["avatar_url"]
                    },
                    "created_at": comment["created_at"],
                    "updated_at": comment["updated_at"],
                    "html_url": comment["html_url"]
                }
                comment_data.append(comment_info)
            
            return {
                "pr_id": pr_id,
                "repository": f"{repo_owner}/{repo_name}",
                "comments": comment_data,
                "page": page,
                "per_page": per_page
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching PR comments: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.post("/pullrequests/{pr_id}/comments")
async def post_pull_request_comment(
    pr_id: int,
    repo_owner: str = Query(..., description="Repository owner"),
    repo_name: str = Query(..., description="Repository name"),
    comment_body: dict = None
):
    """
    Post a comment to a specific pull request
    """
    try:
        # Use token from settings
        if not settings.GITHUB_TOKEN:
            raise HTTPException(status_code=500, detail="GitHub token not configured")
        
        token = settings.GITHUB_TOKEN
        
        if not comment_body or "body" not in comment_body:
            raise HTTPException(status_code=400, detail="Comment body is required")
        
        # GitHub API endpoint for posting PR comments
        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/issues/{pr_id}/comments"
        headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json"
        }
        
        payload = {
            "body": comment_body["body"]
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="Pull request not found")
            elif response.status_code != 201:
                logger.error(f"GitHub API error: {response.status_code} - {response.text}")
                raise HTTPException(status_code=response.status_code, detail="Failed to post comment")
            
            comment = response.json()
            
            return {
                "id": comment["id"],
                "body": comment["body"],
                "user": {
                    "login": comment["user"]["login"],
                    "avatar_url": comment["user"]["avatar_url"]
                },
                "created_at": comment["created_at"],
                "updated_at": comment["updated_at"],
                "html_url": comment["html_url"]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error posting PR comment: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
