// API service for communicating with the FastAPI backend

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Task type validation
export type TaskType = 'explore-codebase' | 'dependency-audit';

// Legacy types (keeping for backward compatibility)
export interface TaskResponse {
  task_id: string;
  status: string;
  message: string;
  websocket_url: string;
  task_type: string;
  repository_url: string;
  github_pr_enabled: boolean;
}

export interface AnalysisProgress {
  type: 'task.started' | 'task.progress' | 'task.completed' | 'task.error';
  task_id?: string;
  current_step?: string;
  progress?: number;
  partial_results?: {
    file_structure?: Record<string, unknown>;
    language_analysis?: Record<string, unknown>;
    architecture_patterns?: string[];
    main_components?: Record<string, unknown>[];
  };
  results?: {
    summary: string;
    statistics: Record<string, any>;
    detailed_results: {
      whisper_analysis: {
        analysis: string;
        file_structure: Record<string, unknown>;
        language_analysis: Record<string, unknown>;
        architecture_patterns: string[];
        main_components: Record<string, unknown>[];
        dependencies: Record<string, string[]>;
      };
    };
  };
  error?: string;
}

// New Smart Analysis Types
export interface SmartAnalysisRequest {
  repository_url: string;
  context: string;
  intent?: string;
  target_languages?: string[];
  scope?: 'full' | 'security_focused' | 'performance_focused';
  depth?: 'surface' | 'deep' | 'comprehensive';
  additional_params?: Record<string, any>;
}

export interface SmartAnalysisResponse {
  task_id: string;
  status: string;
  message: string;
  websocket_url: string;
  analysis_plan?: ExecutionPlan;
}

export interface ExecutionPlan {
  total_tools: number;
  estimated_total_time: string;
  strategy: string;
  batches: ToolBatch[];
}

export interface ToolBatch {
  tools: string[];
  parallel: boolean;
  estimated_time: string;
}

export interface SmartAnalysisProgress {
  type: 'progress' | 'execution_plan' | 'tool_completed' | 'completed' | 'error';
  task_id?: string;
  current_step?: string;
  progress?: number;
  execution_plan?: ExecutionPlan;
  tool_name?: string;
  tool_result?: ToolExecutionResult;
  results?: SmartAnalysisResults;
  execution_time?: number;
  tools_used?: string[];
  error?: string;
}

export interface ToolExecutionResult {
  tool_name: string;
  success: boolean;
  execution_time: number;
  results: Record<string, any>;
  errors: string[];
  warnings: string[];
  metadata: Record<string, any>;
}

export interface SmartAnalysisResults {
  summary: string;
  execution_info: Record<string, any>;
  tool_results: Record<string, any>;
  vulnerability_summary?: VulnerabilitySummary;
  metrics: Record<string, any>;
  recommendations: string[];
}

export interface VulnerabilitySummary {
  total_vulnerabilities: number;
  critical_vulnerabilities: number;
  high_vulnerabilities: number;
  medium_vulnerabilities: number;
  low_vulnerabilities: number;
  risk_level: string;
  risk_score: number;
  affected_modules: string[];
  recommendations: string[];
}

export interface ToolRegistryInfo {
  total_tools: number;
  healthy_tools: number;
  capabilities: string[];
  supported_languages: string[];
  tools: Record<string, {
    capabilities: string[];
    languages: string[];
    healthy: boolean;
  }>;
}

export interface HealthCheck {
  status: string;
  agent_ready: boolean;
  version: string;
  uptime?: number;
  tools_available?: string[];
}

export class WhisperAPI {
  /**
   * Create a new analysis task (legacy method)
   */
  static async createTask(repositoryUrl: string, taskType: TaskType = 'explore-codebase'): Promise<TaskResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tasks/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          repository_url: repositoryUrl,
          task_type: taskType,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to create task: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating task:', error);
      throw error;
    }
  }

  /**
   * Create a new smart analysis task
   */
  static async createSmartTask(request: SmartAnalysisRequest): Promise<SmartAnalysisResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/smart-tasks/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(`Failed to create smart task: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error creating smart task:', error);
      throw error;
    }
  }

  /**
   * Get task status
   */
  static async getTaskStatus(taskId: string): Promise<Record<string, unknown>> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tasks/${taskId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to get task status: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting task status:', error);
      throw error;
    }
  }

  /**
   * Get tools registry information
   */
  static async getToolsRegistry(): Promise<ToolRegistryInfo> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/tools`);
      
      if (!response.ok) {
        throw new Error(`Failed to get tools registry: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error('Error getting tools registry:', error);
      throw error;
    }
  }

  /**
   * Connect to WebSocket for real-time updates (legacy)
   */
  static connectWebSocket(
    websocketUrl: string,
    taskId: string,
    repositoryUrl: string,
    taskType: TaskType,
    onMessage: (data: AnalysisProgress) => void,
    onError: (error: Event) => void,
    onClose: (event: CloseEvent) => void
  ): WebSocket {
    const ws = new WebSocket(websocketUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      // Send task parameters to start analysis
      ws.send(JSON.stringify({
        repository_url: repositoryUrl,
        task_type: taskType,
      }));
    };

    ws.onmessage = (event) => {
      try {
        const data: AnalysisProgress = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      onError(error);
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed:', event.code, event.reason);
      onClose(event);
    };

    return ws;
  }

  /**
   * Connect to WebSocket for smart analysis real-time updates
   */
  static connectSmartWebSocket(
    websocketUrl: string,
    taskId: string,
    request: SmartAnalysisRequest,
    onMessage: (data: SmartAnalysisProgress) => void,
    onError: (error: Event) => void,
    onClose: (event: CloseEvent) => void
  ): WebSocket {
    const ws = new WebSocket(websocketUrl);

    ws.onopen = () => {
      console.log('Smart WebSocket connected');
      // Send smart task parameters to start analysis
      ws.send(JSON.stringify(request));
    };

    ws.onmessage = (event) => {
      try {
        const data: SmartAnalysisProgress = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Error parsing smart WebSocket message:', error);
      }
    };

    ws.onerror = (error) => {
      console.error('Smart WebSocket error:', error);
      onError(error);
    };

    ws.onclose = (event) => {
      console.log('Smart WebSocket closed:', event.code, event.reason);
      onClose(event);
    };

    return ws;
  }

  /**
   * Cancel a running task
   */
  static cancelTask(ws: WebSocket): void {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'cancel' }));
    }
  }

  /**
   * Check if backend is healthy
   */
  static async healthCheck(): Promise<HealthCheck> {
    try {
      const response = await fetch(`${API_BASE_URL}/health`);
      if (!response.ok) {
        throw new Error(`Health check failed: ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('Backend health check failed:', error);
      throw error;
    }
  }

  /**
   * Check if smart analysis is available
   */
  static async isSmartAnalysisAvailable(): Promise<boolean> {
    try {
      const health = await this.healthCheck();
      return health.agent_ready && (health.tools_available?.length || 0) > 0;
    } catch (error) {
      console.error('Smart analysis availability check failed:', error);
      return false;
    }
  }


}

/**
 * Utility function to validate GitHub repository URL
 */
export function validateGitHubUrl(url: string): boolean {
  const githubUrlPattern = /^https:\/\/github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/?$/;
  return githubUrlPattern.test(url);
}

/**
 * Extract repository name from GitHub URL
 */
export function extractRepoName(url: string): string {
  const match = url.match(/github\.com\/([^\/]+\/[^\/]+)/);
  return match ? match[1] : url;
}

/**
 * Generate context suggestions based on repository information
 */
export function generateContextSuggestions(repoUrl: string, detectedLanguage?: string): string[] {
  const suggestions = [
    'explore this codebase and provide an architectural overview',
    'find security vulnerabilities and provide remediation recommendations',
    'analyze code quality and suggest improvements',
    'review performance bottlenecks and optimization opportunities',
    'check for potential bugs and edge cases',
    'analyze dependencies for security issues and updates needed',
  ];

  // Language-specific suggestions
  if (detectedLanguage) {
    const languageSpecific: Record<string, string[]> = {
      go: [
        'find Go-specific security vulnerabilities in dependencies',
        'analyze Go modules for outdated or vulnerable packages',
        'review Go code for memory leaks and goroutine issues',
      ],
      javascript: [
        'scan npm dependencies for known vulnerabilities',
        'analyze JavaScript code for potential security issues',
        'review Node.js code for performance optimization',
      ],
      python: [
        'check Python dependencies for security vulnerabilities',
        'analyze Python code for potential bugs and best practices',
        'review Django/Flask code for security issues',
      ],
      java: [
        'scan Maven/Gradle dependencies for vulnerabilities',
        'analyze Java code for memory leaks and performance issues',
        'review Spring Boot configuration for security best practices',
      ],
    };

    if (languageSpecific[detectedLanguage.toLowerCase()]) {
      suggestions.push(...languageSpecific[detectedLanguage.toLowerCase()]);
    }
  }

  return suggestions;
} 
