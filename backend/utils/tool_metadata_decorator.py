"""
Tool metadata decorator for adding category and other metadata to LangChain tools
"""

from typing import Any

def tool_category(category: str, **metadata):
    """
    Decorator to add category and additional metadata to tools.
    
    Usage:
        @tool_category("security")
        @tool
        def my_tool():
            pass
            
        @tool_category("analysis", priority="high", execution_time="slow")
        @async_tool
        def my_async_tool():
            pass
    
    Args:
        category: The category this tool belongs to (e.g., "security", "analysis", etc.)
        **metadata: Additional metadata key-value pairs
    """
    def decorator(func_or_tool):
        # Add category as the primary metadata
        if hasattr(func_or_tool, 'name'):
            # Already a LangChain tool - use object.__setattr__ to bypass Pydantic validation
            try:
                object.__setattr__(func_or_tool, 'category', category)
                for key, value in metadata.items():
                    object.__setattr__(func_or_tool, key, value)
            except Exception:
                # If that fails, store in a metadata dict
                if not hasattr(func_or_tool, '_custom_metadata'):
                    object.__setattr__(func_or_tool, '_custom_metadata', {})
                func_or_tool._custom_metadata['category'] = category
                func_or_tool._custom_metadata.update(metadata)
        else:
            # Regular function - add metadata that will be preserved by @tool or @async_tool
            func_or_tool.category = category
            for key, value in metadata.items():
                setattr(func_or_tool, key, value)
        
        return func_or_tool
    
    return decorator

def get_tool_metadata(tool, key: str, default: Any = None) -> Any:
    """
    Helper function to extract metadata from a tool.
    
    Args:
        tool: The tool object to extract metadata from
        key: The metadata key to look for
        default: Default value if the key is not found
        
    Returns:
        The metadata value or default
    """
    # First try direct attribute access
    if hasattr(tool, key):
        return getattr(tool, key, default)
    
    # Then try custom metadata dict
    if hasattr(tool, '_custom_metadata') and key in tool._custom_metadata:
        return tool._custom_metadata[key]
    
    return default 
