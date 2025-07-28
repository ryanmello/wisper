from fastapi import APIRouter
from services.task_service import task_service
from models.api_models import VerifyConfigurationRequest, VerifyConfigurationResponse, GetToolsResponse, StartWorkflowResponse, StartWorkflowRequest
from utils.logging_config import get_logger
from services.waypoint_service import waypoint_service
from services.tool_service import tool_service
from services.analysis_service import analysis_service
from config.settings import settings

logger = get_logger(__name__)
router = APIRouter()

@router.post("/verify", response_model=VerifyConfigurationResponse)
def verify_configuration(request: VerifyConfigurationRequest):
    return waypoint_service.verify_configuration(request.nodes, request.connections)

@router.get("/tools", response_model=GetToolsResponse)
def get_tools():
    return tool_service.get_tools()

@router.post("/start_workflow", response_model=StartWorkflowResponse)
async def start_workflow(request: StartWorkflowRequest):
    try:
        # Generate a unique task ID for this workflow
        import uuid
        task_id = str(uuid.uuid4())
        
        # Log the request details for debugging
        logger.info("Waypoint start workflow request received:")
        logger.info(f"Task ID: {task_id}")
        logger.info(f"Repository: {request.repository_url}")
        logger.info(f"Nodes: {[node.tool_name for node in request.nodes]}")
        logger.info(f"Connections: {[(conn.source_tool_name, conn.target_tool_name) for conn in request.connections]}")
        
        # Validate workflow configuration first
        response: VerifyConfigurationResponse = waypoint_service.verify_configuration(request.nodes, request.connections)

        if not response.success:
            return StartWorkflowResponse(
                task_id=task_id,
                status="error",
                websocket_url="",
                message=f"Invalid workflow: {response.message}"
            )
        
        # Create enhanced prompt with workflow configuration
        workflow_prompt = f"""
        Please execute the tools in the order in which they are connected. 
        If tool_2 connects to tool_3 and tool_1 connects to tool_2. The order is tool_1, tool_2, tool_3.

        Nodes: {[{"id": node.id, "tool_name": node.tool_name} for node in request.nodes]}
        Connections: {[{"source": conn.source_tool_name, "target": conn.target_tool_name} for conn in request.connections]}
        
        Repository: {request.repository_url}
        """

        await analysis_service.start_analysis(
            task_id = task_id,
            repository_url=request.repository_url,
            prompt=workflow_prompt
        )
        
        # Return response with WebSocket URL for monitoring
        websocket_url = f"ws://{settings.HOST}:{settings.PORT}/ws/waypoint/{task_id}"

        return StartWorkflowResponse(
            task_id=task_id,
            status="workflow_started",
            websocket_url=websocket_url,
            message=f"Waypoint workflow started for {request.repository_url}. Connect to WebSocket for real-time updates."
        )
        
    except Exception as e:
        logger.error(f"Error in start_workflow: {str(e)}")
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
