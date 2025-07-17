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

export interface AIAnalysisRequest {
  repository_url: string;
  prompt: string;
}

export interface AIAnalysisResponse {
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

export interface StandardToolResponse {
  status: "success" | "error" | "partial_success" | "skipped";
  tool_name: string;
  timestamp: string;
  data?: any;
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
  execution_info: Record<string, any>;
  tool_results: Record<string, StandardToolResponse>;
  metrics: Record<string, any>;
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
