import asyncio
from typing import AsyncGenerator
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, ToolMessage
from tools import ALL_TOOLS
from utils.logging_config import get_logger
from models.api_models import OrchestratorUpdate
from config.settings import settings

logger = get_logger(__name__)

class Orchestrator:
    def __init__(self):
        self.llm = ChatOpenAI(
            model="gpt-4", 
            temperature=0, 
            api_key=settings.OPENAI_API_KEY
        ).bind_tools(ALL_TOOLS)
        
        self.tools_map = {tool.name: tool for tool in ALL_TOOLS}
        self.system_prompt = """
                             You are an expert repository analysis and automation assistant. 
                             Your job is to help users analyze code repositories and automate development workflows.
                             You MUST immediately execute tools to fulfill user requests - never just describe or plan what you will do.
                             Use available tools to fulfill the user's request completely.
                             """

    async def process_prompt(self, user_prompt: str, repository_url: str) -> AsyncGenerator[OrchestratorUpdate, None]:        
        logger.info(f"Processing prompt for repository: {repository_url}")
        
        execution_state = {
            "tools_executed": 0,
            "tool_results": {},
            "errors": [],
            "sent_ai_messages": set()
        }
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"""
                User Request: {user_prompt}
                Repository URL: {repository_url}""")
        ]
        
        max_turns = 12
        
        for turn in range(max_turns):
            try:
                logger.info(f"Turn {turn + 1}: Making LLM call")
                
                response = await self.llm.ainvoke(messages)
                messages.append(response)
                
                if response.content and response.content not in execution_state["sent_ai_messages"]:
                    execution_state["sent_ai_messages"].add(response.content)
                    yield OrchestratorUpdate.content(
                        message=response.content,
                        turn=turn + 1
                    )
                
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    logger.info(f"Executing {len(response.tool_calls)} tools")
                    
                    yield OrchestratorUpdate.status(
                        message=f"Executing {len(response.tool_calls)} tool(s)...",
                        turn=turn + 1
                    )
                    
                    for tool_call in response.tool_calls:
                        tool_name = tool_call.get('name', 'unknown')
                        tool_args = tool_call.get('args', {})
                        tool_call_id = tool_call.get('id', 'unknown')

                        yield OrchestratorUpdate.status(
                            message=f"Executing {tool_name}...",
                            tool_name=tool_name
                        )
                        
                        try:
                            tool = self.tools_map[tool_name]
                            is_async = getattr(tool, '_is_async_tool', False)
                            
                            logger.debug(f"Executing {tool_name} - ASYNC: {is_async}")

                            if is_async:
                                result = await tool.ainvoke(tool_args)
                            else:
                                result = tool.invoke(tool_args)
                            
                            execution_state['tools_executed'] += 1
                            
                            execution_state['tool_results'][tool_name] = result
                            logger.info(f"Stored result for {tool_name}, total tools in state: {len(execution_state['tool_results'])}")
                            
                            yield OrchestratorUpdate.status(
                                message=f"{tool_name} completed successfully",
                                tool_name=tool_name,
                                tools_executed=execution_state['tools_executed']
                            )

                            messages.append(ToolMessage(
                                content=f"<{tool_name}>{result}<{tool_name}>",
                                tool_call_id=tool_call_id
                            ))                            
                        except Exception as e:
                            error_msg = f"Tool {tool_name} failed: {str(e)}"
                            logger.error(error_msg, exc_info=True)
                            execution_state['errors'].append(error_msg)
                            
                            yield OrchestratorUpdate.error(
                                message=error_msg,
                                error_details=str(e),
                                tool_name=tool_name
                            )
                            
                            error_summary = f"<{tool_name}>Failed: {str(e)[:100]}</{tool_name}>"
                            messages.append(ToolMessage(
                                content=error_summary,
                                tool_call_id=tool_call_id
                            ))
                
                else:                    
                    yield OrchestratorUpdate.completed(
                        message=f"Analysis completed successfully with {execution_state['tools_executed']} tools executed.",
                        final_results={
                            "tools_executed": execution_state['tools_executed'],
                            "tool_results": execution_state['tool_results'],
                            "errors": execution_state['errors']
                        },
                        tools_executed=execution_state['tools_executed'],
                        total_turns=turn + 1
                    )
                    break
                
            except Exception as e:
                logger.error(f"Error in turn {turn + 1}: {str(e)}", exc_info=True)
                yield OrchestratorUpdate.error(
                    message=f"Orchestration error: {str(e)}",
                    error_details=str(e),
                    turn=turn + 1
                )
                break
        
        # completed {max_turns} turns without breaking
        else:
            yield OrchestratorUpdate.completed(
                message=f"Analysis completed after {max_turns} turns with {execution_state['tools_executed']} tools executed.",
                final_results={
                    "tools_executed": execution_state['tools_executed'],
                    "tool_results": execution_state['tool_results'],
                    "errors": execution_state['errors']
                },
                tools_executed=execution_state['tools_executed'],
                total_turns=max_turns
            ) 