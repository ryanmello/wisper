from typing import Dict, Any
import json
from fastapi import WebSocket
from utils.logging_config import get_logger
from services.task_service import task_service

logger = get_logger(__name__)

class WebsocketService:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}

    # connect
    async def connect_websocket(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[task_id] = websocket
        logger.info(f"WebSocket connected for task {task_id}")
    
    # disconnect and cancel running tasks
    async def disconnect_websocket(self, task_id: str):
        # Make this method idempotent to handle multiple calls
        websocket = self.active_connections.get(task_id)
        if websocket:
            try:
                await websocket.close()
                logger.debug(f"WebSocket closed for task {task_id}")
            except Exception as e:
                logger.warning(f"Error closing WebSocket for task {task_id}: {e}")
            
            # Remove from active connections after closing
            self.active_connections.pop(task_id, None)
        
        # Only try to cancel if task is still active
        if task_id in task_service.active_tasks:
            cancelled = task_service.cancel_task(task_id)
            if cancelled:
                logger.info(f"Cancelled analysis task {task_id} during disconnect")
        
        logger.info(f"WebSocket disconnected for task {task_id}")

    # send message to a specific websocket connection
    async def send_message(self, task_id: str, message: Dict[str, Any]):
        websocket = self.active_connections.get(task_id)
        if websocket:
            try:
                # Always ensure timestamp is present and valid
                from datetime import datetime
                message["timestamp"] = datetime.now().isoformat()
                
                # Ensure task_id is always present
                if "task_id" not in message:
                    message["task_id"] = task_id
                
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {task_id}: {e}")
                # If we can't send, the connection is likely closed - remove it
                self.active_connections.pop(task_id, None)
                logger.debug(f"Removed disconnected WebSocket for task {task_id}")
    
    # Helper method for sending error messages
    async def send_error(self, task_id: str, error: str, context: str = None):
        """Send a standardized error message"""
        message = {
            "type": "task.error",
            "error": error
        }
        if context:
            message["context"] = context
        
        await self.send_message(task_id, message)
    
    # Helper method for sending progress messages
    async def send_progress(self, task_id: str, percentage: int, current_step: str, 
                           step_number: int = 0, total_steps: int = 10, ai_message: str = None):
        """Send a standardized progress message"""
        message = {
            "type": "progress",
            "progress": {
                "percentage": percentage,
                "current_step": current_step,
                "step_number": step_number,
                "total_steps": total_steps
            }
        }
        if ai_message:
            message["ai_message"] = ai_message
        
        await self.send_message(task_id, message)

websocket_service = WebsocketService()
