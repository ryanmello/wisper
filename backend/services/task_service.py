import asyncio
from typing import Any, Dict
import uuid
from utils.logging_config import get_logger

logger = get_logger(__name__)

class TaskService():
    def __init__(self):
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_metadata: Dict[str, Dict[str, Any]] = {}

    async def create_task(self, repository_url: str, prompt: str) -> str:
        task_id = str(uuid.uuid4())
        
        self.task_metadata[task_id] = {
            "repository_url": repository_url,
            "prompt": prompt,
        }
        
        logger.info(f"Created AI analysis task {task_id} for repository: {repository_url}")
        logger.info(f"User prompt: {prompt[:100]}...")
        return task_id
    
    def cancel_task(self, task_id: str) -> bool:
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if isinstance(task, asyncio.Task) and not task.done():
                task.cancel()
                logger.info(f"Cancelled analysis task {task_id}")
            del self.active_tasks[task_id]
            return True
        return False
    
task_service = TaskService()
