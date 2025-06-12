"""
API Models - Pydantic models for request/response validation
"""

from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, field_validator
import re

class AnalysisRequest(BaseModel):
    """Request model for repository analysis."""
    repository_url: str = Field(..., description="GitHub repository URL")
    task_type: str = Field(default="explore-codebase", description="Type of analysis task")
    github_token: Optional[str] = Field(None, description="GitHub token for private repositories")
    
    @field_validator('repository_url')
    @classmethod
    def validate_repository_url(cls, v):
        """Validate that the repository URL is a valid GitHub URL."""
        # More flexible pattern to handle various GitHub URL formats
        github_pattern = r'^https://github\.com/[a-zA-Z0-9\-_\.]+/[a-zA-Z0-9\-_\.]+/?$'
        if not re.match(github_pattern, v.rstrip('/')):
            raise ValueError('Must be a valid GitHub repository URL (https://github.com/owner/repo)')
        return v.rstrip('/')
    
    @field_validator('task_type')
    @classmethod
    def validate_task_type(cls, v):
        """Validate task type."""
        valid_types = ['explore-codebase', 'dependency-audit']
        if v not in valid_types:
            raise ValueError(f'Task type must be one of: {", ".join(valid_types)}')
        return v

# New smart analysis models
class SmartAnalysisRequest(BaseModel):
    """Request model for smart context-based analysis."""
    repository_url: str = Field(..., description="GitHub repository URL")
    context: str = Field(..., description="Natural language description of what to analyze")
    intent: Optional[str] = Field(None, description="Explicit intent override")
    target_languages: Optional[List[str]] = Field(None, description="Target programming languages")
    scope: Optional[str] = Field("full", description="Analysis scope: full, security_focused, performance_focused")
    depth: Optional[str] = Field("comprehensive", description="Analysis depth: surface, deep, comprehensive")
    additional_params: Optional[Dict[str, Any]] = Field(None, description="Additional parameters")
    
    @field_validator('repository_url')
    @classmethod
    def validate_repository_url(cls, v):
        """Validate that the repository URL is a valid GitHub URL."""
        github_pattern = r'^https://github\.com/[a-zA-Z0-9\-_\.]+/[a-zA-Z0-9\-_\.]+/?$'
        if not re.match(github_pattern, v.rstrip('/')):
            raise ValueError('Must be a valid GitHub repository URL (https://github.com/owner/repo)')
        return v.rstrip('/')
    
    @field_validator('scope')
    @classmethod
    def validate_scope(cls, v):
        """Validate analysis scope."""
        valid_scopes = ["full", "security_focused", "performance_focused"]
        if v not in valid_scopes:
            raise ValueError(f'Scope must be one of: {", ".join(valid_scopes)}')
        return v
    
    @field_validator('depth')
    @classmethod
    def validate_depth(cls, v):
        """Validate analysis depth."""
        valid_depths = ["surface", "deep", "comprehensive"]
        if v not in valid_depths:
            raise ValueError(f'Depth must be one of: {", ".join(valid_depths)}')
        return v

class AnalysisResponse(BaseModel):
    """Response model for analysis task creation."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Status message")
    websocket_url: str = Field(..., description="WebSocket URL for real-time updates")
    task_type: str = Field(..., description="Type of analysis task")
    repository_url: str = Field(..., description="GitHub repository URL")
    github_pr_enabled: bool = Field(default=False, description="Whether GitHub PR creation is enabled")

class SmartAnalysisResponse(BaseModel):
    """Response model for smart analysis task creation."""
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(..., description="Task status")
    message: str = Field(..., description="Status message")
    websocket_url: str = Field(..., description="WebSocket URL for real-time updates")
    analysis_plan: Optional[Dict[str, Any]] = Field(None, description="Initial analysis plan")

class TaskStatus(BaseModel):
    """Model for task status information."""
    task_id: str
    status: str  # created, running, completed, failed, not_found
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

class ProgressUpdate(BaseModel):
    """Model for progress update messages."""
    type: str = Field(..., description="Message type")
    task_id: str = Field(..., description="Task identifier")
    current_step: str = Field(..., description="Current analysis step")
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    partial_results: Dict[str, Any] = Field(default_factory=dict, description="Partial analysis results")

class ExecutionPlan(BaseModel):
    """Model for analysis execution plan."""
    total_tools: int
    estimated_total_time: str
    strategy: str
    batches: List[Dict[str, Any]]

class ToolExecutionResult(BaseModel):
    """Model for individual tool execution results."""
    tool_name: str
    success: bool
    execution_time: float
    results: Dict[str, Any]
    errors: List[str] = []
    warnings: List[str] = []
    metadata: Dict[str, Any] = {}

class VulnerabilitySummary(BaseModel):
    """Model for vulnerability scan summary."""
    total_vulnerabilities: int
    critical_vulnerabilities: int
    high_vulnerabilities: int
    medium_vulnerabilities: int
    low_vulnerabilities: int
    risk_level: str
    risk_score: int
    affected_modules: List[str]
    recommendations: List[str]

class SmartAnalysisResults(BaseModel):
    """Model for smart analysis results."""
    summary: str = Field(..., description="AI-generated analysis summary")
    execution_info: Dict[str, Any] = Field(..., description="Execution information")
    tool_results: Dict[str, Any] = Field(..., description="Results from individual tools")
    vulnerability_summary: Optional[VulnerabilitySummary] = Field(None, description="Security vulnerability summary")
    metrics: Dict[str, Any] = Field(..., description="Key metrics and statistics")
    recommendations: List[str] = Field(..., description="Actionable recommendations")

class FileStructure(BaseModel):
    """Model for file structure analysis results."""
    total_files: int
    total_lines: int
    file_types: Dict[str, int]
    directory_structure: Dict[str, List[str]]
    main_directories: List[str]

class LanguageAnalysis(BaseModel):
    """Model for language analysis results."""
    languages: Dict[str, int]
    primary_language: str
    frameworks: List[Dict[str, Any]]
    total_code_files: int

class MainComponent(BaseModel):
    """Model for main component information."""
    name: str
    type: str
    path: str
    size: Optional[int] = None
    file_count: Optional[int] = None

class WhisperAnalysisResults(BaseModel):
    """Model for whisper analysis results."""
    analysis: str = Field(..., description="AI-generated architectural insights")
    file_structure: FileStructure
    language_analysis: LanguageAnalysis
    architecture_patterns: List[str]
    main_components: List[MainComponent]
    dependencies: Dict[str, List[str]]

class AnalysisResults(BaseModel):
    """Model for complete analysis results."""
    summary: str = Field(..., description="Analysis summary")
    statistics: Dict[str, Any] = Field(..., description="Key statistics")
    detailed_results: Dict[str, Any] = Field(..., description="Detailed analysis results")

class TaskCompletedMessage(BaseModel):
    """Model for task completion message."""
    type: str = Field(default="task.completed")
    task_id: str
    results: AnalysisResults

class TaskErrorMessage(BaseModel):
    """Model for task error message."""
    type: str = Field(default="task.error")
    task_id: str
    error: str
    error_code: Optional[str] = None

class TaskStartedMessage(BaseModel):
    """Model for task started message."""
    type: str = Field(default="task.started")
    task_id: str
    status: str = Field(default="running")
    repository_url: str
    task_type: str

class SmartTaskStartedMessage(BaseModel):
    """Model for smart task started message."""
    type: str = Field(default="smart_task.started")
    task_id: str
    status: str = Field(default="running")
    repository_url: str
    context: str
    execution_plan: Optional[ExecutionPlan] = None

class SmartTaskCompletedMessage(BaseModel):
    """Model for smart task completion message."""
    type: str = Field(default="smart_task.completed")
    task_id: str
    results: SmartAnalysisResults
    execution_time: float
    tools_used: List[str]

class ToolCompletedMessage(BaseModel):
    """Model for individual tool completion message."""
    type: str = Field(default="tool.completed")
    task_id: str
    tool_name: str
    tool_result: ToolExecutionResult

class HealthCheck(BaseModel):
    """Model for health check response."""
    status: str = Field(..., description="Service status")
    agent_ready: bool = Field(..., description="Whether the analysis agent is ready")
    version: str = Field(default="1.0.0", description="API version")
    uptime: Optional[float] = Field(None, description="Service uptime in seconds")
    tools_available: Optional[List[str]] = Field(None, description="Available analysis tools")

class ActiveConnectionsInfo(BaseModel):
    """Model for active connections information."""
    active_connections: int = Field(..., description="Number of active WebSocket connections")
    active_tasks: int = Field(..., description="Number of active analysis tasks")
    connection_ids: List[str] = Field(..., description="List of active connection IDs")

class ToolRegistryInfo(BaseModel):
    """Model for tool registry information."""
    total_tools: int
    healthy_tools: int
    capabilities: List[str]
    supported_languages: List[str]
    tools: Dict[str, Dict[str, Any]]

# Intent Analysis Models
class DetectedIntent(BaseModel):
    """Model for a detected analysis intent."""
    type: str = Field(..., description="Type of analysis intent")
    confidence: float = Field(..., ge=0, le=1, description="Confidence score 0-1")
    keywords: List[str] = Field(..., description="Keywords that triggered this intent")
    suggestedScope: str = Field(..., description="Suggested analysis scope")

class IntentAnalysisRequest(BaseModel):
    """Request model for intent analysis."""
    context: str = Field(..., min_length=10, description="User's analysis request in natural language")
    repository: str = Field(..., description="Repository URL for context")
    maxTokens: Optional[int] = Field(200, ge=50, le=1000, description="Maximum tokens for AI response")

class AIAnalysis(BaseModel):
    """Model for AI intent analysis results."""
    intents: List[DetectedIntent] = Field(..., description="List of detected analysis intents")
    complexity: str = Field(..., description="Analysis complexity: simple, moderate, complex")
    recommendation: str = Field(..., description="AI recommendation for analysis approach")
    estimatedTime: str = Field(..., description="Estimated time for analysis")
    suggestedApproach: str = Field(..., description="Suggested analysis approach")


class GitHubServiceStatus(BaseModel):
    """Status of GitHub service availability."""
    available: bool = Field(..., description="Whether GitHub service is available")
    authenticated: bool = Field(..., description="Whether GitHub authentication is valid")
    rate_limit_remaining: Optional[int] = Field(None, description="API rate limit remaining")


