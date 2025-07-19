import inspect
from typing import List, Dict, Any
from models.api_models import GetToolsResponse, AvailableToolInfo
from tools import ALL_TOOLS

class ToolService:
    def get_tools(self) -> GetToolsResponse:
        """Get information about all available tools"""
        tools_info = []
        
        for tool in ALL_TOOLS:
            # Extract tool metadata
            tool_name = tool.name
            tool_description = self._extract_description(tool.description)
            tool_parameters = self._extract_parameters(tool)
            tool_category = self._extract_category(tool_name)
            
            tool_info = AvailableToolInfo(
                name=tool_name,
                description=tool_description,
                parameters=tool_parameters,
                category=tool_category
            )
            tools_info.append(tool_info)
        
        return GetToolsResponse(
            tools=tools_info,
        )
    
    def _extract_description(self, description: str) -> str:
        """Extract and clean the tool description"""
        if not description:
            return "No description available"
        
        # Take the first paragraph/sentence as the main description
        lines = description.strip().split('\n')
        first_line = lines[0].strip()
        return first_line if first_line else "No description available"
    
    def _extract_parameters(self, tool) -> Dict[str, Any]:
        """Extract parameter information from the tool"""
        try:
            # Get the function signature
            sig = inspect.signature(tool.func)
            parameters = {}
            
            for param_name, param in sig.parameters.items():
                param_info = {
                    "type": str(param.annotation) if param.annotation != inspect.Parameter.empty else "str",
                    "required": param.default == inspect.Parameter.empty,
                    "default": param.default if param.default != inspect.Parameter.empty else None
                }
                parameters[param_name] = param_info
            
            return parameters
        except Exception:
            return {}
    
    def _extract_category(self, tool_name: str) -> str:
        """Determine the tool category based on its name"""
        if any(keyword in tool_name for keyword in ['clone', 'cleanup']):
            return "repository"
        elif any(keyword in tool_name for keyword in ['explore', 'analyze', 'dependencies']):
            return "analysis"
        elif any(keyword in tool_name for keyword in ['scan', 'vulnerabilities', 'security']):
            return "security"
        elif any(keyword in tool_name for keyword in ['create_pull_request', 'apply_fixes']):
            return "git_operations"
        elif any(keyword in tool_name for keyword in ['generate', 'summary', 'report']):
            return "reporting"
        else:
            return "general"

tool_service = ToolService()