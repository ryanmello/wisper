import { LucideIcon } from "lucide-react";

export interface WaypointNode {
  id: string;
  tool_name: string;
  position: { x: number; y: number };
  data: {
    label: string;
    icon: LucideIcon;
    iconColor: string;
    category: string;
  };
}

export interface WaypointConnection {
  id: string;
  source_id: string;
  source_tool_name: string;
  target_id: string;
  target_tool_name: string;
  sourceHandle?: string;
  targetHandle?: string;
}

export interface VerifyWorkflowRequest {
  nodes: WaypointNode[];
  connections: WaypointConnection[];
}

export interface VerifyWorkflowResponse {
  success: boolean;
  message: string;
}

export interface StartWorkflowRequest {
  repository_url: string;
  nodes: WaypointNode[];
  connections: WaypointConnection[];
}

export interface StartWorkflowResponse {
  task_id: string;
  status: string;
  websocket_url: string;
  message: string;
}

// Tool parameter value types
export type ToolParameterValue = string | number | boolean | string[] | Record<string, string>;

export interface ToolParameter {
  type: string;
  description?: string;
  required?: boolean;
  default?: ToolParameterValue;
}

export interface AvailableToolInfo {
  name: string;
  description: string;
  parameters: Record<string, ToolParameter>;
  category: string;
}

export interface GetToolsResponse {
  tools: AvailableToolInfo[];
}

// Standard metrics structure from backend
export interface StandardMetrics {
  items_processed?: number;
  files_analyzed?: number;
  issues_found?: number;
  execution_time_ms?: number;
}

// Tool-specific result data (varies by tool but common patterns)
export interface ToolResultData {
  action?: string;
  files_modified?: number;
  files_failed?: number;
  files_analyzed?: number;
  issues_found?: number;
  vulnerabilities_found?: number;
  summary?: string;
  // Tool-specific fields can extend this
  [key: string]: string | number | boolean | string[] | undefined;
}

// Execution information structure from backend analysis service
export interface ExecutionInfo {
  user_prompt?: string;
  total_tools_executed: number;
  tools_used: string[];
  timestamp: string;
  workflow_id?: string;
  repository_url?: string;
}

// New interfaces for workflow execution tracking
export type NodeExecutionStatus = 'pending' | 'queued' | 'executing' | 'completed' | 'failed';

export interface NodeExecutionState {
  nodeId: string;
  status: NodeExecutionStatus;
  startTime?: string;
  endTime?: string;
  duration?: number;
  result?: ToolResultData;
  error?: string;
}

export interface WorkflowExecutionState {
  isRunning: boolean;
  currentTool?: string;
  nodeStates: Record<string, NodeExecutionState>;
  overallProgress: number;
  executionOrder: string[];
  results?: AnalysisExecutionInfo;
  error?: string;
}

export interface ToolExecutionResult {
  status: 'started' | 'completed' | 'error';
  result?: ToolResultData;
  error?: Error | string;
}

export interface AnalysisExecutionInfo {
  summary: string;
  execution_info: ExecutionInfo;
}

export interface WebSocketMessage {
  type: 'progress' | 'tool_started' | 'tool_completed' | 'tool_error' | 'analysis_completed' | 'analysis_error';
  task_id: string;
  timestamp: string;
  progress?: {
    percentage: number;
    current_step: string;
    step_number?: number;
    total_steps?: number;
  };
  tool?: {
    name: string;
    status: 'started' | 'completed' | 'error';
    result?: ToolResultData;
    error?: Error | string;
  };
  results?: AnalysisExecutionInfo;
  ai_message?: string;
  error?: {
    message: string;
    details?: string;
    error_type?: string;
  };
}
