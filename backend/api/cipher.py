from fastapi import APIRouter, HTTPException
from models.api_models import CipherRequest, CipherResponse
from services.analysis_service import analysis_service
from config.settings import settings
from utils.logging_config import get_logger
import uuid

logger = get_logger(__name__)
router = APIRouter()

@router.post("/cipher", response_model=CipherResponse)
async def analyze_repository(request: CipherRequest):
    """
    Start AI-driven repository analysis based on a natural language prompt
    """
    try:
        # Generate a unique task ID for this analysis
        task_id = str(uuid.uuid4())
        
        # Log the request details for debugging
        logger.info("Cipher analyze repository request received:")
        logger.info(f"Task ID: {task_id}")
        logger.info(f"Repository: {request.repository_url}")
        logger.info(f"Prompt: {request.prompt}")
        
        # Start analysis task immediately
        await analysis_service.start_analysis(
            task_id=task_id,
            repository_url=request.repository_url,
            prompt=request.prompt
        )
        
        # Return response with WebSocket URL for monitoring
        websocket_url = f"ws://{settings.HOST}:{settings.PORT}/ws/cipher/{task_id}"
        
        return CipherResponse(
            task_id=task_id,
            status="analysis_started",
            websocket_url=websocket_url,
            message=f"AI analysis started for {request.repository_url}. Connect to WebSocket for real-time updates."
        )
        
    except Exception as e:
        logger.error(f"Error in analyze_repository: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
