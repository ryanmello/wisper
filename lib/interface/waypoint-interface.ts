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

export interface AvailableToolInfo {
  name: string;
  description: string;
  parameters: Record<string, any>;
  category: string;
}

export interface GetToolsResponse {
  tools: AvailableToolInfo[];
}

// New interfaces for workflow execution tracking
export type NodeExecutionStatus = 'pending' | 'queued' | 'executing' | 'completed' | 'failed';

export interface NodeExecutionState {
  nodeId: string;
  status: NodeExecutionStatus;
  startTime?: string;
  endTime?: string;
  duration?: number;
  result?: any;
  error?: string;
}

export interface WorkflowExecutionState {
  isRunning: boolean;
  currentTool?: string;
  nodeStates: Record<string, NodeExecutionState>;
  overallProgress: number;
  executionOrder: string[];
  results?: any;
  error?: string;
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
    result?: any;
    error?: any;
  };
  results?: {
    summary: string;
    execution_info: any;
  };
  ai_message?: string;
  error?: {
    message: string;
    details?: string;
    error_type?: string;
  };
}
