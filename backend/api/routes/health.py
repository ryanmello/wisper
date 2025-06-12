"""
Health check endpoints.
"""

from fastapi import APIRouter, HTTPException

from models.api_models import HealthCheck
from core.app import get_analysis_service
from config.settings import settings

router = APIRouter()

@router.get("/health", response_model=HealthCheck)
async def health_check():
    """Check the health status of the API and its components."""
    try:
        analysis_service = get_analysis_service()
        
        # Check if analysis service is available
        agent_ready = analysis_service is not None
        
        # Get tool registry information if available
        tools_available = []
        if analysis_service:
            try:
                await analysis_service.initialize()
                registry_info = await analysis_service.get_tool_registry_info()
                tools_available = list(registry_info.get("tools", {}).keys())
            except Exception as e:
                agent_ready = False
        
        if agent_ready and settings.OPENAI_API_KEY:
            status = "healthy"
        elif agent_ready:
            status = "degraded"
        else:
            status = "unhealthy"
        
        return HealthCheck(
            status=status,
            agent_ready=agent_ready,
            version="1.0.0"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")
