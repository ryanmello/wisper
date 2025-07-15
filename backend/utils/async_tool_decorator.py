"""
Custom async-aware tool decorator for LangChain tools
"""

from functools import wraps
from langchain_core.tools import tool

def async_tool(func=None, **tool_kwargs):
    """
    Custom decorator for async tools that properly marks them for detection.
    Usage: @async_tool instead of @tool for async functions.
    """
    def decorator(f):
        # Create the LangChain tool using the standard decorator
        langchain_tool = tool(**tool_kwargs)(f)
        
        # Mark the tool as async for our orchestrator
        langchain_tool._is_async_tool = True
        langchain_tool._original_async_func = f
        
        return langchain_tool
    
    # Handle both @async_tool and @async_tool() usage
    if func is not None:
        return decorator(func)
    else:
        return decorator 
