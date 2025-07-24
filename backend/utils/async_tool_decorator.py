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
        # Preserve any existing metadata from other decorators (like @tool_category)
        metadata = {}
        for attr_name in dir(f):
            if not attr_name.startswith('_') and not callable(getattr(f, attr_name)):
                try:
                    metadata[attr_name] = getattr(f, attr_name)
                except (AttributeError, TypeError):
                    pass
        
        # Create the LangChain tool using the standard decorator
        langchain_tool = tool(**tool_kwargs)(f)
        
        # Mark the tool as async for our orchestrator
        object.__setattr__(langchain_tool, "_is_async_tool", True)
        object.__setattr__(langchain_tool, "_original_async_func", f)
        
        # Restore any metadata that was on the original function
        for key, value in metadata.items():
            setattr(langchain_tool, key, value)
        
        return langchain_tool
    
    # Handle both @async_tool and @async_tool() usage
    if func is not None:
        return decorator(func)
    else:
        return decorator 
