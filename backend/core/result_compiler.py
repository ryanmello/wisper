"""
Result Compiler - Scalable compilation of tool results using metadata
"""

from typing import Dict, Any, List, Type
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from utils.logging_config import get_logger

logger = get_logger(__name__)


@dataclass
class CompilationContext:
    """Context information for result compilation"""
    user_prompt: str
    tools_executed: List[str]
    timestamp: datetime
    analysis_type: str = "ai_orchestrated"


class ResultCompiler(ABC):
    """Base class for result compilers"""
    
    @abstractmethod
    def can_compile(self, tool_name: str, metadata: Dict[str, Any]) -> bool:
        """Check if this compiler can handle the given tool result"""
        pass
    
    @abstractmethod
    def compile(self, tool_name: str, result: Dict[str, Any], context: CompilationContext) -> Dict[str, Any]:
        """Compile the tool result into the final format"""
        pass
    
    @property
    @abstractmethod
    def output_section(self) -> str:
        """The output section this compiler targets"""
        pass


class RepositoryAnalysisCompiler(ResultCompiler):
    """Compiles repository analysis results"""
    
    def can_compile(self, tool_name: str, metadata: Dict[str, Any]) -> bool:
        return metadata.get("category") in ["analysis", "codebase"]
    
    def compile(self, tool_name: str, result: Dict[str, Any], context: CompilationContext) -> Dict[str, Any]:
        metadata = result.get("_tool_metadata", {})
        result_type = metadata.get("result_type", "unknown")
        
        # Extract relevant data based on result type
        compiled_data = {}
        
        if result_type == "exploration":
            compiled_data = {
                "file_structure": result,
                "exploration_tool": tool_name
            }
        elif result_type == "language_detection":
            compiled_data = {
                "language_analysis": result,
                "detection_tool": tool_name
            }
        elif result_type == "dependency_analysis":
            compiled_data = {
                "dependencies": result,
                "analysis_tool": tool_name
            }
        elif result_type == "architecture_analysis":
            compiled_data = {
                "architecture": result,
                "analysis_tool": tool_name
            }
        else:
            # Generic analysis result
            compiled_data = {
                f"{result_type}": result,
                "tool": tool_name
            }
        
        return compiled_data
    
    @property
    def output_section(self) -> str:
        return "repository_analysis"


class SecurityAnalysisCompiler(ResultCompiler):
    """Compiles security analysis results"""
    
    def can_compile(self, tool_name: str, metadata: Dict[str, Any]) -> bool:
        return metadata.get("category") == "security"
    
    def compile(self, tool_name: str, result: Dict[str, Any], context: CompilationContext) -> Dict[str, Any]:
        metadata = result.get("_tool_metadata", {})
        result_type = metadata.get("result_type", "unknown")
        
        compiled_data = {
            f"{result_type}": result,
            "scanner_tool": tool_name,
            "scan_timestamp": context.timestamp.isoformat()
        }
        
        return compiled_data
    
    @property
    def output_section(self) -> str:
        return "security_analysis"


class GitOperationsCompiler(ResultCompiler):
    """Compiles git operations results"""
    
    def can_compile(self, tool_name: str, metadata: Dict[str, Any]) -> bool:
        return metadata.get("category") == "git_operations"
    
    def compile(self, tool_name: str, result: Dict[str, Any], context: CompilationContext) -> Dict[str, Any]:
        return {
            "operation": tool_name,
            "result": result,
            "timestamp": context.timestamp.isoformat()
        }
    
    @property
    def output_section(self) -> str:
        return "git_operations"


class ReportingCompiler(ResultCompiler):
    """Compiles reporting results (summaries, etc.)"""
    
    def can_compile(self, tool_name: str, metadata: Dict[str, Any]) -> bool:
        return metadata.get("category") == "reporting"
    
    def compile(self, tool_name: str, result: Dict[str, Any], context: CompilationContext) -> Dict[str, Any]:
        return result  # Summaries usually go directly to output
    
    @property
    def output_section(self) -> str:
        return "summary"


class PerformanceAnalysisCompiler(ResultCompiler):
    """Compiles performance analysis results - demonstrates extensibility"""
    
    def can_compile(self, tool_name: str, metadata: Dict[str, Any]) -> bool:
        return metadata.get("category") == "performance"
    
    def compile(self, tool_name: str, result: Dict[str, Any], context: CompilationContext) -> Dict[str, Any]:
        metadata = result.get("_tool_metadata", {})
        result_type = metadata.get("result_type", "unknown")
        
        compiled_data = {
            f"{result_type}_metrics": result,
            "performance_tool": tool_name,
            "analysis_timestamp": context.timestamp.isoformat(),
            "benchmark_context": context.user_prompt
        }
        
        return compiled_data
    
    @property
    def output_section(self) -> str:
        return "performance_analysis"


class MetadataBasedResultCompiler:
    """Main result compiler that uses tool metadata for scalable compilation"""
    
    def __init__(self):
        self.compilers: List[ResultCompiler] = [
            RepositoryAnalysisCompiler(),
            SecurityAnalysisCompiler(),
            GitOperationsCompiler(),
            ReportingCompiler(),
            PerformanceAnalysisCompiler()  # New compiler easily added!
        ]
    
    def register_compiler(self, compiler: ResultCompiler):
        """Register a new result compiler"""
        self.compilers.append(compiler)
    
    def compile_results(self, tool_results: Dict[str, Any], context: CompilationContext) -> Dict[str, Any]:
        """
        Compile tool results using metadata-driven approach
        
        Args:
            tool_results: Dictionary of tool_name -> result
            context: Compilation context
            
        Returns:
            Compiled results in standardized format
        """
        compiled = {
            "analysis_metadata": {
                "analysis_type": context.analysis_type,
                "user_prompt": context.user_prompt,
                "tools_executed": len(tool_results),
                "tools_used": context.tools_executed,
                "timestamp": context.timestamp.isoformat()
            }
        }
        
        # Track infrastructure results (setup/cleanup)
        infrastructure_results = {}
        
        # Process each tool result
        for tool_name, result in tool_results.items():
            if not isinstance(result, dict):
                logger.warning(f"Tool {tool_name} returned non-dict result, skipping compilation")
                continue
            
            metadata = result.get("_tool_metadata", {})
            
            # Handle infrastructure tools separately
            if metadata.get("category") == "infrastructure":
                infrastructure_results[tool_name] = result
                continue
            
            # Find appropriate compiler
            compiler = self._find_compiler(tool_name, metadata)
            
            if compiler:
                try:
                    compiled_result = compiler.compile(tool_name, result, context)
                    section = compiler.output_section
                    
                    # Merge into appropriate section
                    if section not in compiled:
                        compiled[section] = {}
                    
                    # Smart merging based on result structure
                    if isinstance(compiled_result, dict):
                        compiled[section].update(compiled_result)
                    else:
                        compiled[section][tool_name] = compiled_result
                        
                except Exception as e:
                    logger.error(f"Failed to compile result from {tool_name}: {e}")
                    # Fallback: add to unprocessed section
                    if "unprocessed_results" not in compiled:
                        compiled["unprocessed_results"] = {}
                    compiled["unprocessed_results"][tool_name] = result
            else:
                # No specific compiler found, add to general results
                if "general_results" not in compiled:
                    compiled["general_results"] = {}
                compiled["general_results"][tool_name] = result
        
        # Add infrastructure metadata if any
        if infrastructure_results:
            compiled["analysis_metadata"]["infrastructure"] = infrastructure_results
        
        return compiled
    
    def _find_compiler(self, tool_name: str, metadata: Dict[str, Any]) -> ResultCompiler:
        """Find the appropriate compiler for a tool result"""
        for compiler in self.compilers:
            if compiler.can_compile(tool_name, metadata):
                return compiler
        return None


# Global instance
result_compiler = MetadataBasedResultCompiler() 