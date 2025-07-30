export interface Task {
  id: string;
  title: string;
  description: string;
  status:
    | "created"
    | "started"
    | "processing"
    | "completed"
    | "failed"
    | "cancelled";
  repository_url: string;
  repository_name: string;
  prompt: string;
  created_at: string;
  updated_at: string;
  websocket_url?: string;
  progress?: ProgressInfo;
  tool_results?: ToolResult[];
  final_results?: AnalysisResults;
  error?: StandardError;
  ai_messages?: string[];
}

export interface ToolResult {
  name: string;
  status: "started" | "completed" | "error";
  result?: StandardToolResponse;
  error?: StandardError;
  started_at?: string;
  completed_at?: string;
}

export interface CipherRequest {
  repository_url: string;
  prompt: string;
}

export interface CipherResponse {
  task_id: string;
  status: string;
  websocket_url: string;
  message: string;
}

export interface StandardError {
  message: string;
  details?: string;
  error_type?: string;
}

export interface StandardMetrics {
  items_processed?: number;
  files_analyzed?: number;
  issues_found?: number;
  execution_time_ms?: number;
}

// Tool-specific result data (varies by tool but follows common patterns)
export interface ToolResponseData {
  action?: string;
  files_modified?: number;
  files_failed?: number;
  files_analyzed?: number;
  issues_found?: number;
  vulnerabilities_found?: number;
  dependencies?: Record<string, string[]>;
  languages?: Record<string, number>;
  frameworks?: string[];
  architecture_patterns?: string[];
  summary?: string;
  // Allow tool-specific fields
  [key: string]: string | number | boolean | string[] | Record<string, any> | undefined;
}

// Analysis execution information from backend
export interface AnalysisExecutionInfo {
  user_prompt: string;
  total_tools_executed: number;
  tools_used: string[];
  timestamp: string;
  task_id?: string;
  repository_url?: string;
}

// Analysis metrics from completed tasks
export interface AnalysisMetrics {
  total_files_processed: number;
  total_issues_found: number;
  execution_time_seconds: number;
  tools_executed: number;
  vulnerabilities_found?: number;
  dependencies_analyzed?: number;
}

export interface StandardToolResponse {
  status: "success" | "error" | "partial_success" | "skipped";
  tool_name: string;
  timestamp: string;
  data?: ToolResponseData;
  error?: StandardError;
  summary?: string;
  metrics?: StandardMetrics;
  warnings?: string[];
}

export interface ProgressInfo {
  percentage: number;
  current_step: string;
  total_steps?: number;
  step_number?: number;
}

export interface ToolInfo {
  name: string;
  status: "started" | "completed" | "error";
  result?: StandardToolResponse;
  error?: StandardError;
}

export interface AnalysisResults {
  summary: string;
  execution_info: AnalysisExecutionInfo;
  tool_results: Record<string, StandardToolResponse>;
  metrics: AnalysisMetrics;
  recommendations: string[];
}

export interface StandardWebSocketMessage {
  type:
    | "progress"
    | "tool_started"
    | "tool_completed"
    | "tool_error"
    | "analysis_completed"
    | "analysis_error";
  task_id: string;
  timestamp: string;
  progress?: ProgressInfo;
  tool?: ToolInfo;
  results?: AnalysisResults;
  ai_message?: string;
  error?: StandardError;
}
