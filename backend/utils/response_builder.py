"""
Response Builder - Utility for creating standardized tool responses

This module provides utilities to wrap existing tool outputs into the standardized 
response format, ensuring consistency across all tools while maintaining backward compatibility.
"""

from typing import Any, Dict, List, Optional, Union
from datetime import datetime
import time

from models.api_models import StandardToolResponse, StandardError, StandardMetrics
from utils.logging_config import get_logger

logger = get_logger(__name__)

class ToolResponseBuilder:
    """Builder class for creating standardized tool responses"""
    
    def __init__(self, tool_name: str):
        self.tool_name = tool_name
        self.start_time = time.time()
        
    def build_success(
        self, 
        data: Any, 
        summary: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None
    ) -> StandardToolResponse:
        """Build a successful tool response"""
        return StandardToolResponse(
            status="success",
            tool_name=self.tool_name,
            data=data,
            summary=summary or self._generate_default_summary(data),
            metrics=self._build_metrics(metrics, data),
            warnings=warnings
        )
    
    def build_error(
        self, 
        error_message: str, 
        error_details: Optional[str] = None,
        error_type: Optional[str] = None,
        data: Optional[Any] = None
    ) -> StandardToolResponse:
        """Build an error tool response"""
        return StandardToolResponse(
            status="error",
            tool_name=self.tool_name,
            data=data,
            error=StandardError(
                message=error_message,
                details=error_details,
                error_type=error_type
            ),
            summary=f"Tool {self.tool_name} failed: {error_message}"
        )
    
    def build_partial_success(
        self,
        data: Any,
        error_message: str,
        summary: Optional[str] = None,
        metrics: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
        error_details: Optional[str] = None
    ) -> StandardToolResponse:
        """Build a partial success response (some operations succeeded, some failed)"""
        return StandardToolResponse(
            status="partial_success",
            tool_name=self.tool_name,
            data=data,
            error=StandardError(
                message=error_message,
                details=error_details,
                error_type="partial_failure"
            ),
            summary=summary or f"Tool {self.tool_name} completed with some failures",
            metrics=self._build_metrics(metrics, data),
            warnings=warnings
        )
    
    def build_skipped(
        self, 
        reason: str, 
        data: Optional[Any] = None
    ) -> StandardToolResponse:
        """Build a skipped tool response"""
        return StandardToolResponse(
            status="skipped",
            tool_name=self.tool_name,
            data=data,
            summary=f"Tool {self.tool_name} skipped: {reason}"
        )
    
    def wrap_existing_result(self, existing_result: Dict[str, Any]) -> StandardToolResponse:
        """
        Wrap an existing tool result into standardized format.
        
        This method analyzes the existing result structure and maps it to the standard format.
        """
        # Check if result already has explicit status field
        if "status" in existing_result:
            status = existing_result["status"]
            
            if status == "success":
                return self._wrap_success_result(existing_result)
            elif status == "error":
                return self._wrap_error_result(existing_result)
            elif status in ["partial_success", "completed"]:
                return self._wrap_success_result(existing_result)
            elif status == "skipped":
                return self._wrap_skipped_result(existing_result)
        
        # Check for error indicators
        if "error" in existing_result:
            return self._wrap_error_result(existing_result)
        
        # Default to success if no error indicators
        return self._wrap_success_result(existing_result)
    
    def _wrap_success_result(self, result: Dict[str, Any]) -> StandardToolResponse:
        """Wrap a successful result"""
        # Extract known fields
        data = self._extract_data_from_result(result)
        summary = result.get("summary") or result.get("message") or result.get("audit_summary")
        warnings = result.get("warnings")
        
        # Extract metrics
        metrics = self._extract_metrics_from_result(result)
        
        return StandardToolResponse(
            status="success",
            tool_name=self.tool_name,
            data=data,
            summary=summary or self._generate_default_summary(data),
            metrics=metrics,
            warnings=warnings
        )
    
    def _wrap_error_result(self, result: Dict[str, Any]) -> StandardToolResponse:
        """Wrap an error result"""
        error_message = result.get("error", "Unknown error")
        error_details = result.get("reason") or result.get("details")
        
        return StandardToolResponse(
            status="error",
            tool_name=self.tool_name,
            data=self._extract_data_from_result(result),
            error=StandardError(
                message=str(error_message),
                details=error_details,
                error_type="tool_execution_error"
            ),
            summary=f"Tool {self.tool_name} failed: {error_message}"
        )
    
    def _wrap_skipped_result(self, result: Dict[str, Any]) -> StandardToolResponse:
        """Wrap a skipped result"""
        reason = result.get("reason", "Unknown reason")
        
        return StandardToolResponse(
            status="skipped",
            tool_name=self.tool_name,
            data=self._extract_data_from_result(result),
            summary=f"Tool {self.tool_name} skipped: {reason}"
        )
    
    def _extract_data_from_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract the actual data content from a result, excluding metadata fields
        """
        # Fields that are metadata, not data
        metadata_fields = {
            "status", "error", "reason", "message", "summary", "audit_summary", 
            "timestamp", "execution_time", "warnings", "action"
        }
        
        # Extract data fields
        data = {}
        for key, value in result.items():
            if key not in metadata_fields:
                data[key] = value
        
        return data if data else result
    
    def _extract_metrics_from_result(self, result: Dict[str, Any]) -> Optional[StandardMetrics]:
        """Extract metrics from existing result structure"""
        metrics_data = {}
        
        # Common metric field mappings
        metric_mappings = {
            "total_files": "files_analyzed",
            "files_modified": "items_processed", 
            "total_dependencies": "items_processed",
            "total_issues": "issues_found",
            "vulnerabilities_found": "issues_found",
            "security_issues": "issues_found"
        }
        
        # Extract metrics based on known field names
        for result_key, metric_key in metric_mappings.items():
            if result_key in result:
                value = result[result_key]
                if isinstance(value, (int, list)):
                    metrics_data[metric_key] = len(value) if isinstance(value, list) else value
        
        # Add execution time
        execution_time_ms = int((time.time() - self.start_time) * 1000)
        metrics_data["execution_time_ms"] = execution_time_ms
        
        return StandardMetrics(**metrics_data) if metrics_data else None
    
    def _build_metrics(self, custom_metrics: Optional[Dict[str, Any]], data: Any) -> Optional[StandardMetrics]:
        """Build metrics from custom metrics and data analysis"""
        metrics_data = {}
        
        # Add custom metrics if provided
        if custom_metrics:
            for key, value in custom_metrics.items():
                if key in ["items_processed", "files_analyzed", "issues_found"]:
                    metrics_data[key] = value
        
        # Try to extract metrics from data if it's a dict
        if isinstance(data, dict):
            metrics_from_data = self._extract_metrics_from_result(data)
            if metrics_from_data:
                for field in ["items_processed", "files_analyzed", "issues_found"]:
                    value = getattr(metrics_from_data, field, None)
                    if value is not None:
                        metrics_data[field] = value
        
        # Always add execution time
        execution_time_ms = int((time.time() - self.start_time) * 1000)
        metrics_data["execution_time_ms"] = execution_time_ms
        
        return StandardMetrics(**metrics_data) if metrics_data else None
    
    def _generate_default_summary(self, data: Any) -> str:
        """Generate a default summary based on the tool name and data"""
        if isinstance(data, dict):
            # Try to generate summary based on data content
            if "total_files" in data:
                return f"{self.tool_name} analyzed {data['total_files']} files"
            elif "vulnerabilities_found" in data:
                count = data["vulnerabilities_found"]
                return f"{self.tool_name} found {count} vulnerabilities"
            elif "dependencies_by_language" in data:
                total = sum(len(deps) for deps in data["dependencies_by_language"].values())
                return f"{self.tool_name} analyzed {total} dependencies"
            elif "architectural_patterns" in data:
                count = len(data["architectural_patterns"])
                return f"{self.tool_name} identified {count} architectural patterns"
        
        return f"{self.tool_name} completed successfully"


def create_tool_response_builder(tool_name: str) -> ToolResponseBuilder:
    """Factory function to create a ToolResponseBuilder"""
    return ToolResponseBuilder(tool_name) 
