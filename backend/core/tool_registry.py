"""
Tool Registry for managing and discovering analysis tools.

This module provides a central registry system for managing all available
analysis tools in the Whisper system.
"""

import importlib
import inspect
import logging
from typing import Dict, List, Optional, Type
from pathlib import Path

from tools.base_tool import BaseTool, ToolCapability, AnalysisContext
from utils.logging_config import get_logger

logger = get_logger(__name__)


class ToolRegistry:
    """
    Registry for managing and discovering analysis tools.
    
    The registry automatically discovers tools and provides methods to
    find appropriate tools based on context and capabilities.
    """
    
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}
        self._tool_classes: Dict[str, Type[BaseTool]] = {}
        self._capabilities_map: Dict[ToolCapability, List[str]] = {}
        self._language_map: Dict[str, List[str]] = {}
        self._initialized = False
    
    async def initialize(self):
        """Initialize the registry by discovering and registering tools."""
        if self._initialized:
            return
        
        logger.info("Initializing tool registry...")
        
        # Discover and register tools
        await self._discover_tools()
        
        # Build capability and language maps
        self._build_maps()
        
        # Perform health checks
        await self._health_check_all_tools()
        
        self._initialized = True
        logger.info(f"Tool registry initialized with {len(self._tools)} tools")
    
    async def _discover_tools(self):
        """Automatically discover tools in the tools directory."""
        tools_path = Path(__file__).parent.parent / "tools"
        
        # Import all tool modules
        for tool_file in tools_path.rglob("*_tool.py"):
            try:
                # Convert file path to module path
                relative_path = tool_file.relative_to(Path(__file__).parent.parent)
                module_path = str(relative_path).replace("/", ".").replace("\\", ".")[:-3]
                
                # Import the module
                module = importlib.import_module(module_path)
                
                # Find tool classes in the module
                for name, obj in inspect.getmembers(module):
                    if (inspect.isclass(obj) and 
                        issubclass(obj, BaseTool) and 
                        obj != BaseTool and
                        not inspect.isabstract(obj)):
                        
                        await self._register_tool_class(name, obj)
                        
            except Exception as e:
                logger.error(f"Failed to import tool from {tool_file}: {e}")
    
    async def _register_tool_class(self, class_name: str, tool_class: Type[BaseTool]):
        """Register a tool class and create an instance."""
        try:
            tool_instance = tool_class()
            tool_name = tool_instance.metadata.name
            
            self._tool_classes[tool_name] = tool_class
            self._tools[tool_name] = tool_instance
            
            logger.info(f"Registered tool: {tool_name} ({class_name})")
            
        except Exception as e:
            logger.error(f"Failed to register tool {class_name}: {e}")
    
    def _build_maps(self):
        """Build capability and language mapping for efficient tool discovery."""
        self._capabilities_map = {}
        self._language_map = {}
        
        for tool_name, tool in self._tools.items():
            metadata = tool.metadata
            
            # Build capability map
            for capability in metadata.capabilities:
                if capability not in self._capabilities_map:
                    self._capabilities_map[capability] = []
                self._capabilities_map[capability].append(tool_name)
            
            # Build language map
            for language in metadata.supported_languages:
                language_lower = language.lower()
                if language_lower not in self._language_map:
                    self._language_map[language_lower] = []
                self._language_map[language_lower].append(tool_name)
    
    async def _health_check_all_tools(self):
        """Perform health checks on all registered tools."""
        unhealthy_tools = []
        
        for tool_name, tool in self._tools.items():
            try:
                is_healthy = await tool.health_check()
                if not is_healthy:
                    unhealthy_tools.append(tool_name)
            except Exception as e:
                logger.error(f"Health check failed for {tool_name}: {e}")
                unhealthy_tools.append(tool_name)
        
        if unhealthy_tools:
            logger.warning(f"Unhealthy tools detected: {unhealthy_tools}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get a specific tool by name."""
        return self._tools.get(tool_name)
    
    def get_all_tools(self) -> Dict[str, BaseTool]:
        """Get all registered tools."""
        return self._tools.copy()
    
    def get_tools_by_capability(self, capability: ToolCapability) -> List[BaseTool]:
        """Get all tools that have a specific capability."""
        tool_names = self._capabilities_map.get(capability, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def get_tools_by_language(self, language: str) -> List[BaseTool]:
        """Get all tools that support a specific language."""
        language_lower = language.lower()
        tool_names = self._language_map.get(language_lower, [])
        return [self._tools[name] for name in tool_names if name in self._tools]
    
    def find_suitable_tools(self, context: AnalysisContext) -> List[BaseTool]:
        """
        Find tools suitable for the given analysis context.
        
        Args:
            context: Analysis context to match against
            
        Returns:
            List of suitable tools, ordered by relevance
        """
        suitable_tools = []
        
        # First, filter by tools that can handle the context
        for tool in self._tools.values():
            if tool.can_handle_context(context) and tool.is_healthy:
                suitable_tools.append(tool)
        
        # Sort by relevance (tools that match languages get priority)
        if context.target_languages:
            def relevance_score(tool: BaseTool) -> int:
                score = 0
                metadata = tool.metadata
                
                # Language match bonus
                for lang in context.target_languages:
                    if lang.lower() in [l.lower() for l in metadata.supported_languages]:
                        score += 10
                
                # Capability match bonus based on intent
                intent_capability_map = {
                    "explore": ToolCapability.CODEBASE_EXPLORATION,
                    "find_vulnerabilities": ToolCapability.VULNERABILITY_SCANNING,
                    "security_audit": ToolCapability.SECURITY_AUDIT,
                    "analyze_performance": ToolCapability.PERFORMANCE_ANALYSIS,
                    "code_quality": ToolCapability.CODE_QUALITY,
                    "documentation": ToolCapability.DOCUMENTATION,
                }
                
                target_capability = intent_capability_map.get(context.intent)
                if target_capability and target_capability in metadata.capabilities:
                    score += 20
                
                return score
            
            suitable_tools.sort(key=relevance_score, reverse=True)
        
        return suitable_tools
    
    def get_tools_for_intent(self, intent: str) -> List[BaseTool]:
        """
        Get tools that are suitable for a specific intent.
        
        Args:
            intent: Analysis intent (e.g., "explore", "find_vulnerabilities")
            
        Returns:
            List of suitable tools
        """
        intent_capability_map = {
            "explore": ToolCapability.CODEBASE_EXPLORATION,
            "find_vulnerabilities": ToolCapability.VULNERABILITY_SCANNING,
            "security_audit": ToolCapability.SECURITY_AUDIT,
            "analyze_performance": ToolCapability.PERFORMANCE_ANALYSIS,
            "code_quality": ToolCapability.CODE_QUALITY,
            "documentation": ToolCapability.DOCUMENTATION,
        }
        
        capability = intent_capability_map.get(intent)
        if capability:
            return self.get_tools_by_capability(capability)
        
        return []
    
    async def register_tool(self, tool: BaseTool):
        """
        Manually register a tool instance.
        
        Args:
            tool: Tool instance to register
        """
        tool_name = tool.metadata.name
        self._tools[tool_name] = tool
        
        # Rebuild maps
        self._build_maps()
        
        logger.info(f"Manually registered tool: {tool_name}")
    
    def unregister_tool(self, tool_name: str):
        """
        Unregister a tool.
        
        Args:
            tool_name: Name of tool to unregister
        """
        if tool_name in self._tools:
            del self._tools[tool_name]
            self._build_maps()  # Rebuild maps
            logger.info(f"Unregistered tool: {tool_name}")
    
    def get_registry_info(self) -> Dict[str, any]:
        """Get information about the registry state."""
        return {
            "total_tools": len(self._tools),
            "healthy_tools": len([t for t in self._tools.values() if t.is_healthy]),
            "capabilities": list(self._capabilities_map.keys()),
            "supported_languages": list(self._language_map.keys()),
            "tools": {
                name: {
                    "capabilities": [c.value for c in tool.metadata.capabilities],
                    "languages": tool.metadata.supported_languages,
                    "healthy": tool.is_healthy
                }
                for name, tool in self._tools.items()
            }
        }


# Global registry instance
_registry: Optional[ToolRegistry] = None


async def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
        await _registry.initialize()
    return _registry


async def initialize_tool_registry():
    """Initialize the global tool registry."""
    await get_tool_registry() 