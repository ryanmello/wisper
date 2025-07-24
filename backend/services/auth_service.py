from typing import Optional, Dict, Any
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from models.database_models import User, Session, TokenEncryption
from config.database import async_session_factory
from config.settings import settings
import httpx
import secrets
from utils.logging_config import get_logger
import os

logger = get_logger(__name__)

class AuthService:
    """Authentication service for managing GitHub OAuth and user sessions"""
    
    def __init__(self):
        self.github_client_id = os.getenv("GITHUB_CLIENT_ID")
        self.github_client_secret = os.getenv("GITHUB_CLIENT_SECRET")
    
    async def exchange_code_for_token(self, code: str) -> Optional[str]:
        """Exchange GitHub OAuth code for access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    "https://github.com/login/oauth/access_token",
                    headers={"Accept": "application/json"},
                    data={
                        "client_id": self.github_client_id,
                        "client_secret": self.github_client_secret,
                        "code": code,
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if "access_token" in data:
                        return data["access_token"]
                
                logger.error(f"Failed to exchange code for token: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error exchanging code for token: {e}")
            return None
    
    async def get_github_user_info(self, token: str) -> Optional[Dict[str, Any]]:
        """Get GitHub user information using access token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"token {token}",
                        "Accept": "application/vnd.github.v3+json"
                    }
                )
                
                if response.status_code == 200:
                    return response.json()
                
                logger.error(f"Failed to get GitHub user info: {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting GitHub user info: {e}")
            return None
    
    async def create_or_update_user(self, github_user: Dict[str, Any], token: str) -> Optional[User]:
        """Create or update user in database"""
        try:
            encrypted_token = TokenEncryption.encrypt_token(token)
            
            async with async_session_factory() as session:
                # Check if user already exists
                result = await session.execute(
                    select(User).where(User.github_id == github_user["id"])
                )
                existing_user = result.scalar_one_or_none()
                
                if existing_user:
                    # Update existing user
                    await session.execute(
                        update(User)
                        .where(User.github_id == github_user["id"])
                        .values(
                            github_login=github_user["login"],
                            github_name=github_user.get("name"),
                            github_email=github_user.get("email"),
                            avatar_url=github_user.get("avatar_url"),
                            encrypted_github_token=encrypted_token,
                            updated_at=datetime.utcnow(),
                            is_active=True
                        )
                    )
                    await session.commit()
                    
                    # Fetch updated user
                    result = await session.execute(
                        select(User).where(User.github_id == github_user["id"])
                    )
                    return result.scalar_one()
                else:
                    # Create new user
                    new_user = User(
                        github_id=github_user["id"],
                        github_login=github_user["login"],
                        github_name=github_user.get("name"),
                        github_email=github_user.get("email"),
                        avatar_url=github_user.get("avatar_url"),
                        encrypted_github_token=encrypted_token,
                        is_active=True
                    )
                    session.add(new_user)
                    await session.commit()
                    await session.refresh(new_user)
                    return new_user
                    
        except Exception as e:
            logger.error(f"Error creating/updating user: {e}")
            return None
    
    async def create_session(self, user_id: int, user_agent: str = None, ip_address: str = None) -> Optional[Session]:
        """Create a new user session"""
        try:
            session_id = Session.generate_session_id()
            expires_at = Session.generate_expiry_time()
            
            new_session = Session(
                id=session_id,
                user_id=user_id,
                expires_at=expires_at,
                user_agent=user_agent,
                ip_address=ip_address,
                is_active=True
            )
            
            async with async_session_factory() as db_session:
                db_session.add(new_session)
                await db_session.commit()
                await db_session.refresh(new_session)
                return new_session
                
        except Exception as e:
            logger.error(f"Error creating session: {e}")
            return None
    
    async def get_user_by_session(self, session_id: str) -> Optional[User]:
        """Get user by session ID"""
        try:
            async with async_session_factory() as session:
                # Get session and check if it's valid
                result = await session.execute(
                    select(Session).where(
                        Session.id == session_id,
                        Session.is_active == True,
                        Session.expires_at > datetime.utcnow()
                    )
                )
                user_session = result.scalar_one_or_none()
                
                if not user_session:
                    return None
                
                # Update last accessed time
                await session.execute(
                    update(Session)
                    .where(Session.id == session_id)
                    .values(last_accessed=datetime.utcnow())
                )
                
                # Get user
                result = await session.execute(
                    select(User).where(
                        User.id == user_session.user_id,
                        User.is_active == True
                    )
                )
                user = result.scalar_one_or_none()
                await session.commit()
                return user
                
        except Exception as e:
            logger.error(f"Error getting user by session: {e}")
            return None
    
    async def get_user_github_token(self, user_id: int) -> Optional[str]:
        """Get decrypted GitHub token for a user"""
        try:
            async with async_session_factory() as session:
                result = await session.execute(
                    select(User).where(
                        User.id == user_id,
                        User.is_active == True
                    )
                )
                user = result.scalar_one_or_none()
                
                if user and user.encrypted_github_token:
                    return TokenEncryption.decrypt_token(user.encrypted_github_token)
                
                return None
                
        except Exception as e:
            logger.error(f"Error getting user GitHub token: {e}")
            return None
    
    async def invalidate_session(self, session_id: str) -> bool:
        """Invalidate a user session"""
        try:
            async with async_session_factory() as session:
                await session.execute(
                    update(Session)
                    .where(Session.id == session_id)
                    .values(is_active=False)
                )
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error invalidating session: {e}")
            return False
    
    async def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        try:
            async with async_session_factory() as session:
                await session.execute(
                    update(Session)
                    .where(Session.expires_at < datetime.utcnow())
                    .values(is_active=False)
                )
                await session.commit()
                logger.info("Cleaned up expired sessions")
                
        except Exception as e:
            logger.error(f"Error cleaning up expired sessions: {e}")

# Create global auth service instance
auth_service = AuthService() 
