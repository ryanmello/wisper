from fastapi import APIRouter
from models.api_models import VerifyConfigurationRequest, VerifyConfigurationResponse
from utils.logging_config import get_logger
from services.waypoint_service import waypoint_service

logger = get_logger(__name__)
router = APIRouter()

@router.post("/verify/", response_model=VerifyConfigurationResponse)
def verify_configuration(request: VerifyConfigurationRequest):
    return waypoint_service.verify_configuration(request.nodes, request.connections)
