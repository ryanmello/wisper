from fastapi import APIRouter, HTTPException, Request, Response, Depends, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
from services.auth_service import auth_service
from middleware.auth_middleware import get_current_user, get_optional_user
from models.database_models import User
from models.api_models import GitHubUser
from config.settings import settings
from utils.logging_config import get_logger
import os

logger = get_logger(__name__)
router = APIRouter(prefix="/auth")

# Request/Response models
class GitHubCallbackRequest(BaseModel):
    code: str
    state: Optional[str] = None

class AuthResponse(BaseModel):
    success: bool
    message: str
    user: Optional[GitHubUser] = None

class SessionStatusResponse(BaseModel):
    authenticated: bool
    user: Optional[GitHubUser] = None

# Environment variables
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

@router.get("/github/authorize")
async def github_authorize(request: Request):
    """Redirect to GitHub OAuth authorization"""
    if not GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=500,
            detail="GitHub OAuth not configured"
        )
    
    redirect_uri = f"{FRONTEND_URL}/auth/callback"
    scope = "repo user"
    
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&response_type=code"
    )
    
    return RedirectResponse(url=github_auth_url)

@router.post("/github/callback", response_model=AuthResponse)
async def github_callback(
    callback_request: GitHubCallbackRequest,
    request: Request,
    response: Response
):
    """Handle GitHub OAuth callback"""
    try:
        if not callback_request.code:
            raise HTTPException(
                status_code=400,
                detail="Authorization code is required"
            )
        
        # Exchange code for token
        token = await auth_service.exchange_code_for_token(callback_request.code)
        if not token:
            raise HTTPException(
                status_code=400,
                detail="Failed to exchange authorization code for token"
            )
        
        # Get GitHub user info
        github_user_data = await auth_service.get_github_user_info(token)
        if not github_user_data:
            raise HTTPException(
                status_code=400,
                detail="Failed to get GitHub user information"
            )
        
        # Create or update user in database
        user = await auth_service.create_or_update_user(github_user_data, token)
        if not user:
            raise HTTPException(
                status_code=500,
                detail="Failed to create user session"
            )
        
        # Create session
        user_agent = request.headers.get("user-agent")
        client_ip = request.client.host if request.client else None
        session = await auth_service.create_session(user.id, user_agent, client_ip)
        
        if not session:
            raise HTTPException(
                status_code=500,
                detail="Failed to create user session"
            )
        
        # Set secure session cookie
        response.set_cookie(
            key="session_id",
            value=session.id,
            max_age=60 * 60 * 24 * 7,  # 7 days
            httponly=True,
            secure=FRONTEND_URL.startswith("https://"),  # Only secure in production (HTTPS)
            samesite="lax"
        )
        
        user_info = GitHubUser(
            login=user.github_login,
            avatar_url=user.avatar_url,
            name=user.github_name
        )
        
        logger.info(f"User {user.github_login} authenticated successfully")
        
        return AuthResponse(
            success=True,
            message="Authentication successful",
            user=user_info
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OAuth callback error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Authentication failed"
        )

@router.get("/status", response_model=SessionStatusResponse)
async def get_auth_status(user: Optional[User] = Depends(get_optional_user)):
    """Get current authentication status"""
    if user:
        user_info = GitHubUser(
            login=user.github_login,
            avatar_url=user.avatar_url,
            name=user.github_name
        )
        return SessionStatusResponse(authenticated=True, user=user_info)
    else:
        return SessionStatusResponse(authenticated=False, user=None)

@router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user and invalidate session"""
    try:
        session_id = request.cookies.get("session_id")
        if session_id:
            await auth_service.invalidate_session(session_id)
        
        # Clear session cookie
        response.delete_cookie(key="session_id", path="/")
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Logout failed"
        )

@router.get("/user", response_model=GitHubUser)
async def get_current_user_info(user: User = Depends(get_current_user)):
    """Get current authenticated user information"""
    return GitHubUser(
        login=user.github_login,
        avatar_url=user.avatar_url,
        name=user.github_name
    )

@router.post("/refresh")
async def refresh_session(
    request: Request,
    response: Response,
    user: User = Depends(get_current_user)
):
    """Refresh current session"""
    try:
        session_id = request.cookies.get("session_id")
        if not session_id:
            raise HTTPException(
                status_code=401,
                detail="No session found"
            )
        
        # Create new session
        user_agent = request.headers.get("user-agent")
        client_ip = request.client.host if request.client else None
        new_session = await auth_service.create_session(user.id, user_agent, client_ip)
        
        if not new_session:
            raise HTTPException(
                status_code=500,
                detail="Failed to refresh session"
            )
        
        # Invalidate old session
        await auth_service.invalidate_session(session_id)
        
        # Set new session cookie
        response.set_cookie(
            key="session_id",
            value=new_session.id,
            max_age=60 * 60 * 24 * 7,  # 7 days
            httponly=True,
            secure=FRONTEND_URL.startswith("https://"),  # Only secure in production (HTTPS)
            samesite="lax"
        )
        
        return {"success": True, "message": "Session refreshed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Session refresh error: {e}")
        raise HTTPException(
            status_code=500,
            detail="Session refresh failed"
        ) 