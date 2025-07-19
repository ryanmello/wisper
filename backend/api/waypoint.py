from fastapi import APIRouter
from models.api_models import VerifyConfigurationRequest, VerifyConfigurationResponse, GetToolsResponse
from utils.logging_config import get_logger
from services.waypoint_service import waypoint_service
from services.tool_service import tool_service

logger = get_logger(__name__)
router = APIRouter()

@router.post("/verify/", response_model=VerifyConfigurationResponse)
def verify_configuration(request: VerifyConfigurationRequest):
    return waypoint_service.verify_configuration(request.nodes, request.connections)

@router.get("/tools/", response_model=GetToolsResponse)
def get_tools():
    return tool_service.get_tools()
