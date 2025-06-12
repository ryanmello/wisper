"""
WebSocket endpoints for real-time analysis updates.
"""

import asyncio
import json
import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from core.app import get_analysis_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.websocket("/ws/tasks/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time analysis updates (legacy)."""
    analysis_service = get_analysis_service()
    if analysis_service is None:
        await websocket.close(code=1011, reason="Analysis service not available")
        return
    
    try:
        await analysis_service.connect_websocket(task_id, websocket)
        
        # Wait for task parameters from client
        data = await websocket.receive_text()
        task_params = json.loads(data)
        
        repository_url = task_params.get("repository_url")
        task_type = task_params.get("task_type", "explore-codebase")
        
        if not repository_url:
            await analysis_service.send_message(task_id, {
                "type": "task.error",
                "task_id": task_id,
                "error": "Repository URL is required"
            })
            return
        
        # Start the legacy analysis as a background task and track it
        analysis_task = asyncio.create_task(
            analysis_service.start_analysis(task_id, repository_url, task_type)
        )
        
        # Store the task in the analysis service for cancellation
        analysis_service.active_tasks[task_id] = analysis_task
        
        # Keep the WebSocket connection alive to receive messages
        while True:
            try:
                # Wait for any additional messages from client (optional)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                # Handle any additional client messages if needed
                logger.debug(f"Received message from client {task_id}: {message}")
            except asyncio.TimeoutError:
                # Check if connection is still alive
                if task_id not in analysis_service.active_connections:
                    break
                continue
            except WebSocketDisconnect:
                logger.info(f"Client {task_id} disconnected")
                break
    
    except WebSocketDisconnect:
        logger.info(f"Client {task_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error for {task_id}: {str(e)}")
        try:
            await analysis_service.send_message(task_id, {
                "type": "task.error",
                "task_id": task_id,
                "error": str(e)
            })
        except:
            pass
    finally:
        # Cancel the analysis task if it's still running
        if task_id in analysis_service.active_tasks:
            analysis_task = analysis_service.active_tasks[task_id] 
            if not analysis_task.done():
                analysis_task.cancel()
            del analysis_service.active_tasks[task_id]
            
        await analysis_service.disconnect_websocket(task_id)

@router.websocket("/ws/smart-tasks/{task_id}")
async def smart_websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time smart analysis updates."""
    analysis_service = get_analysis_service()
    if analysis_service is None:
        await websocket.close(code=1011, reason="Analysis service not available")
        return
    
    try:
        await analysis_service.connect_websocket(task_id, websocket)
        
        # Wait for task parameters from client
        data = await websocket.receive_text()
        task_params = json.loads(data)
        
        repository_url = task_params.get("repository_url")
        context = task_params.get("context", "explore codebase")
        intent = task_params.get("intent")
        target_languages = task_params.get("target_languages")
        scope = task_params.get("scope", "full")
        depth = task_params.get("depth", "comprehensive")
        additional_params = task_params.get("additional_params")
        
        if not repository_url:
            await analysis_service.send_message(task_id, {
                "type": "task.error",
                "task_id": task_id,
                "error": "Repository URL is required"
            })
            return
        
        # Start the smart analysis as a background task and track it
        analysis_task = asyncio.create_task(
            analysis_service.start_smart_analysis(
                task_id, repository_url, context, intent, target_languages,
                scope, depth, additional_params
            )
        )
        
        # Store the task in the analysis service for cancellation
        analysis_service.active_tasks[task_id] = analysis_task
        
        # Keep the WebSocket connection alive to receive messages
        while True:
            try:
                # Wait for any additional messages from client (optional)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                # Handle any additional client messages if needed
                logger.debug(f"Received message from smart client {task_id}: {message}")
                
                # Parse message for potential commands
                try:
                    msg_data = json.loads(message)
                    msg_type = msg_data.get("type")
                    
                    if msg_type == "cancel":
                        # Handle cancellation request
                        if task_id in analysis_service.active_tasks:
                            analysis_service.active_tasks[task_id].cancel()
                            await analysis_service.send_message(task_id, {
                                "type": "task.cancelled",
                                "task_id": task_id,
                                "message": "Analysis cancelled by user"
                            })
                        break
                    
                except json.JSONDecodeError:
                    # Not a JSON message, ignore
                    pass
                
            except asyncio.TimeoutError:
                # Check if connection is still alive
                if task_id not in analysis_service.active_connections:
                    break
                continue
            except WebSocketDisconnect:
                logger.info(f"Smart client {task_id} disconnected")
                break
    
    except WebSocketDisconnect:
        logger.info(f"Smart client {task_id} disconnected")
    except Exception as e:
        logger.error(f"Smart WebSocket error for {task_id}: {str(e)}")
        try:
            await analysis_service.send_message(task_id, {
                "type": "task.error",
                "task_id": task_id,
                "error": str(e)
            })
        except:
            pass
    finally:
        # Cancel the analysis task if it's still running
        if task_id in analysis_service.active_tasks:
            analysis_task = analysis_service.active_tasks[task_id] 
            if not analysis_task.done():
                analysis_task.cancel()
            del analysis_service.active_tasks[task_id]
            
        await analysis_service.disconnect_websocket(task_id) 