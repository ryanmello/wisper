import { cn, formatTimeAgo, getStatusColor } from "@/lib/utils";
import { Github, Loader2 } from "lucide-react";
import { Task } from "@/lib/api";

interface TaskTabProps {
  tasks: Task[];
  isLoading?: boolean;
  onTaskClick: (taskId: string) => void;
  getProgressDisplay?: (task: Task) => string;
  type: "tasks" | "archived";
}

export function TaskTab({
  tasks,
  isLoading = false,
  onTaskClick,
  getProgressDisplay,
  type,
}: TaskTabProps) {
  const isArchived = type === "archived";

  return (
    <div className="space-y-4">
      {/* Loading State - only for tasks */}
      {isLoading && !isArchived && (
        <div className="flex items-center gap-3 p-4 bg-primary/5 rounded-lg border border-primary/20">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span className="text-sm">Creating new task...</span>
        </div>
      )}

      {/* Empty State */}
      {tasks.length === 0 && !isLoading ? (
        <div className="text-center py-12">
          <h3 className="font-medium text-foreground mb-2">
            {isArchived ? "No archived tasks" : "No active tasks"}
          </h3>
          <p className="text-sm text-muted-foreground">
            {isArchived
              ? "Completed tasks will appear here"
              : "Create your first task by selecting a repository and entering a prompt above"}
          </p>
        </div>
      ) : (
        /* Task List */
        tasks.map((task) => (
          <div
            key={task.id}
            onClick={() => onTaskClick(task.id)}
            className={cn(
              "p-4 bg-card border border-border rounded-xl cursor-pointer transition-all hover:shadow-md hover:border-primary/30 group",
              isArchived && "opacity-75 hover:opacity-100"
            )}
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex-1 min-w-0">
                <h4 className="font-medium text-foreground group-hover:text-primary transition-colors truncate">
                  {task.title}
                </h4>
                <p className="text-sm text-muted-foreground mt-1 line-clamp-2">
                  {task.description}
                </p>

                {/* Progress Bar - only for active processing tasks */}
                {!isArchived &&
                  task.status === "processing" &&
                  task.progress &&
                  getProgressDisplay && (
                    <div className="mt-2">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" />
                        <span>{getProgressDisplay(task)}</span>
                      </div>
                      <div className="mt-1 w-full bg-gray-200 rounded-full h-1">
                        <div
                          className="bg-blue-500 h-1 rounded-full transition-all duration-300"
                          style={{ width: `${task.progress.percentage}%` }}
                        />
                      </div>
                    </div>
                  )}
              </div>

              {/* Status Badge */}
              <div
                className={cn(
                  "ml-3 px-2 py-1 rounded-md text-xs font-medium border",
                  getStatusColor(task.status)
                )}
              >
                {task.status}
              </div>
            </div>

            {/* Task Meta Info */}
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <div className="flex items-center gap-3">
                <span className="flex items-center gap-1">
                  <Github className="w-3 h-3" />
                  {task.repository_name}
                </span>
                <span className="px-1.5 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-700">
                  analysis
                </span>
              </div>
              <span>{formatTimeAgo(task.created_at)}</span>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
