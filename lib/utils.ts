import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { Task, ToolResult } from "./api";
import { AIAnalysisRequest, AIAnalysisResponse } from "./interface";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function extractRepositoryName(repositoryUrl: string): string {
  try {
    const url = new URL(repositoryUrl);
    const pathParts = url.pathname.split('/').filter(Boolean);
    if (pathParts.length >= 2) {
      return `${pathParts[0]}/${pathParts[1]}`;
    }
    return repositoryUrl;
  } catch {
    return repositoryUrl;
  }
}

export function formatTimeAgo(dateString: string): string {
  const date = new Date(dateString);
  const now = new Date();
  const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60));

  if (diffInMinutes < 1) return 'just now';
  if (diffInMinutes < 60) return `${diffInMinutes}m ago`;

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) return `${diffInHours}h ago`;

  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 30) return `${diffInDays}d ago`;

  const diffInMonths = Math.floor(diffInDays / 30);
  return `${diffInMonths}mo ago`;
}

export function getStatusColor(status: Task['status']): string {
  const colors = {
    created: 'bg-gray-100 text-gray-700 border-gray-200',
    started: 'bg-blue-100 text-blue-700 border-blue-200',
    processing: 'bg-blue-100 text-blue-700 border-blue-200',
    completed: 'bg-green-100 text-green-700 border-green-200',
    failed: 'bg-red-100 text-red-700 border-red-200',
    cancelled: 'bg-gray-100 text-gray-700 border-gray-200',
  };
  return colors[status] || colors.created;
}

export function generateTaskTitle(prompt: string): string {
  const title = prompt.trim().substring(0, 50);
  return title.length < prompt.trim().length ? `${title}...` : title;
}

export function createTaskFromResponse(
  response: AIAnalysisResponse,
  request: AIAnalysisRequest
): Task {
  const now = new Date().toISOString();
  return {
    id: response.task_id,
    title: generateTaskTitle(request.prompt),
    description: request.prompt,
    status: 'created',
    repository_url: request.repository_url,
    repository_name: extractRepositoryName(request.repository_url),
    prompt: request.prompt,
    created_at: now,
    updated_at: now,
    websocket_url: response.websocket_url,
    progress: {
      percentage: 0,
      current_step: 'Task created',
      step_number: 0,
      total_steps: 1
    },
    tool_results: [],
    ai_messages: []
  };
}

export function updateToolResults(
  currentResults: ToolResult[],
  toolName: string,
  updates: Partial<ToolResult>
): ToolResult[] {
  const existingIndex = currentResults.findIndex(
    (result) => result.name === toolName
  );

  if (existingIndex >= 0) {
    // Update existing tool result
    const updatedResults = [...currentResults];
    updatedResults[existingIndex] = {
      ...updatedResults[existingIndex],
      ...updates,
    };
    return updatedResults;
  } else {
    // Add new tool result
    return [...currentResults, { name: toolName, ...updates } as ToolResult];
  }
}
