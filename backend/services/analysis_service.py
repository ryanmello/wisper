import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from fastapi import WebSocket
import logging
from agents.codebase_exploration_agent import CodebaseExplorationAgent
from agents.dependency_audit_agent import DependencyAuditAgent
from agents.smart_analysis_agent import SmartAnalysisAgent
from agents.smart_agent import SmartAgent  # New AI-driven agent
from core.tool_registry import get_tool_registry, initialize_tool_registry

logger = logging.getLogger(__name__)

class AnalysisService:
    """Service to manage repository analysis tasks and WebSocket connections."""
    
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        self.smart_agent = SmartAnalysisAgent(openai_api_key=openai_api_key)  # Legacy agent
        self.ai_smart_agent = SmartAgent(openai_api_key=openai_api_key)  # New AI-driven agent
        
        self.active_connections: Dict[str, WebSocket] = {}
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.task_metadata: Dict[str, Dict[str, Any]] = {}
        self._initialized = False
        
    async def initialize(self):
        """Initialize the analysis service and tool registry."""
        if self._initialized:
            return
        
        await initialize_tool_registry()
        
        self._initialized = True
        logger.info("Analysis service initialized successfully")
        
    async def create_task(
        self, 
        repository_url: str, 
        task_type: str = "explore-codebase"
    ) -> str:
        """Create a new analysis task and return task ID."""
        task_id = str(uuid.uuid4())
        
        self.task_metadata[task_id] = {
            "repository_url": repository_url,
            "task_type": task_type
        }
        
        logger.info(f"Created analysis task {task_id} for repository: {repository_url}")
        return task_id
    
    async def create_smart_task(
        self, 
        repository_url: str, 
        context: str,
        intent: Optional[str] = None,
        target_languages: Optional[list] = None,
        scope: str = "full",
        depth: str = "comprehensive",
        additional_params: Optional[Dict] = None
    ) -> str:
        task_id = str(uuid.uuid4())
        logger.info(f"Created smart analysis task {task_id} for repository: {repository_url}")
        logger.info(f"Context: {context[:100]}...")
        return task_id
    
    async def create_ai_task(self, repository_url: str, prompt: str) -> str:
        """Create a new AI-driven analysis task using simplified request (just prompt!)."""
        task_id = str(uuid.uuid4())
        
        self.task_metadata[task_id] = {
            "repository_url": repository_url,
            "prompt": prompt,
            "task_type": "ai_analysis"
        }
        
        logger.info(f"Created AI analysis task {task_id} for repository: {repository_url}")
        logger.info(f"User prompt: {prompt[:100]}...")
        return task_id
    
    async def connect_websocket(self, task_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[task_id] = websocket
        logger.info(f"WebSocket connected for task {task_id}")
    
    async def disconnect_websocket(self, task_id: str):
        if task_id in self.active_connections:
            del self.active_connections[task_id]
        
        if task_id in self.active_tasks:
            task = self.active_tasks[task_id]
            if isinstance(task, asyncio.Task):
                task.cancel()
            del self.active_tasks[task_id]
        
        if task_id in self.task_metadata:
            del self.task_metadata[task_id]
        
        logger.info(f"WebSocket disconnected for task {task_id}")
    
    async def send_message(self, task_id: str, message: Dict[str, Any]):
        """Send a message to the WebSocket client."""
        if task_id in self.active_connections:
            try:
                await self.active_connections[task_id].send_text(json.dumps(message))
            except Exception as e:
                logger.error(f"Failed to send message to {task_id}: {e}")
                await self.disconnect_websocket(task_id)
    
    async def start_analysis(
        self, 
        task_id: str, 
        repository_url: str, 
        task_type: str = "explore-codebase"
    ):        
        try:
            await self._run_analysis(task_id, repository_url, task_type)
        except asyncio.CancelledError:
            logger.info(f"Analysis task {task_id} was cancelled")
            raise
        except Exception as e:
            logger.error(f"Analysis task {task_id} failed: {e}")
            raise
    
    async def start_smart_analysis(
        self, 
        task_id: str, 
        repository_url: str, 
        context: str,
        intent: Optional[str] = None,
        target_languages: Optional[list] = None,
        scope: str = "full",
        depth: str = "comprehensive",
        additional_params: Optional[Dict] = None
    ):
        """Start smart repository analysis with AI-powered tool selection."""
        
        await self.initialize()
        
        try:
            await self._run_ai_smart_analysis(
                task_id, repository_url, context, intent, target_languages, 
                scope, depth, additional_params
            )
        except asyncio.CancelledError:
            logger.info(f"Smart analysis task {task_id} was cancelled")
            raise
        except Exception as e:
            logger.error(f"Smart analysis task {task_id} failed: {e}")
            raise
    
    async def start_ai_analysis(self, task_id: str, repository_url: str, prompt: str):
        """Start simplified AI-driven analysis with just a prompt."""
        
        await self.initialize()
        
        try:
            await self._run_simple_ai_analysis(task_id, repository_url, prompt)
        except asyncio.CancelledError:
            logger.info(f"AI analysis task {task_id} was cancelled")
            raise
        except Exception as e:
            logger.error(f"AI analysis task {task_id} failed: {e}")
            raise
    
    async def _run_analysis(
        self, 
        task_id: str, 
        repository_url: str, 
        task_type: str
    ):
        """Execute repository analysis using the appropriate specialized agent."""
        try:
            await self._send_task_started(task_id, repository_url, task_type)
            
            agent = self._create_agent(task_type)
            
            async for update in agent.analyze_repository(repository_url):
                await self._handle_analysis_update(task_id, update, task_type)
                
                if update["type"] == "completed":
                    break
                    
        except Exception as e:
            await self._handle_analysis_error(task_id, e, "analysis_execution")

    def _create_agent(self, task_type: str):
        agent_map = {
            "dependency-audit": DependencyAuditAgent,
            "explore-codebase": CodebaseExplorationAgent
        }
        
        agent_class = agent_map.get(task_type, CodebaseExplorationAgent)
        return agent_class(self.openai_api_key)

    async def _send_task_started(self, task_id: str, repository_url: str, task_type: str):
        """Send task started message."""
        await self.send_message(task_id, {
            "type": "task.started",
            "task_id": task_id,
            "status": "running",
            "repository_url": repository_url,
            "task_type": task_type
        })

    async def _handle_analysis_update(self, task_id: str, update: Dict[str, Any], task_type: str):
        """Handle different types of analysis updates."""
        if update["type"] == "progress":
            await self._send_progress_update(task_id, update)
        elif update["type"] == "completed":
            await self._send_completion_message(task_id, update["results"], task_type)

    async def _send_progress_update(self, task_id: str, update: Dict[str, Any]):
        """Send progress update message."""
        await self.send_message(task_id, {
            "type": "task.progress",
            "task_id": task_id,
            "current_step": update["current_step"],
            "progress": update["progress"],
            "partial_results": update.get("partial_results", {})
        })

    async def _send_completion_message(self, task_id: str, results: Dict[str, Any], task_type: str):
        """Send task completion message with formatted results."""
        formatted_results = self._format_analysis_results(results, task_type)
        
        await self.send_message(task_id, {
            "type": "task.completed",
            "task_id": task_id,
            "results": {
                "summary": self._generate_summary(results),
                "statistics": self._generate_statistics(results),
                "detailed_results": formatted_results
            }
        })

    def _format_analysis_results(self, results: Dict[str, Any], task_type: str) -> Dict[str, Any]:
        """Format analysis results based on task type."""
        if task_type == "dependency-audit":
            return self._format_dependency_audit_results(results)
        else:
            return self._format_codebase_exploration_results(results)

    def _format_dependency_audit_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format dependency audit specific results."""
        formatted = {
            "dependency_audit": {
                "summary": results.get("summary", "Vulnerability audit completed"),
                "vulnerability_scan": results.get("vulnerability_scan", {}),
                "github_pr": results.get("github_pr", {}),
                "build_validation": results.get("build_validation", {})
            }
        }
        
        if results.get("vulnerability_scan"):
            formatted["vulnerability_scanner"] = results["vulnerability_scan"]
            
        return formatted

    def _format_codebase_exploration_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Format codebase exploration specific results."""
        return {
            "whisper_analysis": {
                "analysis": results.get("architectural_insights", ""),
                "file_structure": results.get("file_structure", {}),
                "language_analysis": results.get("language_analysis", {}),
                "architecture_patterns": results.get("architecture_patterns", []),
                "main_components": results.get("main_components", []),
                "dependencies": results.get("dependencies", {})
            }
        }

    async def _handle_analysis_error(self, task_id: str, error: Exception, context: str):
        """Handle analysis errors with context."""
        error_message = f"Analysis failed during {context}: {str(error)}"
        logger.error(f"Task {task_id} - {error_message}", exc_info=True)
        
        await self.send_message(task_id, {
            "type": "task.error",
            "task_id": task_id,
            "error": error_message,
            "context": context
        })
    
    async def _run_smart_analysis(
        self,
        task_id: str,
        repository_url: str, 
        context: str,
        intent: Optional[str] = None,
        target_languages: Optional[list] = None,
        scope: str = "full",
        depth: str = "comprehensive",
        additional_params: Optional[Dict] = None
    ):
        """Legacy method to run smart analysis using SmartAnalysisAgent."""
        try:
            # Send initial confirmation
            await self.send_message(task_id, {
                "type": "smart_task.started",
                "task_id": task_id,
                "status": "running",
                "repository_url": repository_url,
                "context": context,
                "intent": intent,
                "scope": scope,
                "depth": depth
            })
            
            # Build additional parameters
            if additional_params is None:
                additional_params = {}
            
            if intent:
                additional_params["intent"] = intent
            if target_languages:
                additional_params["target_languages"] = target_languages
            if scope:
                additional_params["scope"] = scope
            if depth:
                additional_params["depth"] = depth
            
            # Run smart analysis with real-time updates
            async for update in self.smart_agent.analyze_repository(
                repository_url, context, additional_params
            ):
                # Forward all updates to the client
                update["task_id"] = task_id
                await self.send_message(task_id, update)
                
                # Break on completion or error
                if update["type"] in ["completed", "error"]:
                    break
        
        except Exception as e:
            logger.error(f"Smart analysis failed for task {task_id}: {e}")
            await self.send_message(task_id, {
                "type": "task.error",
                "task_id": task_id,
                "error": f"Smart analysis failed: {str(e)}"
            })
    
    async def _run_ai_smart_analysis(
        self,
        task_id: str,
        repository_url: str, 
        context: str,
        intent: Optional[str] = None,
        target_languages: Optional[list] = None,
        scope: str = "full",
        depth: str = "comprehensive",
        additional_params: Optional[Dict] = None
    ):
        """New method to run AI-driven smart analysis using SmartAgent with tool orchestration."""
        try:
            # Send initial confirmation
            await self.send_message(task_id, {
                "type": "ai_smart_task.started",
                "task_id": task_id,
                "status": "running",
                "repository_url": repository_url,
                "context": context,
                "intent": intent,
                "scope": scope,
                "depth": depth,
                "analysis_mode": "ai_orchestrated"
            })
            
            # Run AI-driven smart analysis with real-time updates
            async for update in self.ai_smart_agent.analyze_repository(repository_url, context):
                # Forward all updates to the client with task_id
                update["task_id"] = task_id
                await self.send_message(task_id, update)
                
                # Break on completion or error
                if update["type"] in ["completed", "error"]:
                    break
        
        except Exception as e:
            logger.error(f"AI-driven smart analysis failed for task {task_id}: {e}")
            await self.send_message(task_id, {
                "type": "task.error",
                "task_id": task_id,
                "error": f"AI-driven smart analysis failed: {str(e)}",
                "context": "ai_smart_analysis"
            })
    
    async def _run_simple_ai_analysis(self, task_id: str, repository_url: str, prompt: str):
        """Run simplified AI-driven analysis using just a user prompt."""
        try:
            # Send initial confirmation with simplified format
            await self.send_message(task_id, {
                "type": "ai_analysis.started",
                "task_id": task_id,
                "status": "running",
                "repository_url": repository_url,
                "prompt": prompt,
                "message": "AI is analyzing your repository based on your prompt..."
            })
            
            logger.info(f"Starting simplified AI analysis for task {task_id}")
            logger.info(f"Repository: {repository_url}")
            logger.info(f"User prompt: {prompt}")
            
            # Run AI-driven analysis with the prompt as context
            async for update in self.ai_smart_agent.analyze_repository(repository_url, prompt):
                # Forward all updates to the client with task_id
                update["task_id"] = task_id
                await self.send_message(task_id, update)
                
                # Break on completion or error
                if update["type"] in ["completed", "error"]:
                    logger.info(f"AI analysis task {task_id} finished with type: {update['type']}")
                    break
        
        except Exception as e:
            logger.error(f"Simplified AI analysis failed for task {task_id}: {e}")
            await self.send_message(task_id, {
                "type": "task.error",
                "task_id": task_id,
                "error": f"AI analysis failed: {str(e)}",
                "context": "simple_ai_analysis"
            })
    
    def _generate_summary(self, results: Dict[str, Any]) -> str:
        """Generate a summary from the analysis results."""
        lang_analysis = results.get("language_analysis", {})
        file_structure = results.get("file_structure", {})
        patterns = results.get("architecture_patterns", [])
        
        primary_lang = lang_analysis.get("primary_language", "Unknown")
        total_files = file_structure.get("total_files", 0)
        total_lines = file_structure.get("total_lines", 0)
        
        summary = f"Analysis complete for {primary_lang} project with {total_files} files ({total_lines:,} lines of code)"
        
        if patterns:
            summary += f". Detected architectural patterns: {', '.join(patterns[:3])}"
        
        return summary
    
    def _generate_statistics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate statistics from the analysis results."""
        lang_analysis = results.get("language_analysis", {})
        file_structure = results.get("file_structure", {})
        components = results.get("main_components", [])
        patterns = results.get("architecture_patterns", [])
        dependencies = results.get("dependencies", {})
        
        return {
            "Files Analyzed": file_structure.get("total_files", 0),
            "Lines of Code": file_structure.get("total_lines", 0),
            "Languages Detected": len(lang_analysis.get("languages", {})),
            "Main Components": len(components),
            "Architecture Patterns": len(patterns),
            "Dependency Groups": len(dependencies)
        }
    
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get the status of a specific task."""
        if task_id in self.active_connections:
            return {"task_id": task_id, "status": "running"}
        elif task_id in self.active_tasks:
            return {"task_id": task_id, "status": "processing"}
        else:
            return {"task_id": task_id, "status": "not_found"}
    
    def get_active_connections_info(self) -> Dict[str, Any]:
        """Get information about active connections."""
        return {
            "active_connections": len(self.active_connections),
            "active_tasks": len(self.active_tasks),
            "connection_ids": list(self.active_connections.keys())
        }
    
    async def get_tool_registry_info(self) -> Dict[str, Any]:
        """Get information about the tool registry."""
        await self.initialize()
        
        try:
            registry = await get_tool_registry()
            return registry.get_registry_info()
        except Exception as e:
            logger.error(f"Failed to get tool registry info: {e}")
            return {
                "total_tools": 0,
                "healthy_tools": 0,
                "capabilities": [],
                "supported_languages": [],
                "tools": {},
                "error": str(e)
            } 
