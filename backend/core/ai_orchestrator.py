"""
AI Orchestrator - AI-driven tool orchestration using bind_tools

This module provides the core AI orchestration engine that uses GPT-4 to 
dynamically select and execute appropriate tools based on natural language prompts.
"""

import json
import asyncio
from typing import AsyncGenerator, Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
import time

from tools import ALL_TOOLS
from utils.logging_config import get_logger

logger = get_logger(__name__)

class AIOrchestrator:
    """AI-driven tool orchestration using bind_tools"""
    
    def __init__(self, openai_api_key: str):
        # Bind tools directly to the LLM
        self.llm = ChatOpenAI(
            model="gpt-4", 
            temperature=0, 
            api_key=openai_api_key
        ).bind_tools(ALL_TOOLS)
        
        self.tools_map = {tool.name: tool for tool in ALL_TOOLS}
        self.system_prompt = self._create_system_prompt()
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt that explains available tools and orchestration guidelines."""
        
        # Generate tool descriptions dynamically
        tool_descriptions = []
        for tool in ALL_TOOLS:
            tool_descriptions.append(f"- {tool.name}: {tool.description}")
        
        tools_list = "\n".join(tool_descriptions)
        
        return f"""You are an expert code analysis orchestrator with access to specialized tools for repository analysis.

Available tools:
{tools_list}

Your Role:
You help users analyze code repositories by intelligently selecting and executing the appropriate tools based on their requests. Read the tool descriptions carefully to understand what each tool does, what it requires, and what it provides.

Key Principles:
- Understand the user's intent and select tools that will fulfill their request
- Read tool descriptions to understand dependencies and prerequisites  
- Work systematically - some tools may need outputs from other tools
- Provide clear progress updates as you work
- Handle errors gracefully and continue with other tools when possible
- Be concise but informative in your explanations

You have full autonomy to decide which tools to use, in what order, and how to combine their results to best serve the user's request."""

    async def process_prompt(self, user_prompt: str, repository_url: str) -> AsyncGenerator[Dict[str, Any], None]:
        """Process user prompt and orchestrate tools using bound LLM"""
        
        logger.info(f"Processing prompt: {user_prompt[:100]}... for repository: {repository_url}")
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
User Request: {user_prompt}
Repository URL: {repository_url}

Please analyze this request and use the appropriate tools to fulfill it. 
Work step by step, explain your approach, and provide progress updates.
""")
        ]
        
        # Track execution state
        execution_state = {
            "repository_path": None,
            "tool_results": {},
            "total_tools_executed": 0,
            "errors": []
        }
        
        conversation_turn = 0
        max_turns = 12  # Reduced from 20 to minimize API usage
        last_api_call_time = 0
        total_api_calls = 0
        
        while conversation_turn < max_turns:
            conversation_turn += 1
            
            try:
                # Rate limiting - ensure at least 2 seconds between API calls to avoid 429s
                current_time = time.time()
                time_since_last_call = current_time - last_api_call_time
                if time_since_last_call < 2.0:
                    await asyncio.sleep(2.0 - time_since_last_call)
                
                # Get response from LLM (may include tool calls)
                response = await self.llm.ainvoke(messages)
                last_api_call_time = time.time()
                total_api_calls += 1
                logger.info(f"API call #{total_api_calls} completed (turn {conversation_turn})")
                messages.append(response)
                
                # Yield the AI's reasoning/explanation
                if response.content:
                    yield {
                        "type": "ai_message",
                        "content": response.content,
                        "turn": conversation_turn
                    }
                
                # Check if LLM wants to call tools
                if response.tool_calls:
                    yield {
                        "type": "progress", 
                        "message": f"Executing {len(response.tool_calls)} tool(s)...",
                        "turn": conversation_turn
                    }
                    
                    # Execute each tool call
                    for tool_call in response.tool_calls:
                        tool_name = tool_call["name"]
                        tool_args = tool_call["args"]
                        
                        yield {
                            "type": "tool_start",
                            "tool_name": tool_name,
                            "tool_args": tool_args,
                            "message": f"Executing {tool_name}..."
                        }
                        
                        try:
                            # Execute the tool
                            tool_result = await self._execute_tool(tool_name, tool_args, execution_state)
                            execution_state["tool_results"][tool_name] = tool_result
                            execution_state["total_tools_executed"] += 1
                            
                            # Track repository path from clone_repository
                            if tool_name == "clone_repository" and tool_result.get("clone_path"):
                                execution_state["repository_path"] = tool_result["clone_path"]
                            
                            # Add tool result to conversation
                            messages.append(ToolMessage(
                                content=json.dumps(tool_result, default=str),
                                tool_call_id=tool_call["id"]
                            ))
                            
                            yield {
                                "type": "tool_completed",
                                "tool_name": tool_name,
                                "success": True,
                                "result": tool_result,
                                "execution_summary": f"{tool_name} completed successfully"
                            }
                            
                            # OPTIMIZATION: If cleanup just completed, likely done - minimize additional API calls
                            if tool_name == "cleanup_repository":
                                yield {
                                    "type": "progress",
                                    "message": "Analysis pipeline completed, finalizing results..."
                                }
                            
                        except Exception as e:
                            error_msg = f"Tool {tool_name} failed: {str(e)}"
                            logger.error(error_msg)
                            execution_state["errors"].append(error_msg)
                            
                            messages.append(ToolMessage(
                                content=f"Error: {error_msg}",
                                tool_call_id=tool_call["id"]
                            ))
                            
                            yield {
                                "type": "tool_error",
                                "tool_name": tool_name,
                                "error": str(e),
                                "execution_summary": f"{tool_name} failed: {str(e)}"
                            }
                
                else:
                    # No more tool calls - check completion status
                    
                    # OPTIMIZATION: If cleanup was just executed, terminate with minimal additional processing
                    if "cleanup_repository" in execution_state["tool_results"] and execution_state["total_tools_executed"] >= 3:
                        yield {
                            "type": "completed",
                            "final_response": response.content or "Analysis pipeline completed successfully. Repository analysis finished and cleaned up.",
                                                         "execution_summary": {
                                 "tools_executed": execution_state["total_tools_executed"],
                                 "tool_results": execution_state["tool_results"],
                                 "errors": execution_state["errors"],
                                 "total_turns": conversation_turn,
                                 "total_api_calls": total_api_calls,
                                 "completion_reason": "cleanup_completed"
                             }
                        }
                        break
                    
                    # Standard completion detection
                    elif self._is_completion_response(response.content, execution_state):
                        # Final response
                        yield {
                            "type": "completed",
                            "final_response": response.content,
                            "execution_summary": {
                                "tools_executed": execution_state["total_tools_executed"],
                                "tool_results": execution_state["tool_results"],
                                "errors": execution_state["errors"],
                                                                 "total_turns": conversation_turn,
                                 "total_api_calls": total_api_calls,
                                 "completion_reason": "natural_completion"
                            }
                        }
                        break
                    
                    # OPTIMIZATION: Limit conversation turns to prevent excessive API calls
                    elif conversation_turn >= 8 and execution_state["total_tools_executed"] >= 3:
                        yield {
                            "type": "completed",
                            "final_response": response.content or "Analysis completed with substantial tool execution.",
                            "execution_summary": {
                                "tools_executed": execution_state["total_tools_executed"],
                                "tool_results": execution_state["tool_results"],
                                "errors": execution_state["errors"],
                                                                 "total_turns": conversation_turn,
                                 "total_api_calls": total_api_calls,
                                 "completion_reason": "conversation_limit_reached"
                            }
                        }
                        break
                    
                    else:
                        # Continue the conversation but warn about potential API usage
                        if conversation_turn >= 5:
                            yield {
                                "type": "progress",
                                "message": f"Continuing analysis... (turn {conversation_turn}/20)"
                            }
                        continue
                        
            except Exception as e:
                logger.error(f"Error in orchestration turn {conversation_turn}: {e}")
                yield {
                    "type": "error",
                    "error": str(e),
                    "turn": conversation_turn,
                    "total_api_calls": total_api_calls
                }
                break
        
        # If we hit max turns, provide a summary
        if conversation_turn >= max_turns:
            yield {
                "type": "completed",
                "final_response": "Analysis completed (reached maximum conversation turns)",
                "execution_summary": {
                    "tools_executed": execution_state["total_tools_executed"],
                    "tool_results": execution_state["tool_results"],
                    "errors": execution_state["errors"],
                    "total_turns": conversation_turn,
                    "total_api_calls": total_api_calls,
                    "note": "Analysis may be incomplete due to conversation limit"
                }
            }
    
    async def _execute_tool(self, tool_name: str, tool_args: dict, execution_state: dict) -> Any:
        """Execute a specific tool by name"""
        if tool_name not in self.tools_map:
            raise ValueError(f"Tool {tool_name} not found")
        
        tool = self.tools_map[tool_name]
        
        # Handle special argument injection for tools that need repository_path
        if "repository_path" in tool_args and not tool_args["repository_path"]:
            if execution_state.get("repository_path"):
                tool_args["repository_path"] = execution_state["repository_path"]
        
        # Handle tools that need results from other tools
        if tool_name == "analyze_architecture":
            # Always inject language detection results if available
            if "detect_languages" in execution_state["tool_results"]:
                tool_args["language_info"] = execution_state["tool_results"]["detect_languages"]
            elif "language_info" not in tool_args:
                # Provide default language info if none available
                tool_args["language_info"] = {
                    "languages": {},
                    "primary_language": "Unknown",
                    "frameworks": [],
                    "total_code_files": 0
                }
        
        # Execute the tool
        logger.info(f"Executing tool {tool_name} with args: {tool_args}")
        
        if asyncio.iscoroutinefunction(tool.func):
            result = await tool.ainvoke(tool_args)
        else:
            result = tool.invoke(tool_args)
        
        logger.info(f"Tool {tool_name} completed successfully")
        return result
    
    def _is_completion_response(self, content: str, execution_state: dict) -> bool:
        """Determine if the AI's response indicates completion"""
        if not content:
            return False
        
        content_lower = content.lower()
        
        # Look for completion indicators
        completion_phrases = [
            "analysis complete",
            "task completed",
            "finished analyzing",
            "analysis is complete",
            "completed successfully",
            "final analysis",
            "summary:",
            "in conclusion",
            "final results",
            "analysis results"
        ]
        
        has_completion_phrase = any(phrase in content_lower for phrase in completion_phrases)
        
        # CRITICAL: Only consider complete if cleanup has been run
        # This ensures we don't end prematurely
        has_cleanup = "cleanup_repository" in execution_state["tool_results"]
        has_substantial_analysis = execution_state["total_tools_executed"] >= 4  # clone + 2-3 analysis + cleanup
        
        # Must have cleanup AND completion phrase AND substantial analysis
        return has_completion_phrase and has_cleanup and has_substantial_analysis
    
    def get_available_tools(self) -> List[Dict[str, str]]:
        """Get list of available tools with their descriptions"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in ALL_TOOLS
        ] 