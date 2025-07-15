import { AIAnalysisRequest, AIAnalysisResponse } from "./interface";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export type TaskType = 'explore-codebase' | 'dependency-audit';

// ========================================
// TASK MANAGEMENT INTERFACES
// ========================================

export interface Task {
  id: string;
  title: string;
  description: string;
  status: 'created' | 'started' | 'processing' | 'completed' | 'failed' | 'cancelled';
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
  status: 'started' | 'completed' | 'error';
  result?: StandardToolResponse;
  error?: StandardError;
  started_at?: string;
  completed_at?: string;
}

// ========================================
// STANDARDIZED RESPONSE SCHEMAS (matching backend)
// ========================================

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
  status: 'success' | 'error' | 'partial_success' | 'skipped';
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
  status: 'started' | 'completed' | 'error';
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
  type: 'progress' | 'tool_started' | 'tool_completed' | 'tool_error' | 'analysis_completed' | 'analysis_error';
  task_id: string;
  timestamp: string;
  progress?: ProgressInfo;
  tool?: ToolInfo;
  results?: AnalysisResults;
  ai_message?: string;
  error?: StandardError;
}

export class CipherAPI {
  static async createTask(request: AIAnalysisRequest): Promise<AIAnalysisResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/task/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(`Failed to create AI task: ${response.status} ${response.statusText}${errorData.detail ? ` - ${errorData.detail}` : ''}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating AI task:', error);
      throw error;
    }
  }

  static connectWebSocket(
    websocketUrl: string,
    taskId: string,
    request: AIAnalysisRequest,
    onMessage: (data: StandardWebSocketMessage) => void,
    onError: (error: Event) => void,
    onClose: (event: CloseEvent) => void
  ): WebSocket {
    const ws = new WebSocket(websocketUrl);

    ws.onopen = () => {
      ws.send(JSON.stringify(request));
    };

    ws.onmessage = (event) => {
      try {
        const data: StandardWebSocketMessage = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Error parsing AI WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('AI WebSocket error:', error);
      onError(error);
    };

    ws.onclose = (event) => {
      onClose(event);
    };

    return ws;
  }

  static cancelTask(ws: WebSocket): void {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'cancel' }));
    }
  }
}
