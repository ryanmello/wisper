"""
FastAPI application factory and initialization.
"""

import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config.settings import settings
from services.analysis_service import AnalysisService
from utils.logging_config import setup_logging, get_logger

# Setup logging
setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)

# Global variables
analysis_service: AnalysisService = None
start_time = time.time()

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title=settings.API_TITLE,
        version=settings.API_VERSION,
        description=settings.API_DESCRIPTION
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        **settings.get_cors_config()
    )
    
    # Add startup and shutdown events
    app.add_event_handler("startup", startup_event)
    app.add_event_handler("shutdown", shutdown_event)
    
    # Register routes
    from api.routes import health, tasks, websocket
    app.include_router(health.router, tags=["health"])
    app.include_router(tasks.router, prefix="/api", tags=["tasks"])
    app.include_router(websocket.router, tags=["websocket"])
    
    return app

async def startup_event():
    """Initialize services on startup."""
    global analysis_service
    
    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not found in environment variables")
        openai_api_key = "dummy-key"  # For testing without real API
    else:
        openai_api_key = settings.OPENAI_API_KEY
    
    analysis_service = AnalysisService(openai_api_key=openai_api_key)
    logger.info("Analysis service initialized successfully")

async def shutdown_event():
    """Clean up resources on shutdown."""
    global analysis_service
    if analysis_service:
        # Cleanup any active connections
        for task_id in list(analysis_service.active_connections.keys()):
            await analysis_service.disconnect_websocket(task_id)
        logger.info("Analysis service shutdown complete")

def get_analysis_service() -> AnalysisService:
    """Get the global analysis service instance."""
    return analysis_service

def get_uptime() -> float:
    """Get application uptime in seconds."""
    return time.time() - start_time 