import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import React from "react";
import { CipherRequest, CipherResponse, Task, ToolResult } from "./interface/cipher-interface";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

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

export const getLanguageColor = (language: string | null) => {
  if (!language) return "bg-gray-500";
  const colors: Record<string, string> = {
    TypeScript: "bg-blue-500",
    JavaScript: "bg-purple-500",
    Python: "bg-yellow-500",
    Java: "bg-orange-500",
    Go: "bg-cyan-500",
    Rust: "bg-red-500",
    "C++": "bg-green-500",
    "C#": "bg-purple-600",
    PHP: "bg-indigo-500",
    Ruby: "bg-red-600",
  };
  return colors[language] || "bg-gray-500";
};

export function generateTaskTitle(prompt: string): string {
  const title = prompt.trim().substring(0, 50);
  return title.length < prompt.trim().length ? `${title}...` : title;
}

export function createTaskFromResponse(
  response: CipherResponse,
  request: CipherRequest
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

export const formatSummaryText = (text: string): React.ReactNode[] | null => {
  if (!text) return null;
  
  const lines = text.split('\n').filter(line => line.trim());
  const elements: React.ReactNode[] = [];
  
  lines.forEach((line, index) => {
    const trimmed = line.trim();
    
    // Main headers (###)
    if (trimmed.startsWith('### ')) {
      elements.push(
        React.createElement('h3', {
          key: index,
          className: "text-lg font-bold mt-4 mb-2 first:mt-0"
        }, trimmed.replace('### ', ''))
      );
    }
    // Sub headers (####)
    else if (trimmed.startsWith('#### ')) {
      elements.push(
        React.createElement('h4', {
          key: index,
          className: "text-base font-semibold mt-3 mb-2"
        }, trimmed.replace('#### ', ''))
      );
    }
    // Horizontal rules
    else if (trimmed === '---') {
      elements.push(
        React.createElement('hr', {
          key: index,
          className: "my-4"
        })
      );
    }
    // Numbered lists
    else if (/^\d+\.\s/.test(trimmed)) {
      elements.push(
        React.createElement('div', {
          key: index,
          className: "ml-4 mb-1"
        }, React.createElement('span', {
          className: "font-medium"
        }, trimmed))
      );
    }
    // Bullet points with dashes
    else if (trimmed.startsWith('- ')) {
      elements.push(
        React.createElement('div', {
          key: index,
          className: "ml-6 mb-1 flex items-start gap-2"
        }, [
          React.createElement('div', {
            key: 'bullet',
            className: "w-1 h-1 rounded-full mt-2 flex-shrink-0"
          }),
          React.createElement('span', {
            key: 'text',
          }, trimmed.replace('- ', ''))
        ])
      );
    }
    // Bold text patterns
    else if (trimmed.includes('**')) {
      const parts = trimmed.split('**');
      const formattedParts = parts.map((part, i) => 
        i % 2 === 1 ? React.createElement('strong', { key: i, className: "font-semibold" }, part) : part
      );
      elements.push(
        React.createElement('p', {
          key: index,
          className: "mb-2"
        }, formattedParts)
      );
    }
    // Regular paragraphs
    else if (trimmed.length > 0) {
      elements.push(
        React.createElement('p', {
          key: index,
          className: "mb-2"
        }, trimmed)
      );
    }
  });
  
  return elements;
};
