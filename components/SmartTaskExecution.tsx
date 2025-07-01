"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  WhisperAPI, 
  AIAnalysisRequest, 
  AIAnalysisProgress, 
  SmartAnalysisResults,
  ExecutionPlan as ExecutionPlanType,
  extractRepoName 
} from "@/lib/api";
import ExecutionPlan from "./ExecutionPlan";

interface SmartTaskExecutionProps {
  repository: string;
  context: string;
  onBack: () => void;
  onComplete?: (results: SmartAnalysisResults) => void;
}

export default function SmartTaskExecution({ 
  repository, 
  context, 
  onBack,
  onComplete
}: SmartTaskExecutionProps) {
  const [currentStep, setCurrentStep] = useState<string>("Initializing AI analysis...");
  const [isCompleted, setIsCompleted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(true);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [executionPlan, setExecutionPlan] = useState<ExecutionPlanType | null>(null);
  
  // Track tool execution state
  const [currentBatch, setCurrentBatch] = useState(0);
  const [completedTools, setCompletedTools] = useState<Set<string>>(new Set());
  const [failedTools, setFailedTools] = useState<Set<string>>(new Set());
  const [runningTools, setRunningTools] = useState<Set<string>>(new Set());
  const [startTime, setStartTime] = useState<Date | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let mounted = true;

    const startSmartAnalysis = async () => {
      try {
        setIsConnecting(true);
        setError(null);

        // Create AI analysis request (simplified!)
        const request: AIAnalysisRequest = {
          repository_url: repository,
          prompt: context  // Use context as the prompt
        };

        const taskResponse = await WhisperAPI.createAITask(request);
        
        if (!mounted) return;
        
        setTaskId(taskResponse.task_id);
        setCurrentStep("Connecting to AI analysis service...");

        // Connect to AI WebSocket
        const ws = WhisperAPI.connectAIWebSocket(
          taskResponse.websocket_url,
          taskResponse.task_id,
          request,
          (data: AIAnalysisProgress) => {
            if (!mounted) return;


            switch (data.type) {
              case 'ai_analysis.started':
                setCurrentStep(data.message || "🤖 AI analysis started - analyzing your prompt...");
                setIsConnecting(false);
                if (!startTime) {
                  setStartTime(new Date());
                }
                break;

              case 'progress':
                if (data.current_step) {
                  setCurrentStep(data.current_step);
                }
                if (data.progress !== undefined) {
                  setProgress(data.progress);
                }
                setIsConnecting(false);
                if (!startTime) {
                  setStartTime(new Date());
                }
                break;

              case 'execution_plan':
                if (data.execution_plan) {
                  setExecutionPlan(data.execution_plan);
                  setCurrentStep("Execution plan created - starting tool execution...");
                }
                setIsConnecting(false);
                if (!startTime) {
                  setStartTime(new Date());
                }
                break;

              case 'tool_completed':
                if (data.tool_name) {
                  setCompletedTools(prev => new Set([...prev, data.tool_name!]));
                  setRunningTools(prev => {
                    const newSet = new Set(prev);
                    newSet.delete(data.tool_name!);
                    return newSet;
                  });
                  
                  if (data.tool_result?.success) {
                    setCurrentStep(`✅ ${data.tool_name} completed successfully`);
                  } else {
                    setFailedTools(prev => new Set([...prev, data.tool_name!]));
                    setCurrentStep(`❌ ${data.tool_name} failed`);
                  }
                  
                  // Update current batch based on completed tools
                  if (executionPlan) {
                    const completedToolsArray = [...completedTools, data.tool_name];
                    let newCurrentBatch = 0;
                    
                    for (let i = 0; i < executionPlan.batches.length; i++) {
                      const batchTools = executionPlan.batches[i].tools;
                      const batchToolsCompleted = batchTools.filter(tool => 
                        completedToolsArray.includes(tool)
                      ).length;
                      
                      if (batchToolsCompleted === batchTools.length) {
                        // This batch is complete, move to next
                        newCurrentBatch = i + 1;
                      } else if (batchToolsCompleted > 0) {
                        // This batch is in progress
                        newCurrentBatch = i;
                        break;
                      }
                    }
                    
                    setCurrentBatch(newCurrentBatch);
                  }
                }
                break;

              case 'tool_error':
                if (data.tool_name) {
                  setFailedTools(prev => new Set([...prev, data.tool_name!]));
                  setRunningTools(prev => {
                    const newSet = new Set(prev);
                    newSet.delete(data.tool_name!);
                    return newSet;
                  });
                  setCurrentStep(`❌ ${data.tool_name} failed: ${data.error || 'Unknown error'}`);
                }
                break;

              case 'completed':
                setIsCompleted(true);
                setProgress(100);
                setCurrentStep("🎉 AI analysis complete! Redirecting to results...");
                if (data.results) {
                  // Call onComplete immediately
                  if (onComplete && data.results) {
                    // Navigate to results immediately
                    onComplete(data.results!);
                  }
                }
                setRunningTools(new Set());
                // Set current batch to beyond all batches to show AI processing as complete
                // Use a larger number to ensure it's definitely beyond the batches
                setCurrentBatch(1000); // This ensures currentBatch > executionPlan.batches.length
                break;

              case 'error':
                setError(data.error || "An unknown error occurred during AI analysis");
                setIsConnecting(false);
                setRunningTools(new Set());
                break;
            }
          },
          (error: Event) => {
            if (!mounted) return;
            console.error('Smart WebSocket error:', error);
            setError("Connection error occurred during AI analysis");
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
        console.error('Error starting AI analysis:', err);
        setError(err instanceof Error ? err.message : "Failed to start AI analysis");
        setIsConnecting(false);
      }
    };

    startSmartAnalysis();

    return () => {
      mounted = false;
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [repository, context]);

  const handleRetry = () => {
    setError(null);
    setIsCompleted(false);
    setProgress(0);
    setCurrentStep("Initializing AI analysis...");
    setIsConnecting(true);
    setTaskId(null);
    setExecutionPlan(null);
    setCurrentBatch(0);
    setCompletedTools(new Set());
    setFailedTools(new Set());
    setRunningTools(new Set());
    setStartTime(null);
  };

  const handleCancel = () => {
    if (wsRef.current) {
      WhisperAPI.cancelTask(wsRef.current);
    }
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
                🤖 AI Analysis
              </h1>
              <p className="text-gray-600 text-lg">
                Analyzing <span className="font-semibold text-gray-800">{repoName}</span> with AI-powered tool selection
              </p>
              {taskId && (
                <p className="text-xs text-gray-500 font-mono mt-1">
                  Task ID: {taskId}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Context Display */}
        <Card className="mb-6 shadow-lg border-0 bg-white">
          <CardHeader className="pb-4">
            <CardTitle className="flex items-center gap-3 text-xl">
              <div className="p-2 bg-indigo-100 rounded-lg">
                <svg className="w-5 h-5 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              Analysis Context
            </CardTitle>
          </CardHeader>
          <CardContent className="pt-0">
            <div className="p-4 bg-indigo-50 rounded-xl border border-indigo-200">
              <p className="text-gray-800 italic font-medium leading-relaxed">
                "{context}"
              </p>
            </div>
            <div className="mt-4">
              <div className="inline-flex items-center px-3 py-1 bg-gradient-to-r from-green-100 to-blue-100 text-green-800 border border-green-200 rounded-full text-sm font-medium">
                <span className="mr-2">🤖</span>
                AI will automatically determine scope, depth, and approach
              </div>
            </div>
          </CardContent>
        </Card>

        {error ? (
          <Card className="shadow-lg border-0 bg-red-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-3 text-red-800">
                <div className="p-2 bg-red-500 rounded-lg shadow-md">
                  <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                AI Analysis Failed
              </CardTitle>
              <CardDescription className="text-red-700">
                {error}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-3">
                <Button onClick={handleRetry} variant="outline" size="sm">
                  Try Again
                </Button>
                <Button onClick={onBack} variant="ghost" size="sm">
                  Go Back
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-8">
            {/* Current Progress */}
            <Card className="shadow-lg border-0 bg-white">
              <CardHeader className="pb-4">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-3 text-xl">
                    <div className="p-2 bg-yellow-100 rounded-lg">
                      <span className="text-2xl">⚡</span>
                    </div>
                    Current Status
                  </CardTitle>
                  {!isCompleted && !error && (
                    <Button onClick={handleCancel} variant="outline" size="sm">
                      Cancel
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent className="pt-0">
                <div className="space-y-6">
                  <div className="flex items-center gap-4 p-4 bg-gray-50 rounded-xl border border-gray-200">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center shadow-md ${
                      isConnecting ? 'bg-blue-500' :
                      isCompleted ? 'bg-green-500' : 'bg-blue-500'
                    }`}>
                      {isConnecting ? (
                        <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      ) : isCompleted ? (
                        <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <div className="w-3 h-3 bg-white rounded-full animate-pulse"></div>
                      )}
                    </div>
                    <span className="font-medium text-lg text-gray-900">{currentStep}</span>
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-3">
                    <div 
                      className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-sm text-gray-600 font-medium">
                    <span>Progress: {progress}%</span>
                    <span>{isCompleted ? "Complete" : "In Progress"}</span>
                  </div>
                </div>
              </CardContent>
            </Card>

            {/* Execution Plan */}
            {executionPlan && (
              <ExecutionPlan
                executionPlan={executionPlan}
                currentBatch={currentBatch}
                completedTools={completedTools}
                failedTools={failedTools}
                runningTools={runningTools}
              />
            )}


          </div>
        )}
      </div>
    </div>
  );
} 