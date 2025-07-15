"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import { useTask } from "@/context/task-context";
import { AuthLoadingScreen } from "@/components/AuthLoadingScreen";
import { Chat } from "@/components/cipher/Chat";
import { TaskTab } from "@/components/cipher/TaskTab";
import { Button } from "@/components/ui/button";
import { Fingerprint } from "lucide-react";
import { Task } from "@/lib/api";
import { useAuth } from "@/context/auth-context";

const CipherPage = () => {
  const router = useRouter();

  const { isLoading: isAuthLoading, isAuthenticated } = useAuth();
  const { tasks, archivedTasks, isLoading: isTaskLoading } = useTask();

  const [activeTab, setActiveTab] = useState<"tasks" | "archived">("tasks");

  const handleTaskClick = (taskId: string) => {
    router.push(`/cipher/${taskId}`);
  };

  const getProgressDisplay = (task: Task) => {
    if (task.progress) {
      return `${task.progress.percentage}% - ${task.progress.current_step}`;
    }
    return task.status;
  };

  if (isAuthLoading) return <AuthLoadingScreen />;
  if (!isAuthenticated) return null;

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col pt-32 p-4">
      <div className="w-full max-w-4xl mx-auto">
        {/* Header */}
        <div className="flex items-center justify-center mb-12 gap-2">
          <Fingerprint size={32} />
          <h1 className="text-3xl font-semibold">Cipher</h1>
        </div>

        {/* Chat Component */}
        <Chat isAuthenticated={isAuthenticated} />

        {/* Tasks Section */}
        <div className="mt-8">
          <div className="bg-card rounded-2xl border border-border shadow-sm">
            {/* Tab Headers */}
            <div className="flex border-b border-border">
              <Button
                variant="ghost"
                onClick={() => setActiveTab("tasks")}
                className={cn(
                  "flex-1 px-6 py-6 text-sm font-medium transition-colors rounded-none",
                  "border-b-2 border-transparent",
                  activeTab === "tasks"
                    ? "text-primary border-primary bg-primary/5"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                )}
              >
                Tasks ({tasks.length})
              </Button>
              <Button
                variant="ghost"
                onClick={() => setActiveTab("archived")}
                className={cn(
                  "flex-1 px-6 py-6 text-sm font-medium transition-colors rounded-none",
                  "border-b-2 border-transparent",
                  activeTab === "archived"
                    ? "text-primary border-primary bg-primary/5"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted/50"
                )}
              >
                Archive ({archivedTasks.length})
              </Button>
            </div>

            {/* Tab Content */}
            <div className="p-6">
              {activeTab === "tasks" && (
                <TaskTab
                  tasks={tasks}
                  isLoading={isTaskLoading}
                  onTaskClick={handleTaskClick}
                  getProgressDisplay={getProgressDisplay}
                  type="tasks"
                />
              )}

              {activeTab === "archived" && (
                <TaskTab
                  tasks={archivedTasks}
                  onTaskClick={handleTaskClick}
                  type="archived"
                />
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CipherPage;
