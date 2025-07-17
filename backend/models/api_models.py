from typing import Dict, Any, List, Optional, Literal
from pydantic import BaseModel, Field, field_validator
from services.github_service import github_service
from datetime import datetime

class AIAnalysisRequest(BaseModel):
    """Request model for AI-driven analysis - just repository and prompt!"""
    repository_url: str = Field(..., description="GitHub repository URL")
    prompt: str = Field(..., min_length=10, max_length=1000, description="Natural language prompt describing what you want to analyze")
    
    @field_validator('repository_url')
    @classmethod
    def validate_repository_url(cls, v):
        if github_service.extract_github_repo_path(v) is None:
            raise ValueError("Must be a valid GitHub repository URL")
        return v.rstrip('/')
    
    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v):
        v = v.strip()
        if len(v) < 10:
            raise ValueError('Prompt must be at least 10 characters long')
        if len(v) > 1000:
            raise ValueError('Prompt must be less than 1000 characters')
        return v

class AIAnalysisResponse(BaseModel):
    task_id: str = Field(..., description="Unique task identifier")
    status: str = Field(default="created", description="Task status")
    websocket_url: str = Field(..., description="WebSocket URL for real-time AI orchestration updates")
    message: str = Field(..., description="Status message")

# GitHub API Models
class GitHubRepository(BaseModel):
    """GitHub repository information"""
    id: int = Field(..., description="Repository ID")
    name: str = Field(..., description="Repository name")
    full_name: str = Field(..., description="Full repository name (owner/repo)")
    description: Optional[str] = Field(None, description="Repository description")
    language: Optional[str] = Field(None, description="Primary language")
    stargazers_count: int = Field(..., description="Number of stars")
    forks_count: int = Field(..., description="Number of forks")
    updated_at: str = Field(..., description="Last updated timestamp")
    private: bool = Field(..., description="Whether repository is private")

class GetRepositoriesRequest(BaseModel):
    """Request model for getting user repositories"""
    page: int = Field(1, ge=1, description="Page number for pagination")
    per_page: int = Field(30, ge=1, le=100, description="Number of repositories per page")
    sort: str = Field("updated", description="Sort by: created, updated, pushed, full_name")
    direction: str = Field("desc", description="Sort direction: asc or desc")

class GetRepositoriesResponse(BaseModel):
    """Response model for getting user repositories"""
    total_count: int = Field(..., description="Total number of repositories")
    repositories: List[GitHubRepository] = Field(..., description="List of repositories")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of repositories per page")

class GitHubUser(BaseModel):
    """GitHub user information"""
    login: str = Field(..., description="User login name")
    avatar_url: str = Field(..., description="User avatar URL")

class GitHubLabel(BaseModel):
    """GitHub label information"""
    name: str = Field(..., description="Label name")
    color: str = Field(..., description="Label color")

class GitHubPullRequest(BaseModel):
    """GitHub pull request information"""
    id: int = Field(..., description="Pull request number")
    title: str = Field(..., description="Pull request title")
    state: str = Field(..., description="Pull request state")
    repository: Dict[str, str] = Field(..., description="Repository information")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last updated timestamp")
    html_url: str = Field(..., description="GitHub URL")
    user: GitHubUser = Field(..., description="Pull request author")
    comments: int = Field(..., description="Number of comments")
    labels: List[GitHubLabel] = Field(..., description="Pull request labels")

class GetPullRequestsRequest(BaseModel):
    """Request model for getting pull requests"""
    repo_owner: str = Field(..., description="Repository owner")
    repo_name: str = Field(..., description="Repository name")
    page: int = Field(1, ge=1, description="Page number for pagination")
    per_page: int = Field(30, ge=1, le=100, description="Number of PRs per page")
    state: str = Field("open", description="State of PRs: open, closed, or all")

class GetPullRequestsResponse(BaseModel):
    """Response model for getting pull requests"""
    total_count: int = Field(..., description="Total number of pull requests")
    items: List[GitHubPullRequest] = Field(..., description="List of pull requests")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of pull requests per page")

class GitHubFileChange(BaseModel):
    """GitHub file change information"""
    filename: str = Field(..., description="File name")
    status: str = Field(..., description="File status: added, modified, removed, renamed")
    additions: int = Field(..., description="Number of additions")
    deletions: int = Field(..., description="Number of deletions")
    changes: int = Field(..., description="Total number of changes")
    patch: str = Field("", description="File patch/diff")
    previous_filename: Optional[str] = Field(None, description="Previous filename if renamed")
    blob_url: str = Field(..., description="Blob URL")
    raw_url: str = Field(..., description="Raw file URL")

class GetPullRequestFilesRequest(BaseModel):
    """Request model for getting pull request files"""
    pr_id: int = Field(..., description="Pull request ID")
    repo_owner: str = Field(..., description="Repository owner")
    repo_name: str = Field(..., description="Repository name")

class GetPullRequestFilesResponse(BaseModel):
    """Response model for getting pull request files"""
    pr_id: int = Field(..., description="Pull request ID")
    repository: str = Field(..., description="Repository full name")
    files: List[GitHubFileChange] = Field(..., description="List of file changes")
    total_files: int = Field(..., description="Total number of files")

class GitHubComment(BaseModel):
    """GitHub comment information"""
    id: int = Field(..., description="Comment ID")
    body: str = Field(..., description="Comment body")
    user: GitHubUser = Field(..., description="Comment author")
    created_at: str = Field(..., description="Creation timestamp")
    updated_at: str = Field(..., description="Last updated timestamp")
    html_url: str = Field(..., description="GitHub URL")

class GetPullRequestCommentsRequest(BaseModel):
    """Request model for getting pull request comments"""
    pr_id: int = Field(..., description="Pull request ID")
    repo_owner: str = Field(..., description="Repository owner")
    repo_name: str = Field(..., description="Repository name")
    page: int = Field(1, ge=1, description="Page number for pagination")
    per_page: int = Field(30, ge=1, le=100, description="Number of comments per page")

class GetPullRequestCommentsResponse(BaseModel):
    """Response model for getting pull request comments"""
    pr_id: int = Field(..., description="Pull request ID")
    repository: str = Field(..., description="Repository full name")
    comments: List[GitHubComment] = Field(..., description="List of comments")
    page: int = Field(..., description="Current page number")
    per_page: int = Field(..., description="Number of comments per page")

class PostPullRequestCommentRequest(BaseModel):
    """Request model for posting pull request comment"""
    pr_id: int = Field(..., description="Pull request ID")
    repo_owner: str = Field(..., description="Repository owner")
    repo_name: str = Field(..., description="Repository name")
    body: str = Field(..., min_length=1, description="Comment body")

class PostPullRequestCommentResponse(BaseModel):
    """Response model for posting pull request comment"""
    comment: GitHubComment = Field(..., description="Created comment")

# Waypoint
class WaypointNode(BaseModel):
    id: str
    tool_name: str

class WaypointConnection(BaseModel):
    id: str
    source_id: str
    source_tool_name: str
    target_id: str
    target_tool_name: str

class VerifyConfigurationRequest(BaseModel):
    nodes: List[WaypointNode] = Field(..., description="")
    connections: List[WaypointConnection] = Field(..., description="")

class VerifyConfigurationResponse(BaseModel):
    success: bool = Field(..., description="Represents a valid configuration")
    message: str = Field(..., description="Human-readable message about the validation result")

class StandardError(BaseModel):
    """Standardized error information"""
    message: str = Field(..., description="Human-readable error message")
    details: Optional[str] = Field(None, description="Technical error details")
    error_type: Optional[str] = Field(None, description="Error category/type")

class StandardMetrics(BaseModel):
    """Standard metrics that tools can provide"""
    items_processed: Optional[int] = Field(None, description="Number of items processed")
    files_analyzed: Optional[int] = Field(None, description="Number of files analyzed")
    issues_found: Optional[int] = Field(None, description="Number of issues/problems found")
    execution_time_ms: Optional[int] = Field(None, description="Tool execution time in milliseconds")

class StandardToolResponse(BaseModel):
    """Standardized response format for all tools"""
    # Execution metadata (consistent across all tools)
    status: Literal["success", "error", "partial_success", "skipped"] = Field(..., description="Tool execution status")
    tool_name: str = Field(..., description="Name of the tool that was executed")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="ISO 8601 timestamp")
    
    # Result data (tool-specific content)
    data: Any = Field(None, description="Tool-specific results and findings")
    
    # Error handling (when status is error/partial_success)
    error: Optional[StandardError] = Field(None, description="Error details if execution failed")
    
    # Success metadata
    summary: Optional[str] = Field(None, description="Human-readable summary of what was accomplished")
    metrics: Optional[StandardMetrics] = Field(None, description="Quantitative metrics about the execution")
    
    # Warnings/info (non-blocking issues)
    warnings: Optional[List[str]] = Field(None, description="Non-blocking warnings or information")

class ProgressInfo(BaseModel):
    """Progress tracking information"""
    percentage: int = Field(..., ge=0, le=100, description="Progress percentage (0-100)")
    current_step: str = Field(..., description="Description of current step")
    total_steps: Optional[int] = Field(None, description="Total number of steps")
    step_number: Optional[int] = Field(None, description="Current step number")

class ToolInfo(BaseModel):
    """Information about tool execution"""
    name: str = Field(..., description="Tool name")
    status: Literal["started", "completed", "error"] = Field(..., description="Tool execution status")
    result: Optional[StandardToolResponse] = Field(None, description="Tool result (only present when completed)")
    error: Optional[StandardError] = Field(None, description="Error details (only present when error)")

class AnalysisResults(BaseModel):
    """Final analysis results"""
    summary: str = Field(..., description="Overall analysis summary")
    execution_info: Dict[str, Any] = Field(..., description="Execution metadata")

class StandardWebSocketMessage(BaseModel):
    """Standardized WebSocket message format"""
    type: Literal["progress", "tool_started", "tool_completed", "tool_error", "analysis_completed", "analysis_error"] = Field(..., description="Message type")
    task_id: str = Field(..., description="Task identifier")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="ISO 8601 timestamp")
    progress: Optional[ProgressInfo] = Field(None, description="Progress information")
    tool: Optional[ToolInfo] = Field(None, description="Tool execution information")
    results: Optional[AnalysisResults] = Field(None, description="Final analysis results")    
    ai_message: Optional[str] = Field(None, description="AI-generated explanation or reasoning")
    error: Optional[StandardError] = Field(None, description="Error information")

# Simplified Orchestrator Update Models (keeping for backward compatibility)
class ExecutionMetadata(BaseModel):
    """Metadata about the current execution state"""
    turn: Optional[int] = Field(None, description="Current conversation turn")
    total_turns: Optional[int] = Field(None, description="Total conversation turns")
    total_api_calls: Optional[int] = Field(None, description="Total API calls made")
    tools_executed: Optional[int] = Field(None, description="Number of tools executed")
    tool_name: Optional[str] = Field(None, description="Current/relevant tool name")
    completion_reason: Optional[str] = Field(None, description="Reason for completion")

class PRCreationResult(BaseModel):
    """Result of Pull Request creation operation"""
    success: bool = Field(..., description="Whether PR creation succeeded")
    pr_url: Optional[str] = Field(None, description="URL of created pull request")
    pr_number: Optional[int] = Field(None, description="Pull request number")
    branch_name: Optional[str] = Field(None, description="Branch name used for PR")
    files_changed: List[str] = Field(default_factory=list, description="List of files modified")
    vulnerabilities_fixed: int = Field(default=0, description="Number of vulnerabilities fixed")
    error_message: Optional[str] = Field(None, description="Error message if creation failed")

class OrchestratorUpdate(BaseModel):
    """Unified update model for all orchestrator communications"""
    type: Literal["status", "content", "error", "completed"] = Field(..., description="Type of update")
    message: str = Field(..., description="Human-readable message about what's happening")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional structured data")
    metadata: Optional[ExecutionMetadata] = Field(None, description="Execution context metadata")
    
    @classmethod
    def status(cls, message: str, **metadata_kwargs) -> "OrchestratorUpdate":
        """Create a status update (progress, tool execution, etc.)"""
        metadata = ExecutionMetadata(**metadata_kwargs) if metadata_kwargs else None
        return cls(type="status", message=message, metadata=metadata)
    
    @classmethod
    def content(cls, message: str, data: Optional[Dict[str, Any]] = None, **metadata_kwargs) -> "OrchestratorUpdate":
        """Create a content update (AI responses, explanations)"""
        metadata = ExecutionMetadata(**metadata_kwargs) if metadata_kwargs else None
        return cls(type="content", message=message, data=data, metadata=metadata)
    
    @classmethod
    def error(cls, message: str, error_details: Optional[str] = None, **metadata_kwargs) -> "OrchestratorUpdate":
        """Create an error update"""
        metadata = ExecutionMetadata(**metadata_kwargs) if metadata_kwargs else None
        data = {"error_details": error_details} if error_details else None
        return cls(type="error", message=message, data=data, metadata=metadata)
    
    @classmethod
    def completed(cls, message: str, final_results: Dict[str, Any], **metadata_kwargs) -> "OrchestratorUpdate":
        """Create a completion update with final results"""
        metadata = ExecutionMetadata(**metadata_kwargs) if metadata_kwargs else None
        return cls(type="completed", message=message, data=final_results, metadata=metadata)
