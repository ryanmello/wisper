from fastapi import Request, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from services.auth_service import auth_service
from models.database_models import User
from utils.logging_config import get_logger

logger = get_logger(__name__)

class SessionAuthMiddleware:
    """Middleware for session-based authentication"""
    
    @staticmethod
    async def get_current_user_from_session(request: Request) -> Optional[User]:
        """Get current user from session cookie"""
        try:
            # Get session ID from cookie
            session_id = request.cookies.get("session_id")
            if not session_id:
                return None
            
            # Get user by session
            user = await auth_service.get_user_by_session(session_id)
            return user
            
        except Exception as e:
            logger.error(f"Error getting user from session: {e}")
            return None
    
    @staticmethod
    async def require_authentication(request: Request) -> User:
        """Require authentication and return user or raise HTTPException"""
        user = await SessionAuthMiddleware.get_current_user_from_session(request)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required",
                headers={"WWW-Authenticate": "Session"},
            )
        
        return user
    
    @staticmethod
    async def get_user_github_token(user: User) -> str:
        """Get GitHub token for authenticated user"""
        token = await auth_service.get_user_github_token(user.id)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GitHub token not available"
            )
        return token

# FastAPI dependency functions
async def get_current_user(request: Request) -> User:
    """FastAPI dependency to get current authenticated user"""
    return await SessionAuthMiddleware.require_authentication(request)

async def get_optional_user(request: Request) -> Optional[User]:
    """FastAPI dependency to get current user if authenticated"""
    return await SessionAuthMiddleware.get_current_user_from_session(request) 
