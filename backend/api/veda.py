from services import waypoint_service
from models.api_models import VerifyConfigurationRequest

def get_pull_requests(request: VerifyConfigurationRequest):
    return waypoint_service.verify_configuration(request.nodes, request.connections)
