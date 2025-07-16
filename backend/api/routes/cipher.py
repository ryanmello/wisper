from fastapi import APIRouter
from models.api_models import AIAnalysisRequest, AIAnalysisResponse
from config.settings import settings
from utils.logging_config import get_logger
from services.task_service import task_service

logger = get_logger(__name__)
router = APIRouter()

@router.post("/cipher/", response_model=AIAnalysisResponse)
async def create_task(request: AIAnalysisRequest):
    task_id = await task_service.create_task(
        repository_url=request.repository_url,
        prompt=request.prompt
    )
    
    websocket_url = f"ws://{settings.HOST}:{settings.PORT}/ws/cipher/{task_id}"
    
    return AIAnalysisResponse(
        task_id=task_id,
        status="created",
        websocket_url=websocket_url,
        message=f"Task created: {task_id}:{request.repository_url}"
    )
