"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { WhisperAPI, AnalysisProgress, TaskType, extractRepoName } from "@/lib/api";

interface TaskExecutionProps {
  repository: string;
  task: TaskType;
  onBack: () => void;
  onComplete?: (results: AnalysisProgress['results']) => void;
}

// Task configuration
const taskConfig: Record<string, {
  title: string;
  icon: string;
  description: string;
}> = {
  "explore-codebase": {
    title: "Explore Codebase",
    icon: "🔍",
    description: "AI-powered comprehensive codebase analysis",
  },
  "dependency-audit": {
    title: "Dependency Audit",
    icon: "📦",
    description: "Analyze security vulnerabilities and create PR with fixes",
  },
};

export default function TaskExecution({ repository, task, onBack, onComplete }: TaskExecutionProps) {
  const [currentStep, setCurrentStep] = useState<string>("Initializing...");
  const [isCompleted, setIsCompleted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(true);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [startTime, setStartTime] = useState<Date | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const taskInfo = taskConfig[task] || taskConfig["explore-codebase"];

  useEffect(() => {
    let mounted = true;

    const startAnalysis = async () => {
      try {
        setIsConnecting(true);
        setError(null);

        const taskResponse = await WhisperAPI.createTask(repository, task);
        
        if (!mounted) return;
        
        setTaskId(taskResponse.task_id);
        setCurrentStep("Connecting to analysis service...");

        const ws = WhisperAPI.connectWebSocket(
          taskResponse.websocket_url,
          taskResponse.task_id,
          repository,
          task,
          (data: AnalysisProgress) => {
            if (!mounted) return;

            switch (data.type) {
              case 'task.started':
                setIsConnecting(false);
                setCurrentStep("Analysis started...");
                setStartTime(new Date());
                break;

              case 'task.progress':
                if (data.current_step) {
                  setCurrentStep(data.current_step);
                }
                if (data.progress !== undefined) {
                  setProgress(data.progress);
                }
                break;

              case 'task.completed':
                setIsCompleted(true);
                setProgress(100);
                setCurrentStep("Analysis complete! Redirecting to results...");
                if (data.results) {
                  // Call onComplete immediately
                  if (onComplete) {
                    // Navigate to results immediately
                    onComplete(data.results);
                  }
                }
                break;

              case 'task.error':
                setError(data.error || "An unknown error occurred");
                setIsConnecting(false);
                break;
            }
          },
          (error: Event) => {
            if (!mounted) return;
            console.error('WebSocket error:', error);
            setError("Connection error occurred");
            setIsConnecting(false);
          },
          (event: CloseEvent) => {
            if (!mounted) return;
            if (event.code !== 1000 && !isCompleted) {
              setError(`Connection closed unexpectedly (${event.code})`);
            }
            setIsConnecting(false);
          }
        );

        wsRef.current = ws;

      } catch (err) {
        if (!mounted) return;
        console.error('Error starting analysis:', err);
        setError(err instanceof Error ? err.message : "Failed to start analysis");
        setIsConnecting(false);
      }
    };

    startAnalysis();

    return () => {
      mounted = false;
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
    // ESLint disabled: onComplete is stable with useCallback, startTime/isCompleted change during execution
    // Adding them would restart WebSocket connection unnecessarily
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repository, task]);

  const handleRetry = () => {
    setError(null);
    setIsCompleted(false);
    setProgress(0);
    setCurrentStep("Initializing...");
    setIsConnecting(true);
    setTaskId(null);
    setStartTime(null);
  };

  const repoName = extractRepoName(repository);

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-6">
            <Button 
              variant="ghost" 
              onClick={onBack}
              className="p-2 hover:bg-white/60 rounded-lg transition-colors"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Button>
            <div className="w-12 h-12 bg-gray-800 rounded-xl flex items-center justify-center shadow-lg">
              <span className="text-white font-bold text-lg">W</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                {taskInfo.icon} {taskInfo.title}
              </h1>
              <p className="text-gray-600 text-lg">
                Analyzing <span className="font-semibold text-gray-800">{repoName}</span>
              </p>
              {taskId && (
                <p className="text-xs text-gray-500 font-mono mt-1">
                  Task ID: {taskId}
                </p>
              )}
            </div>
          </div>
        </div>

        {error ? (
          <Card className="shadow-lg border-0 bg-red-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-3 text-red-800">
                <div className="p-2 bg-red-500 rounded-lg shadow-md">
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                Analysis Failed
              </CardTitle>
              <CardDescription className="text-red-700">
                {error}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3">
                <Button variant="outline" onClick={handleRetry}>
                  Retry Analysis
                </Button>
                <Button variant="outline" onClick={onBack}>
                  Back to Tasks
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-8">
            {/* Progress Bar */}
            <Card className="shadow-lg border-0 bg-white">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-3 text-xl">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    {isCompleted ? (
                      <div className="w-5 h-5 bg-green-500 rounded-full flex items-center justify-center">
                        <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    ) : isConnecting ? (
                      <div className="animate-spin w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                    ) : (
                      <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-white rounded-full animate-pulse"></div>
                      </div>
                    )}
                  </div>
                  {isCompleted ? "Analysis Complete!" : isConnecting ? "Connecting..." : "Analysis in Progress"}
                </CardTitle>
                <CardDescription>
                  {isCompleted 
                    ? "Redirecting to results..." 
                    : isConnecting 
                      ? "Establishing connection to analysis service..." 
                      : taskInfo.description
                  }
                </CardDescription>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
                  <div 
                    className="bg-blue-600 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-gray-600 font-medium">{Math.round(progress)}% complete</p>
              </CardContent>
            </Card>

            {/* Current Step */}
            <Card className="shadow-lg border-0 bg-white">
              <CardHeader className="pb-4">
                <CardTitle className="flex items-center gap-3 text-xl">
                  <div className="p-2 bg-purple-100 rounded-lg">
                    <svg className="w-5 h-5 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  Current Step
                </CardTitle>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm shadow-md ${
                    isCompleted 
                      ? 'bg-green-500 text-white'
                      : 'bg-blue-500 text-white animate-pulse'
                  }`}>
                    {isCompleted ? (
                      <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    ) : (
                      <div className="w-3 h-3 bg-white rounded-full"></div>
                    )}
                  </div>
                  <span className="text-gray-900 font-medium text-lg">{currentStep}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  );
} 
