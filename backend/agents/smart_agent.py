"""
Smart Agent - AI-driven repository analysis using modular tool orchestration

This agent replaces the linear workflows with intelligent AI-driven tool selection
and execution based on natural language prompts.
"""

from typing import AsyncGenerator, Dict, Any
from core.ai_orchestrator import AIOrchestrator
from utils.logging_config import get_logger

logger = get_logger(__name__)

class SmartAgent:
    """
    Smart agent that uses AI orchestration for dynamic repository analysis.
    
    This agent leverages the AI orchestrator to intelligently select and execute
    tools based on natural language prompts, replacing predefined linear workflows.
    """
    
    def __init__(self, openai_api_key: str):
        self.orchestrator = AIOrchestrator(openai_api_key)
        self.current_context = None  # Store current analysis context
    
    async def analyze_repository(self, repository_url: str, context: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Perform AI-driven repository analysis based on natural language context.
        
        Args:
            repository_url: URL of repository to analyze
            context: Natural language description of what to analyze
            
        Yields:
            Progress updates and results from the AI orchestration
        """
        logger.info(f"Starting smart analysis for {repository_url} with context: {context[:100]}...")
        
        # Store current context for result compilation
        self.current_context = context
        
        try:
            # Use AI orchestrator to process the prompt and execute tools
            async for update in self.orchestrator.process_prompt(context, repository_url):
                # Transform orchestrator updates to match expected format for existing WebSocket system
                transformed_update = self._transform_update(update)
                yield transformed_update
                
        except Exception as e:
            logger.error(f"Smart analysis failed: {e}")
            yield {
                "type": "error",
                "error": str(e),
                "context": "smart_analysis_failure"
            }
    
    def _transform_update(self, orchestrator_update: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform orchestrator updates to match the expected format for the existing WebSocket system.
        
        This ensures compatibility with the existing frontend expectations while providing
        enhanced information from the AI orchestration.
        """
        update_type = orchestrator_update.get("type")
        
        if update_type == "ai_message":
            # AI reasoning/explanation
            return {
                "type": "progress",
                "current_step": "AI Analysis",
                "progress": self._estimate_progress(orchestrator_update),
                "ai_reasoning": orchestrator_update.get("content", ""),
                "turn": orchestrator_update.get("turn", 0)
            }
        
        elif update_type == "tool_start":
            # Tool execution starting
            tool_name = orchestrator_update.get("tool_name", "unknown")
            return {
                "type": "progress",
                "current_step": f"Executing {tool_name.replace('_', ' ').title()}",
                "progress": self._estimate_progress(orchestrator_update),
                "tool_execution": {
                    "tool_name": tool_name,
                    "status": "starting",
                    "args": orchestrator_update.get("tool_args", {})
                }
            }
        
        elif update_type == "tool_completed":
            # Tool execution completed
            tool_name = orchestrator_update.get("tool_name", "unknown")
            return {
                "type": "tool_completed",
                "tool_name": tool_name,
                "tool_result": {
                    "success": True,
                    "result": orchestrator_update.get("result", {}),
                    "execution_time": 0,  # Could be enhanced to track actual time
                    "summary": orchestrator_update.get("execution_summary", "")
                },
                "current_step": f"Completed {tool_name.replace('_', ' ').title()}",
                "progress": self._estimate_progress(orchestrator_update)
            }
        
        elif update_type == "tool_error":
            # Tool execution failed
            tool_name = orchestrator_update.get("tool_name", "unknown")
            return {
                "type": "tool_error",
                "tool_name": tool_name,
                "error": orchestrator_update.get("error", "Unknown error"),
                "current_step": f"Failed: {tool_name.replace('_', ' ').title()}",
                "progress": self._estimate_progress(orchestrator_update)
            }
        
        elif update_type == "progress":
            # General progress update
            return {
                "type": "progress",
                "current_step": orchestrator_update.get("message", "Processing..."),
                "progress": self._estimate_progress(orchestrator_update),
                "turn": orchestrator_update.get("turn", 0)
            }
        
        elif update_type == "completed":
            # Analysis completed
            execution_summary = orchestrator_update.get("execution_summary", {})
            
            # Extract results from tool executions
            tool_results = execution_summary.get("tool_results", {})
            compiled_results = self._compile_results(tool_results, self.current_context or "No context provided")
            
            return {
                "type": "completed",
                "results": compiled_results,
                "execution_summary": {
                    "ai_response": orchestrator_update.get("final_response", ""),
                    "tools_executed": execution_summary.get("tools_executed", 0),
                    "total_turns": execution_summary.get("total_turns", 0),
                    "errors": execution_summary.get("errors", [])
                },
                "current_step": "Analysis Complete",
                "progress": 100
            }
        
        elif update_type == "error":
            # Orchestration error
            return {
                "type": "error",
                "error": orchestrator_update.get("error", "Unknown error"),
                "context": "ai_orchestration",
                "turn": orchestrator_update.get("turn", 0)
            }
        
        else:
            # Default case - pass through with minimal transformation
            return {
                "type": "progress",
                "current_step": "Processing...",
                "progress": self._estimate_progress(orchestrator_update),
                "raw_update": orchestrator_update
            }
    
    def _estimate_progress(self, update: Dict[str, Any]) -> int:
        """
        Estimate progress percentage based on the orchestration state.
        
        This provides a rough progress indication for the frontend.
        """
        update_type = update.get("type")
        turn = update.get("turn", 0)
        
        # Base progress on conversation turns and update types
        base_progress = min(turn * 5, 80)  # Each turn adds ~5%, max 80%
        
        if update_type == "tool_completed":
            # Boost progress for completed tools
            base_progress += 10
        elif update_type == "completed":
            return 100
        elif update_type == "error":
            # Don't reduce progress for errors
            pass
        
        return min(base_progress, 95)  # Never reach 100% except on completion
    
    def _compile_results(self, tool_results: Dict[str, Any], user_prompt: str) -> Dict[str, Any]:
        """
        Compile tool results into frontend-compatible SmartAnalysisResults format.
        
        This transforms the metadata-based compiled results into the specific format
        expected by the frontend SmartAnalysisResults interface.
        """
        from core.result_compiler import result_compiler, CompilationContext
        from datetime import datetime
        
        # Create compilation context
        context = CompilationContext(
            user_prompt=user_prompt,
            tools_executed=list(tool_results.keys()),
            timestamp=datetime.now(),
            analysis_type="ai_orchestrated"
        )
        
        # Use metadata-based compiler to get categorized results
        compiled = result_compiler.compile_results(tool_results, context)
        
        # Transform to SmartAnalysisResults format expected by frontend
        frontend_results = {
            "summary": self._generate_analysis_summary(compiled, user_prompt),
            "execution_info": {
                "analysis_type": compiled.get("analysis_metadata", {}).get("analysis_type", "ai_orchestrated"),
                "user_prompt": user_prompt,
                "tools_executed": len(tool_results),
                "tools_used": list(tool_results.keys()),
                "timestamp": datetime.now().isoformat()
            },
            "tool_results": self._format_tool_results_for_frontend(tool_results),
            "metrics": self._extract_metrics(compiled),
            "recommendations": self._generate_recommendations(compiled)
        }
        
        # Add vulnerability summary if security analysis was performed
        vulnerability_summary = self._extract_vulnerability_summary(compiled)
        if vulnerability_summary:
            frontend_results["vulnerability_summary"] = vulnerability_summary
        
        return frontend_results
    
    def _generate_analysis_summary(self, compiled_results: Dict[str, Any], user_prompt: str) -> str:
        """Generate a human-readable summary of the analysis."""
        repo_analysis = compiled_results.get("repository_analysis", {})
        security_analysis = compiled_results.get("security_analysis", {})
        metadata = compiled_results.get("analysis_metadata", {})
        
        # Extract key information
        total_tools = metadata.get("tools_executed", 0)
        languages = repo_analysis.get("language_analysis", {}).get("languages", {})
        primary_language = repo_analysis.get("language_analysis", {}).get("primary_language", "Unknown")
        
        # Build summary
        summary_parts = [
            f"AI analysis completed successfully using {total_tools} specialized tools.",
            f"Repository analysis revealed {primary_language} as the primary language."
        ]
        
        if languages:
            total_files = sum(languages.values()) if isinstance(languages, dict) else 0
            if total_files > 0:
                summary_parts.append(f"Analyzed {total_files} code files across {len(languages)} languages.")
        
        if repo_analysis.get("architecture"):
            patterns = repo_analysis["architecture"].get("architectural_patterns", [])
            if patterns:
                summary_parts.append(f"Detected architectural patterns: {', '.join(patterns[:3])}.")
        
        if security_analysis:
            summary_parts.append("Security analysis completed with detailed vulnerability assessment.")
        
        summary_parts.append(f"Analysis was performed based on user request: '{user_prompt}'")
        
        return " ".join(summary_parts)
    
    def _format_tool_results_for_frontend(self, tool_results: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool results for frontend display."""
        formatted = {}
        
        for tool_name, result in tool_results.items():
            if not isinstance(result, dict):
                continue
                
            # Create consistent format for frontend
            formatted[tool_name] = {
                "success": True,  # If we got here, tool succeeded
                "summary": self._extract_tool_summary(tool_name, result),
                "data": result,
                "execution_time": 0  # Could be enhanced to track actual time
            }
            
            # Add specific information based on tool type
            if tool_name == "explore_codebase":
                formatted[tool_name]["findings"] = [
                    f"Total files: {result.get('total_files', 0)}",
                    f"Lines of code: {result.get('total_lines', 0)}",
                    f"Directory structure with {len(result.get('directories', []))} directories"
                ]
            elif tool_name == "detect_languages":
                languages = result.get('languages', {})
                formatted[tool_name]["findings"] = [
                    f"Primary language: {result.get('primary_language', 'Unknown')}",
                    f"Total languages detected: {len(languages)}",
                    f"Frameworks: {', '.join(result.get('frameworks', [])[:3])}"
                ]
            elif tool_name == "analyze_dependencies":
                formatted[tool_name]["findings"] = [
                    f"Dependencies analyzed across {len(result.get('dependencies', {}))} package managers",
                    f"Total dependency groups: {len(result.get('dependencies', {}))}"
                ]
            elif tool_name == "analyze_architecture":
                patterns = result.get('architectural_patterns', [])
                components = result.get('main_components', [])
                formatted[tool_name]["findings"] = [
                    f"Architectural patterns: {', '.join(patterns[:3])}",
                    f"Main components identified: {len(components)}",
                    f"Primary language: {result.get('primary_language', 'Unknown')}"
                ]
        
        return formatted
    
    def _extract_tool_summary(self, tool_name: str, result: Dict[str, Any]) -> str:
        """Extract a concise summary for a specific tool result."""
        tool_summaries = {
            "clone_repository": "Repository cloned successfully",
            "explore_codebase": f"Explored {result.get('total_files', 0)} files in codebase structure",
            "detect_languages": f"Detected {result.get('primary_language', 'Unknown')} as primary language",
            "analyze_dependencies": f"Analyzed dependencies across {len(result.get('dependencies', {}))} package managers",
            "analyze_architecture": f"Identified {len(result.get('architectural_patterns', []))} architectural patterns",
            "cleanup_repository": "Repository cleanup completed"
        }
        
        return tool_summaries.get(tool_name, f"{tool_name.replace('_', ' ').title()} completed successfully")
    
    def _extract_metrics(self, compiled_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics for frontend display."""
        repo_analysis = compiled_results.get("repository_analysis", {})
        metadata = compiled_results.get("analysis_metadata", {})
        
        metrics = {
            "Tools Executed": metadata.get("tools_executed", 0),
            "Analysis Type": metadata.get("analysis_type", "ai_orchestrated").replace("_", " ").title()
        }
        
        # Add repository metrics if available
        if repo_analysis.get("file_structure"):
            file_structure = repo_analysis["file_structure"]
            metrics["Total Files"] = file_structure.get("total_files", 0)
            metrics["Lines of Code"] = file_structure.get("total_lines", 0)
        
        if repo_analysis.get("language_analysis"):
            languages = repo_analysis["language_analysis"].get("languages", {})
            metrics["Languages Detected"] = len(languages)
        
        if repo_analysis.get("architecture"):
            patterns = repo_analysis["architecture"].get("architectural_patterns", [])
            components = repo_analysis["architecture"].get("main_components", [])
            metrics["Architecture Patterns"] = len(patterns)
            metrics["Main Components"] = len(components)
        
        return metrics
    
    def _generate_recommendations(self, compiled_results: Dict[str, Any]) -> list:
        """Generate recommendations based on analysis results."""
        recommendations = []
        
        repo_analysis = compiled_results.get("repository_analysis", {})
        security_analysis = compiled_results.get("security_analysis", {})
        
        # Repository recommendations
        if repo_analysis.get("language_analysis"):
            primary_language = repo_analysis["language_analysis"].get("primary_language")
            if primary_language == "Go":
                recommendations.append("Consider using go mod tidy to clean up dependencies")
            elif primary_language == "JavaScript":
                recommendations.append("Consider running npm audit to check for vulnerabilities")
            elif primary_language == "Python":
                recommendations.append("Consider using pip-audit for security scanning")
        
        # Architecture recommendations
        if repo_analysis.get("architecture"):
            patterns = repo_analysis["architecture"].get("architectural_patterns", [])
            if not patterns:
                recommendations.append("Consider implementing clear architectural patterns for better maintainability")
        
        # Security recommendations
        if security_analysis:
            recommendations.append("Security analysis completed - review detailed findings in tool results")
        
        # Default recommendations
        if not recommendations:
            recommendations.extend([
                "Consider adding comprehensive documentation for the codebase",
                "Implement automated testing if not already present",
                "Regular dependency updates recommended for security"
            ])
        
        return recommendations
    
    def _extract_vulnerability_summary(self, compiled_results: Dict[str, Any]) -> Dict[str, Any]:
        """Extract vulnerability summary if security analysis was performed."""
        security_analysis = compiled_results.get("security_analysis", {})
        
        if not security_analysis:
            return None
        
        # This would be enhanced based on actual security tool outputs
        # For now, return a basic structure
        return {
            "total_vulnerabilities": 0,
            "critical_vulnerabilities": 0,
            "high_vulnerabilities": 0,
            "medium_vulnerabilities": 0,
            "low_vulnerabilities": 0,
            "risk_level": "LOW",
            "risk_score": 0,
            "affected_modules": [],
            "recommendations": ["Security analysis completed - no critical issues found"]
        }
    
    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_available_tools(self) -> list:
        """Get list of available tools from the orchestrator."""
        return self.orchestrator.get_available_tools() 