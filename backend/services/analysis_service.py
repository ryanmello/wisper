import asyncio
from datetime import datetime
from typing import Any, AsyncGenerator, Dict

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from config.settings import settings
from models.api_models import AnalysisResults, OrchestratorUpdate, ProgressInfo, StandardError, StandardToolResponse, StandardWebSocketMessage, ToolInfo
from core.orchestrator import Orchestrator
from utils.logging_config import get_logger
from services.websocket_service import websocket_service
from services.task_service import task_service

logger = get_logger(__name__)

class AnalysisService:    
    def __init__(self):
        self.orchestrator = Orchestrator()
        self.user_prompt = None
        self.start_time = None
        self.total_steps = 12

        self.llm = ChatOpenAI(
            model="gpt-4", 
            temperature=0.1, 
            api_key=settings.OPENAI_API_KEY
        )
    
    async def start_analysis(self, task_id: str, repository_url: str, prompt: str):
        analysis_task = asyncio.create_task(self._run_analysis(task_id, repository_url, prompt))
        task_service.active_tasks[task_id] = analysis_task
        logger.info(f"Created analysis task for {task_id}")

    async def _run_analysis(self, task_id: str, repository_url: str, prompt: str):
        try:
            await websocket_service.send_message(task_id, {
                "type": "progress",
                "task_id": task_id,
                "timestamp": "",
                "progress": {
                    "percentage": 0,
                    "current_step": "Starting AI Analysis",
                    "step_number": 0,
                    "total_steps": 10
                },
                "ai_message": "AI is analyzing your repository based on your prompt..."
            })
            
            logger.info(f"Starting analysis for task {task_id}")
            logger.info(f"Repository: {repository_url}")
            logger.info(f"Prompt: {prompt}")
            
            # on every update from analyze repository
            # send a websocket message to update the client
            # end task if the update type is 'analysis_completed' or 'analysis_error' 
            async for update in self._analyze_repository(task_id, repository_url, prompt):
                await websocket_service.send_message(task_id, update)
                
                if update["type"] in ["analysis_completed", "analysis_error"]:
                    logger.info(f"AI analysis task {task_id} finished with type: {update['type']}")
                    break

        except asyncio.CancelledError:
            logger.info(f"AI analysis task {task_id} was cancelled")
            raise
        except Exception as e:
            logger.error(f"AI analysis task {task_id} failed: {e}")
            raise
        finally:
            if task_id in task_service.active_tasks:
                del task_service.active_tasks[task_id]

    async def _analyze_repository(self, task_id: str, repository_url: str, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Perform repository analysis based on a user prompt.
        
        Args:
            repository_url: URL of repository
            prompt: User prompt
            
        Yields:
            Progress updates and results from the AI orchestration
        """
        logger.info(f"Starting analysis for {repository_url} with context: {prompt[:100]}...")
        
        self.user_prompt = prompt
        self.start_time = datetime.now()
        
        try:
            async for update in self.orchestrator.process_prompt(prompt, repository_url):
                standardized_update = self._standardize_update(task_id, update)
                yield standardized_update.model_dump()
                
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            error_message = StandardWebSocketMessage(
                type="analysis_error",
                task_id=task_id,
                error=StandardError(
                    message=str(e),
                    details="Analysis orchestration failed",
                    error_type="orchestration_error"
                )
            )
            yield error_message.model_dump()

    def _standardize_update(self, task_id: str, orchestrator_update: OrchestratorUpdate) -> StandardWebSocketMessage:
        """Standardized orchestrator updates to WebSocket message format to client consistency."""        
        update_type = orchestrator_update.type
        
        if update_type == "content":
            return self._handle_content_update(task_id, orchestrator_update)
        elif update_type == "status":
            return self._handle_status_update(task_id, orchestrator_update)
        elif update_type == "completed":
            return self._handle_completion_update(task_id, orchestrator_update)
        elif update_type == "error":
            return self._handle_error_update(task_id, orchestrator_update)
        else:
            return self._handle_default_update(task_id, orchestrator_update)

    def _handle_content_update(self, task_id: str, update: OrchestratorUpdate) -> StandardWebSocketMessage:
        """Handle content-type updates."""
        turn = (update.metadata.turn or 0) if update.metadata else 0
        return StandardWebSocketMessage(
            type="progress",
            task_id=task_id,
            progress=ProgressInfo(
                percentage=self._estimate_progress(update),
                current_step="Analysis",
                step_number=turn,
                total_steps=self.total_steps
            ),
            ai_message=update.message
        )

    def _handle_status_update(self, task_id: str, update: OrchestratorUpdate) -> StandardWebSocketMessage:
        """Handle status-type updates, including tool execution states."""
        message = update.message
        metadata = update.metadata
        tool_name = metadata.tool_name if metadata else None
        turn = (metadata.turn or 0) if metadata else 0
        
        # Check if this is a tool-related status update
        if tool_name and self._is_tool_status_message(message):
            return self._create_tool_status_message(task_id, update, tool_name, turn)
        
        # Default progress message for non-tool status updates
        return StandardWebSocketMessage(
            type="progress",
            task_id=task_id,
            progress=ProgressInfo(
                percentage=self._estimate_progress(update),
                current_step=message,
                step_number=turn,
                total_steps=self.total_steps
            )
        )

    def _is_tool_status_message(self, message: str) -> bool:
        """Check if message indicates tool execution status."""
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in ["executing", "completed", "failed"])

    def _create_tool_status_message(self, task_id: str, update: OrchestratorUpdate, tool_name: str, turn: int) -> StandardWebSocketMessage:
        """Create appropriate tool status message based on message content."""
        message = update.message.lower()
        
        if "executing" in message:
            return self._create_tool_started_message(task_id, update, tool_name, turn)
        elif "completed" in message and "failed" not in message:
            return self._create_tool_completed_message(task_id, update, tool_name, turn)
        
        # Fallback to progress message
        return StandardWebSocketMessage(
            type="progress",
            task_id=task_id,
            progress=ProgressInfo(
                percentage=self._estimate_progress(update),
                current_step=update.message,
                step_number=turn,
                total_steps=self.total_steps
            )
        )

    def _create_tool_started_message(self, task_id: str, update: OrchestratorUpdate, tool_name: str, turn: int) -> StandardWebSocketMessage:
        """Create tool started message."""
        return StandardWebSocketMessage(
            type="tool_started",
            task_id=task_id,
            progress=ProgressInfo(
                percentage=self._estimate_progress(update),
                current_step=f"Executing {tool_name.replace('_', ' ').title()}",
                step_number=turn,
                total_steps=self.total_steps
            ),
            tool=ToolInfo(name=tool_name, status="started")
        )

    def _create_tool_completed_message(self, task_id: str, update: OrchestratorUpdate, tool_name: str, turn: int) -> StandardWebSocketMessage:
        """Create tool completed message."""
        mock_result = StandardToolResponse(
            status="success",
            tool_name=tool_name,
            data={},
            summary=f"{tool_name} completed successfully"
        )
        
        return StandardWebSocketMessage(
            type="tool_completed",
            task_id=task_id,
            progress=ProgressInfo(
                percentage=self._estimate_progress(update),
                current_step=f"Completed {tool_name.replace('_', ' ').title()}",
                step_number=turn,
                total_steps=self.total_steps
            ),
            tool=ToolInfo(name=tool_name, status="completed", result=mock_result)
        )

    def _handle_completion_update(self, task_id: str, update: OrchestratorUpdate) -> StandardWebSocketMessage:
        """Handle completion-type updates."""
        execution_summary = update.data.get("tool_results", {}) if update.data else {}
        logger.info(f"Analysis received {len(execution_summary)} tool results: {list(execution_summary.keys())}")
        
        summary = self._generate_summary(execution_summary, self.user_prompt)
        total_turns = (update.metadata.total_turns or 0) if update.metadata else 0
        
        return StandardWebSocketMessage(
            type="analysis_completed",
            task_id=task_id,
            progress=ProgressInfo(
                percentage=100,
                current_step="Analysis Complete",
                step_number=total_turns,
                total_steps=self.total_steps
            ),
            results=AnalysisResults(
                summary=summary,
                execution_info={
                    "user_prompt": self.user_prompt,
                    "total_tools_executed": len(execution_summary),
                    "tools_used": list(execution_summary.keys()),
                    "timestamp": self.start_time.isoformat() if self.start_time else datetime.now().isoformat()
                },
            ),
            ai_message=update.message
        )

    def _handle_error_update(self, task_id: str, update: OrchestratorUpdate) -> StandardWebSocketMessage:
        """Handle error-type updates."""
        error_details = update.data.get("error_details") if update.data else None
        
        return StandardWebSocketMessage(
            type="analysis_error",
            task_id=task_id,
            error=StandardError(
                message=str(update.message),
                details=error_details,
                error_type="orchestration_error"
            )
        )

    def _handle_default_update(self, task_id: str, update: OrchestratorUpdate) -> StandardWebSocketMessage:
        """Handle unknown update types with default progress message."""
        turn = (update.metadata.turn or 0) if update.metadata else 0
        return StandardWebSocketMessage(
            type="progress",
            task_id=task_id,
            progress=ProgressInfo(
                percentage=self._estimate_progress(update),
                current_step="Processing...",
                step_number=turn,
                total_steps=self.total_steps
            ),
            ai_message=update.message
        )
 
    def _estimate_progress(self, update: OrchestratorUpdate) -> int:
        """Estimate progress percentage based on the orchestration state."""
        update_type = update.type
        
        turn = (update.metadata.turn or 0) if update.metadata else 0
        tools_executed = (update.metadata.tools_executed or 0) if update.metadata else 0
        
        base_progress = min((turn * 8) + (tools_executed * 10), 90)
        
        if update_type == "tool_completed":
            base_progress += 5
        elif update_type == "completed":
            return 100
        
        return min(base_progress, 95)
 
    def _generate_summary(self, tool_results: Dict[str, Any], user_prompt: str) -> str:
        """Generate summary of tool results"""

        summary_prompt = f"""
        Based on the following analysis results, generate a comprehensive summary:
        
        User Request: {user_prompt}        
        Tool Results: {tool_results}       
        """

        response = self.llm.invoke([HumanMessage(content=summary_prompt)])
        return response.content
    
analysis_service = AnalysisService()
