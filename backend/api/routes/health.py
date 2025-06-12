"""
Health check endpoints.
"""

from fastapi import APIRouter, HTTPException

from models.api_models import HealthCheck
from core.app import get_analysis_service, get_uptime
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
                # Service is available but tools might not be initialized
                agent_ready = False
        
        # Determine overall status
        if agent_ready and settings.OPENAI_API_KEY:
            status = "healthy"
        elif agent_ready:
            status = "degraded"  # Service works but no AI capabilities
        else:
            status = "unhealthy"
        
        return HealthCheck(
            status=status,
            agent_ready=agent_ready,
            version="2.0.0",  # Updated version for smart analysis
            uptime=get_uptime(),
            tools_available=tools_available
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")

@router.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Whisper API - AI-Powered Repository Analysis",
        "version": "2.0.0",
        "capabilities": [
            "Legacy repository analysis",
            "Smart context-based analysis", 
            "AI-powered tool selection",
            "Real-time progress updates",
            "Multi-tool execution",
            "Vulnerability scanning",
            "Architecture analysis"
        ],
        "endpoints": {
            "health": "/health",
            "docs": "/docs",
            "legacy_tasks": "/api/tasks/",
            "smart_tasks": "/api/smart-tasks/",
            "tools": "/api/tools",
            "websocket_legacy": "/ws/tasks/{task_id}",
            "websocket_smart": "/ws/smart-tasks/{task_id}"
        }
    } 