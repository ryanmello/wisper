"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTask } from "@/context/task-context";
import { AuthLoadingScreen } from "@/components/AuthLoadingScreen";
import {
  Fingerprint,
  ArrowLeft,
  Clock,
  CheckCircle,
  XCircle,
  AlertCircle,
  Github,
  Play,
  Pause,
  ExternalLink,
  FileText,
  Zap,
  Target,
  AlertTriangle,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Switch } from "@/components/ui/switch";
import { cn, formatTimeAgo, getStatusColor } from "@/lib/utils";
import { useAuth } from "@/context/auth-context";
import { Task, ToolResult } from "@/lib/interface/cipher-interface";

interface TaskPageProps {
  params: Promise<{ taskId: string }>;
}

const TaskDetailPage = ({ params }: TaskPageProps) => {
  const { isLoading: isAuthLoading, isAuthenticated } = useAuth();
  const {
    getTaskById,
    cancelTask,
    archiveTask,
    unarchiveTask,
    deleteTask,
    archivedTasks,
  } = useTask();
  const router = useRouter();
  const [taskId, setTaskId] = useState<string>("");
  const [task, setTask] = useState<Task | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const getTaskId = async () => {
      const resolvedParams = await params;
      setTaskId(resolvedParams.taskId);
    };
    getTaskId();
  }, [params]);

  useEffect(() => {
    if (taskId) {
      const foundTask = getTaskById(taskId);
      setTask(foundTask);
      setIsLoading(false);
    }
  }, [taskId, getTaskById]);

  // Auto-refresh for running tasks
  useEffect(() => {
    if (task && (task.status === "processing" || task.status === "started")) {
      const interval = setInterval(() => {
        const updatedTask = getTaskById(taskId);
        if (updatedTask) {
          setTask(updatedTask);
        }
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [task, taskId, getTaskById]);

  const handleCancel = () => {
    if (task) {
      cancelTask(task.id);
    }
  };

  const handleArchiveToggle = (checked: boolean) => {
    if (task) {
      if (checked) {
        archiveTask(task.id);
      } else {
        unarchiveTask(task.id);
      }
    }
  };

  const handleDelete = () => {
    if (task) {
      deleteTask(task.id);
      router.push("/cipher");
    }
  };

  // Check if task is archived
  const isTaskArchived = task
    ? archivedTasks.some((archivedTask) => archivedTask.id === task.id)
    : false;

  const getStatusIcon = (status: Task["status"]) => {
    const iconProps = { className: "w-5 h-5" };
    switch (status) {
      case "created":
        return <Clock {...iconProps} className="w-5 h-5 text-gray-500" />;
      case "started":
      case "processing":
        return <Play {...iconProps} className="w-5 h-5 text-blue-500" />;
      case "completed":
        return (
          <CheckCircle {...iconProps} className="w-5 h-5 text-green-500" />
        );
      case "failed":
        return <XCircle {...iconProps} className="w-5 h-5 text-red-500" />;
      case "cancelled":
        return <Pause {...iconProps} className="w-5 h-5 text-gray-500" />;
      default:
        return <Clock {...iconProps} className="w-5 h-5 text-gray-500" />;
    }
  };

  const getToolStatusIcon = (status: ToolResult["status"]) => {
    const iconProps = { className: "w-4 h-4" };
    switch (status) {
      case "started":
        return <Play {...iconProps} className="w-4 h-4 text-blue-500" />;
      case "completed":
        return (
          <CheckCircle {...iconProps} className="w-4 h-4 text-green-500" />
        );
      case "error":
        return <XCircle {...iconProps} className="w-4 h-4 text-red-500" />;
      default:
        return <Clock {...iconProps} className="w-4 h-4 text-gray-500" />;
    }
  };

  const renderToolResults = () => {
    if (!task?.tool_results || task.tool_results.length === 0) {
      return (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Zap className="w-5 h-5" />
              Tool Execution
            </CardTitle>
            <CardDescription>
              No tool execution data available yet
            </CardDescription>
          </CardHeader>
        </Card>
      );
    }

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5" />
            Tool Execution ({task.tool_results.length})
          </CardTitle>
          <CardDescription>
            Tools executed as part of this analysis
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {task.tool_results.map((tool, index) => (
              <div key={index} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    {getToolStatusIcon(tool.status)}
                    <span className="font-medium">{tool.name}</span>
                  </div>
                  <Badge
                    className={cn(
                      "text-xs",
                      tool.status === "completed" &&
                        "bg-green-100 text-green-700",
                      tool.status === "started" && "bg-blue-100 text-blue-700",
                      tool.status === "error" && "bg-red-100 text-red-700"
                    )}
                  >
                    {tool.status}
                  </Badge>
                </div>

                {tool.started_at && (
                  <div className="text-sm text-muted-foreground mb-2">
                    Started: {formatTimeAgo(tool.started_at)}
                    {tool.completed_at &&
                      ` • Completed: ${formatTimeAgo(tool.completed_at)}`}
                  </div>
                )}

                {tool.result && (
                  <div className="mt-3 p-3 bg-muted/50 rounded text-sm">
                    <div className="font-medium mb-1">Result:</div>
                    {tool.result.summary && (
                      <p className="text-muted-foreground">
                        {tool.result.summary}
                      </p>
                    )}
                    {tool.result.metrics && (
                      <div className="mt-2 grid grid-cols-2 gap-2 text-xs">
                        {tool.result.metrics.items_processed && (
                          <div>
                            Items processed:{" "}
                            {tool.result.metrics.items_processed}
                          </div>
                        )}
                        {tool.result.metrics.files_analyzed && (
                          <div>
                            Files analyzed: {tool.result.metrics.files_analyzed}
                          </div>
                        )}
                        {tool.result.metrics.issues_found && (
                          <div>
                            Issues found: {tool.result.metrics.issues_found}
                          </div>
                        )}
                        {tool.result.metrics.execution_time_ms && (
                          <div>
                            Execution time:{" "}
                            {tool.result.metrics.execution_time_ms}ms
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {tool.error && (
                  <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-sm">
                    <div className="font-medium text-red-700 mb-1">Error:</div>
                    <p className="text-red-600">{tool.error.message}</p>
                    {tool.error.details && (
                      <p className="text-red-500 text-xs mt-1">
                        {tool.error.details}
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderAnalysisResults = () => {
    if (!task?.final_results) {
      return null;
    }

    const results = task.final_results;

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Target className="w-5 h-5" />
            Analysis Results
          </CardTitle>
          <CardDescription>Final analysis summary and findings</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Summary */}
            <div>
              <h4 className="font-medium mb-2">Summary</h4>
              <p className="text-muted-foreground">{results.summary}</p>
            </div>

            {/* Recommendations */}
            {results.recommendations && results.recommendations.length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Recommendations</h4>
                <ul className="space-y-1">
                  {results.recommendations.map((rec, index) => (
                    <li
                      key={index}
                      className="text-sm text-muted-foreground flex items-start gap-2"
                    >
                      <span className="text-primary">•</span>
                      {rec}
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {/* Metrics */}
            {results.metrics && Object.keys(results.metrics).length > 0 && (
              <div>
                <h4 className="font-medium mb-2">Metrics</h4>
                <div className="grid grid-cols-2 gap-4 text-sm">
                  {Object.entries(results.metrics).map(([key, value]) => (
                    <div key={key} className="flex justify-between">
                      <span className="text-muted-foreground">{key}:</span>
                      <span className="font-medium">{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Execution Info */}
            {results.execution_info && (
              <details className="mt-4">
                <summary className="font-medium cursor-pointer text-sm">
                  Execution Details
                </summary>
                <div className="mt-2 p-3 bg-muted/50 rounded text-xs">
                  <pre className="whitespace-pre-wrap">
                    {JSON.stringify(results.execution_info, null, 2)}
                  </pre>
                </div>
              </details>
            )}
          </div>
        </CardContent>
      </Card>
    );
  };

  const renderAIMessages = () => {
    if (!task?.ai_messages || task.ai_messages.length === 0) {
      return null;
    }

    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <FileText className="w-5 h-5" />
            AI Insights
          </CardTitle>
          <CardDescription>
            Real-time AI analysis and explanations
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            {task.ai_messages.map((message, index) => (
              <div key={index} className="p-3 bg-muted/50 rounded-lg text-sm">
                {message}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    );
  };

  useEffect(() => {
    if (!isAuthLoading && !isAuthenticated) {
      router.push('/sign-in');
    }
  }, [isAuthLoading, isAuthenticated, router]);

  if (isAuthLoading) return <AuthLoadingScreen />;
  if (!isAuthenticated) return <AuthLoadingScreen />;

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-muted-foreground">Loading task details...</p>
        </div>
      </div>
    );
  }

  if (!task) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center">
        <div className="text-center">
          <AlertTriangle className="w-16 h-16 text-muted-foreground mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">Task Not Found</h2>
          <p className="text-muted-foreground mb-4">
            The task you're looking for doesn't exist.
          </p>
          <Button onClick={() => router.push("/cipher")} variant="outline">
            <ArrowLeft className="w-4 h-4 mr-2" />
            Back to Tasks
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 p-4">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <Button
              variant="ghost"
              size="icon"
              onClick={() => router.push("/cipher")}
            >
              <ArrowLeft className="w-4 h-4" />
            </Button>
            <div className="flex items-center gap-4">
              <Fingerprint className="w-6 h-6" />
              <h1 className="text-xl font-semibold">Task Details</h1>
            </div>
          </div>

          <div className="flex items-center gap-4">
            {(task.status === "processing" || task.status === "started") && (
              <Button variant="outline" size="sm" onClick={handleCancel}>
                <Pause className="w-4 h-4 mr-2" />
                Cancel
              </Button>
            )}

            {["failed", "cancelled"].includes(task.status) && (
              <Button variant="outline" size="sm" onClick={handleDelete}>
                Delete
              </Button>
            )}

            {/* Archive toggle for completed, failed, and cancelled tasks */}
            {["completed", "failed", "cancelled"].includes(task.status) && (
              <div className="flex items-center gap-2">
                <label
                  htmlFor="archive-toggle"
                  className="text-sm font-medium leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70"
                >
                  {isTaskArchived ? "Archived" : "Archive"}
                </label>
                <Switch
                  checked={isTaskArchived}
                  onCheckedChange={handleArchiveToggle}
                  id="archive-toggle"
                />
              </div>
            )}
          </div>
        </div>

        {/* Task Info Card */}
        <Card className="mb-6">
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <CardTitle className="flex items-center gap-2 mb-2">
                  {getStatusIcon(task.status)}
                  {task.title}
                </CardTitle>
                <CardDescription>{task.description}</CardDescription>
              </div>
              <Badge className={cn("ml-4", getStatusColor(task.status))}>
                {task.status}
              </Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <div className="flex items-center gap-2 text-sm text-muted-foreground mb-1">
                  <Github className="w-4 h-4" />
                  Repository
                </div>
                <div className="flex items-center gap-2">
                  <span className="font-medium">{task.repository_name}</span>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => window.open(task.repository_url, "_blank")}
                  >
                    <ExternalLink className="w-3 h-3" />
                  </Button>
                </div>
              </div>

              <div>
                <div className="text-sm text-muted-foreground mb-1">
                  Timeline
                </div>
                <div className="space-y-1 text-sm">
                  <div>Created: {formatTimeAgo(task.created_at)}</div>
                  {task.updated_at !== task.created_at && (
                    <div>Updated: {formatTimeAgo(task.updated_at)}</div>
                  )}
                </div>
              </div>
            </div>

            {/* Progress Bar */}
            {task.progress &&
              (task.status === "processing" || task.status === "started") && (
                <div className="mt-4">
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">Progress</span>
                    <span className="text-sm text-muted-foreground">
                      {task.progress.percentage}%
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${task.progress.percentage}%` }}
                    />
                  </div>
                  <div className="text-sm text-muted-foreground mt-1">
                    {task.progress.current_step}
                    {task.progress.step_number && task.progress.total_steps && (
                      <span className="ml-2">
                        (Step {task.progress.step_number} of{" "}
                        {task.progress.total_steps})
                      </span>
                    )}
                  </div>
                </div>
              )}

            {/* Error Display */}
            {task.error && (
              <div className="mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <div className="flex items-center gap-2 mb-2">
                  <AlertCircle className="w-4 h-4 text-red-500" />
                  <span className="font-medium text-red-700">Error</span>
                </div>
                <p className="text-red-600 text-sm">{task.error.message}</p>
                {task.error.details && (
                  <p className="text-red-500 text-xs mt-1">
                    {task.error.details}
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Results Sections */}
        <div className="space-y-6">
          {/* AI Messages */}
          {renderAIMessages()}

          {/* Tool Results */}
          {renderToolResults()}

          {/* Final Results */}
          {renderAnalysisResults()}
        </div>
      </div>
    </div>
  );
};

export default TaskDetailPage;
