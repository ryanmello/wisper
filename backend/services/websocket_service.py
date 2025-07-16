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
        if task_id in self.active_connections:
            del self.active_connections[task_id]
        
        cancelled = task_service.cancel_task(task_id)
        if cancelled:
            logger.info(f"Cancelled analysis task {task_id} during disconnect")
        
        logger.info(f"WebSocket disconnected for task {task_id}")

    # send message to a specific websocket connection
    async def send_message(self, task_id: str, message: Dict[str, Any]):
        if task_id in self.active_connections:
            try:
                # Always ensure timestamp is present and valid
                from datetime import datetime
                message["timestamp"] = datetime.now().isoformat()
                
                # Ensure task_id is always present
                if "task_id" not in message:
                    message["task_id"] = task_id
                
                await self.active_connections[task_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {task_id}: {e}")
                await self.disconnect_websocket(task_id)
    
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
