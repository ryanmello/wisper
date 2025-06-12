"""
Base tool interface for Whisper analysis tools.

This module defines the base interface that all analysis tools must implement
to be compatible with the SmartAnalysisAgent system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass
from pydantic import BaseModel


class ToolCapability(Enum):
    """Enumeration of tool capabilities."""
    CODEBASE_EXPLORATION = "codebase_exploration"
    VULNERABILITY_SCANNING = "vulnerability_scanning"
    PERFORMANCE_ANALYSIS = "performance_analysis"
    CODE_QUALITY = "code_quality"
    SECURITY_AUDIT = "security_audit"
    DOCUMENTATION = "documentation"
    DEPENDENCY_ANALYSIS = "dependency_analysis"
    ARCHITECTURE_REVIEW = "architecture_review"


@dataclass
class ToolMetadata:
    """Metadata about a tool's capabilities and requirements."""
    name: str
    description: str
    version: str
    capabilities: List[ToolCapability]
    supported_languages: List[str]
    required_files: List[str]  # Files that must exist for tool to work
    optional_files: List[str]  # Files that enhance tool functionality
    execution_time_estimate: str  # e.g., "1-2 minutes", "30 seconds"
    dependencies: List[str]  # External dependencies required


class ToolResult(BaseModel):
    """Result returned by a tool execution."""
    tool_name: str
    success: bool
    execution_time: float
    results: Dict[str, Any]
    errors: List[str] = []
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True


class AnalysisContext(BaseModel):
    """Context provided to tools for analysis."""
    repository_path: str
    repository_url: str
    intent: str  # "explore", "find_vulnerabilities", "analyze_performance", etc.
    target_languages: List[str] = []
    scope: str = "full"  # "full", "security_focused", "performance_focused"
    specific_files: List[str] = []
    depth: str = "comprehensive"  # "surface", "deep", "comprehensive"
    additional_params: Dict[str, Any] = {}


class BaseTool(ABC):
    """
    Abstract base class for all analysis tools.
    
    All tools must inherit from this class and implement the required methods.
    """
    
    def __init__(self):
        self._metadata = self._create_metadata()
        self._is_healthy = True
        self._last_health_check = None
    
    @abstractmethod
    def _create_metadata(self) -> ToolMetadata:
        """Create and return tool metadata."""
        pass
    
    @property
    def metadata(self) -> ToolMetadata:
        """Get tool metadata."""
        return self._metadata
    
    @abstractmethod
    async def execute(self, context: AnalysisContext, **kwargs) -> ToolResult:
        """
        Execute the tool with the given context.
        
        Args:
            context: Analysis context containing repository info and parameters
            **kwargs: Additional tool-specific parameters
            
        Returns:
            ToolResult containing the analysis results
        """
        pass
    
    @abstractmethod
    def validate_context(self, context: AnalysisContext) -> tuple[bool, List[str]]:
        """
        Validate that the context is suitable for this tool.
        
        Args:
            context: Analysis context to validate
            
        Returns:
            Tuple of (is_valid, list_of_validation_errors)
        """
        pass
    
    def can_handle_context(self, context: AnalysisContext) -> bool:
        """
        Check if this tool can handle the given context.
        
        Args:
            context: Analysis context to check
            
        Returns:
            True if tool can handle this context
        """
        is_valid, _ = self.validate_context(context)
        return is_valid
    
    def get_execution_estimate(self, context: AnalysisContext) -> str:
        """
        Get estimated execution time for this context.
        
        Args:
            context: Analysis context
            
        Returns:
            Human-readable execution time estimate
        """
        return self._metadata.execution_time_estimate
    
    async def health_check(self) -> bool:
        """
        Perform a health check to ensure tool is ready.
        
        Returns:
            True if tool is healthy and ready to execute
        """
        # Default implementation - can be overridden
        import time
        self._last_health_check = time.time()
        return True
    
    @property
    def is_healthy(self) -> bool:
        """Check if tool is currently healthy."""
        return self._is_healthy
    
    def _extract_file_paths(self, context: AnalysisContext, file_patterns: List[str]) -> List[str]:
        """
        Helper method to extract file paths matching patterns from repository.
        
        Args:
            context: Analysis context
            file_patterns: List of file patterns to search for
            
        Returns:
            List of matching file paths
        """
        import os
        import glob
        
        found_files = []
        repo_path = context.repository_path
        
        for pattern in file_patterns:
            pattern_path = os.path.join(repo_path, pattern)
            matches = glob.glob(pattern_path, recursive=True)
            found_files.extend(matches)
        
        return found_files
    
    def _read_file_content(self, file_path: str) -> Optional[str]:
        """
        Helper method to safely read file content.
        
        Args:
            file_path: Path to file to read
            
        Returns:
            File content as string, or None if error
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception:
            try:
                # Try with different encoding
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except Exception:
                return None 