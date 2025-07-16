import asyncio
import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from utils.logging_config import get_logger
from services.websocket_service import websocket_service
from services.analysis_service import analysis_service
from services.task_service import task_service

logger = get_logger(__name__)
router = APIRouter()

@router.websocket("/ws/cipher/{task_id}")
async def ai_websocket_endpoint(websocket: WebSocket, task_id: str):
    try:
        await websocket_service.connect_websocket(task_id, websocket)
        
        data = await websocket.receive_text()
        task_params = json.loads(data)
        
        repository_url = task_params.get("repository_url")
        prompt = task_params.get("prompt")
        
        if not repository_url:
            await websocket_service.send_error(task_id, "Repository URL is required")
            return
            
        if not prompt:
            await websocket_service.send_error(task_id, "Prompt is required")
            return
        
        logger.info(f"Starting task: {task_id}")
        logger.info(f"Repository: {repository_url}")
        logger.info(f"User prompt: {prompt[:100]}...")
        
        await analysis_service.start_analysis(task_id, repository_url, prompt)
        
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                logger.debug(f"Received message from AI client {task_id}: {message}")
                
                try:
                    msg_data = json.loads(message)
                    msg_type = msg_data.get("type")
                    
                    if msg_type == "cancel":
                        cancelled = task_service.cancel_task(task_id)
                        if cancelled:
                            await websocket_service.send_message(task_id, {
                                "type": "task.cancelled",
                                "message": "AI analysis cancelled by user"
                            })
                        break
                    
                except json.JSONDecodeError:
                    pass
                
            except asyncio.TimeoutError:
                if task_id not in task_service.active_tasks:
                    logger.info(f"Analysis completed for task: {task_id}")
                    break
                if task_id not in websocket_service.active_connections:
                    break
                continue
            except WebSocketDisconnect:
                logger.info(f"AI client {task_id} disconnected")
                break
    
    except WebSocketDisconnect:
        logger.info(f"AI client {task_id} disconnected")
    except Exception as e:
        logger.error(f"AI WebSocket error for {task_id}: {str(e)}")
        try:
            await websocket_service.send_error(task_id, str(e), "ai_websocket")
        except:
            pass
    finally:
        await websocket_service.disconnect_websocket(task_id)
