"""
Configuration settings for Whisper backend application.
"""

import os
import logging
from typing import List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logger = logging.getLogger(__name__)

class Settings:
    """Application settings loaded from environment variables."""
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", "8000"))
    RELOAD: bool = os.getenv("RELOAD", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "info")
    
    # API Configuration
    API_TITLE: str = "Whisper API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "AI-powered repository analysis and exploration API"
    
    # CORS Configuration
    FRONTEND_URL: str = os.getenv("FRONTEND_URL", "http://localhost:3000")
    ALLOWED_ORIGINS: List[str] = [
        FRONTEND_URL,
        "http://localhost:3000"
    ]
    
    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    
    # Application Settings
    TEMP_DIR_PREFIX: str = "whisper_analysis_"
    MAX_CONCURRENT_ANALYSES: int = int(os.getenv("MAX_CONCURRENT_ANALYSES", "5"))
    
    GITHUB_TOKEN: Optional[str] = os.getenv("GITHUB_TOKEN")
    GITHUB_DRY_RUN: bool = os.getenv("GITHUB_DRY_RUN", "false").lower() == "true"
    
    @classmethod
    def validate_required_settings(cls) -> bool:
        """Validate that required settings are present."""
        if not cls.OPENAI_API_KEY:
            return False
        return True
    
    @classmethod
    def get_cors_config(cls) -> dict:
        """Get CORS configuration dictionary."""
        return {
            "allow_origins": cls.ALLOWED_ORIGINS,
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"],
        }

# Global settings instance
settings = Settings() 