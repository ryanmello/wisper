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
async def cipher_websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for Cipher analysis tasks"""
    try:
        await websocket_service.connect_websocket(task_id, websocket)
        logger.info(f"Cipher client connected: {task_id}")
        
        # Keep connection alive until task completes or client disconnects
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                logger.debug(f"Received message from Cipher client {task_id}: {message}")
                
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
                # Check if task is still active
                if task_id not in task_service.active_tasks:
                    logger.info(f"Cipher analysis completed for task: {task_id}")
                    break
                if task_id not in websocket_service.active_connections:
                    break
                continue
            except WebSocketDisconnect:
                logger.info(f"Cipher client {task_id} disconnected")
                break
    
    except WebSocketDisconnect:
        logger.info(f"Cipher client {task_id} disconnected")
    except Exception as e:
        logger.error(f"Cipher WebSocket error for {task_id}: {str(e)}")
        try:
            await websocket_service.send_error(task_id, str(e), "cipher_websocket")
        except:
            pass
    finally:
        await websocket_service.disconnect_websocket(task_id)

@router.websocket("/ws/veda/{task_id}")
async def veda_websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for Veda analysis tasks"""
    try:
        await websocket_service.connect_websocket(task_id, websocket)
        logger.info(f"Veda client connected: {task_id}")
        
        # Keep connection alive until task completes or client disconnects
        
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                logger.debug(f"Received message from Veda client {task_id}: {message}")
                
                try:
                    msg_data = json.loads(message)
                    msg_type = msg_data.get("type")
                    
                    if msg_type == "cancel":
                        cancelled = task_service.cancel_task(task_id)
                        if cancelled:
                            await websocket_service.send_message(task_id, {
                                "type": "task.cancelled",
                                "message": "Veda analysis cancelled by user"
                            })
                        break
                    
                except json.JSONDecodeError:
                    pass
                
            except asyncio.TimeoutError:
                # Check if task is still active
                if task_id not in task_service.active_tasks:
                    logger.info(f"Veda analysis completed for task: {task_id}")
                    break
                if task_id not in websocket_service.active_connections:
                    break
                continue
            except WebSocketDisconnect:
                logger.info(f"Veda client {task_id} disconnected")
                break
    
    except WebSocketDisconnect:
        logger.info(f"Veda client {task_id} disconnected")
    except Exception as e:
        logger.error(f"Veda WebSocket error for {task_id}: {str(e)}")
        try:
            await websocket_service.send_error(task_id, str(e), "veda_websocket")
        except:
            pass
    finally:
        await websocket_service.disconnect_websocket(task_id)

@router.websocket("/ws/waypoint/{task_id}")
async def waypoint_websocket_endpoint(websocket: WebSocket, task_id: str):
    """"""
    try:
        await websocket_service.connect_websocket(task_id, websocket)
        logger.info(f"Waypoint client connected: {task_id}")
        
        # Keep connection alive until task completes or client disconnects
        while True:
            try:
                message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                logger.debug(f"Received message from Waypoint client {task_id}: {message}")
                
                try:
                    msg_data = json.loads(message)
                    msg_type = msg_data.get("type")
                    
                    if msg_type == "cancel":
                        cancelled = task_service.cancel_task(task_id)
                        if cancelled:
                            await websocket_service.send_message(task_id, {
                                "type": "task.cancelled",
                                "message": "Waypoint cancelled by user"
                            })
                        break
                    
                except json.JSONDecodeError:
                    pass
                
            except asyncio.TimeoutError:
                # Check if task is still active
                if task_id not in task_service.active_tasks:
                    logger.info(f"Waypoint completed for task: {task_id}")
                    break
                if task_id not in websocket_service.active_connections:
                    break
                continue
            except WebSocketDisconnect:
                logger.info(f"Waypoint client {task_id} disconnected")
                break
    
    except WebSocketDisconnect:
        logger.info(f"Waypoint client {task_id} disconnected")
    except Exception as e:
        logger.error(f"Waypoint WebSocket error for {task_id}: {str(e)}")
        try:
            await websocket_service.send_error(task_id, str(e), "waypoint_websocket")
        except:
            pass
    finally:
        await websocket_service.disconnect_websocket(task_id)
