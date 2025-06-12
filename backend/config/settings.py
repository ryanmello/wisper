import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

class Settings:
    PROJECT_NAME: str = "whisper"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    ALLOWED_ORIGINS: List[str] = [
        FRONTEND_URL,
        "http://localhost:3000"
    ]
    
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    TEMP_DIR_PREFIX: str = f"{PROJECT_NAME}_"
    
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
    GITHUB_DRY_RUN: bool = os.getenv("GITHUB_DRY_RUN", "false").lower() == "true"
    
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