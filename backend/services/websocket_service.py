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
                # Ensure message has required fields for StandardWebSocketMessage
                if "timestamp" not in message or not message["timestamp"]:
                    from datetime import datetime
                    message["timestamp"] = datetime.now().isoformat()
                
                await self.active_connections[task_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {task_id}: {e}")
                await self.disconnect_websocket(task_id)

websocket_service = WebsocketService()
