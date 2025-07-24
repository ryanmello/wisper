import time
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import cipher
from config.settings import settings
from utils.logging_config import setup_logging, get_logger
from services.websocket_service import websocket_service

setup_logging(level=settings.LOG_LEVEL)
logger = get_logger(__name__)

start_time = time.time()

def create_app() -> FastAPI:    
    app = FastAPI()
    
    app.add_middleware(
        CORSMiddleware,
        **settings.get_cors_config()
    )
    
    app.add_event_handler("startup", startup_event)
    app.add_event_handler("shutdown", shutdown_event)
    
    from api import websocket, waypoint, github, veda, auth
    app.include_router(cipher.router, tags=["cipher"])
    app.include_router(websocket.router, tags=["websocket"])
    app.include_router(waypoint.router, tags=["waypoint"])
    app.include_router(github.router, tags=["github"])
    app.include_router(veda.router, tags=["veda"])
    app.include_router(auth.router, tags=["auth"])
    
    return app

async def startup_event():    
    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY is required but not set in environment variables")
    
    # Initialize database
    from config.database import init_database
    await init_database()
    
    # Cleanup expired sessions on startup
    from services.auth_service import auth_service
    await auth_service.cleanup_expired_sessions()
    
async def shutdown_event():
    for task_id in list(websocket_service.active_connections.keys()):
        await websocket_service.disconnect_websocket(task_id)
    logger.info("Shutdown complete")
