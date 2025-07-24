import os
from typing import List, Optional
from dotenv import load_dotenv
from utils.logging_config import get_logger

load_dotenv()

logger = get_logger(__name__)

class Settings:
    PROJECT_NAME: str = "cipher"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    BACKEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:8000")
    ALLOWED_ORIGINS: List[str] = [FRONTEND_URL, "http://localhost:3000"]
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    TEMP_DIR_PREFIX: str = f"{PROJECT_NAME}_"
    
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
    GITHUB_API_URL: str = os.getenv("GITHUB_API_URL", "https://api.github.com")
    GITHUB_DRY_RUN: bool = os.getenv("GITHUB_DRY_RUN", "false").lower() == "true"
    
    # GitHub OAuth settings
    GITHUB_CLIENT_ID: Optional[str] = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET: Optional[str] = os.getenv("GITHUB_CLIENT_SECRET")
    
    # Database settings
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app.db")
    
    # Encryption settings
    ENCRYPTION_KEY: Optional[str] = os.getenv("ENCRYPTION_KEY")
    
    @classmethod
    def get_cors_config(cls) -> dict:
        """Get CORS configuration dictionary."""
        return {
            "allow_origins": cls.ALLOWED_ORIGINS,
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }

settings = Settings() 
