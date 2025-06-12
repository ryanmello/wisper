"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { 
  WhisperAPI, 
  SmartAnalysisRequest, 
  SmartAnalysisProgress, 
  SmartAnalysisResults,
  ExecutionPlan as ExecutionPlanType,
  extractRepoName 
} from "@/lib/api";
import ExecutionPlan from "./ExecutionPlan";

interface SmartTaskExecutionProps {
  repository: string;
  context: string;
  options?: any;
  onBack: () => void;
}

export default function SmartTaskExecution({ 
  repository, 
  context, 
  options = {},
  onBack 
}: SmartTaskExecutionProps) {
  const [currentStep, setCurrentStep] = useState<string>("Initializing smart analysis...");
  const [isCompleted, setIsCompleted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(true);
  const [results, setResults] = useState<SmartAnalysisResults | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [executionPlan, setExecutionPlan] = useState<ExecutionPlanType | null>(null);
  
  // Track tool execution state
  const [currentBatch, setCurrentBatch] = useState(0);
  const [completedTools, setCompletedTools] = useState<Set<string>>(new Set());
  const [failedTools, setFailedTools] = useState<Set<string>>(new Set());
  const [runningTools, setRunningTools] = useState<Set<string>>(new Set());
  
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let mounted = true;

    const startSmartAnalysis = async () => {
      try {
        setIsConnecting(true);
        setError(null);

        // Create smart analysis request
        const request: SmartAnalysisRequest = {
          repository_url: repository,
          context: context,
          ...options
        };

        console.log('Creating smart analysis task:', request);
        const taskResponse = await WhisperAPI.createSmartTask(request);
        
        if (!mounted) return;
        
        setTaskId(taskResponse.task_id);
        setCurrentStep("Connecting to smart analysis service...");

        // Connect to smart WebSocket
        const ws = WhisperAPI.connectSmartWebSocket(
          taskResponse.websocket_url,
          taskResponse.task_id,
          request,
          (data: SmartAnalysisProgress) => {
            if (!mounted) return;

            console.log('Smart WebSocket message:', data);

            switch (data.type) {
              case 'progress':
                if (data.current_step) {
                  setCurrentStep(data.current_step);
                }
                if (data.progress !== undefined) {
                  setProgress(data.progress);
                }
                setIsConnecting(false);
                break;

              case 'execution_plan':
                if (data.execution_plan) {
                  setExecutionPlan(data.execution_plan);
                  setCurrentStep("Execution plan created - starting tool execution...");
                }
                setIsConnecting(false);
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

              case 'completed':
                setIsCompleted(true);
                setProgress(100);
                setCurrentStep("🎉 Smart analysis complete!");
                if (data.results) {
                  setResults(data.results);
                }
                setRunningTools(new Set());
                // Set current batch to beyond all batches to show AI processing as complete
                // Use a larger number to ensure it's definitely beyond the batches
                setCurrentBatch(1000); // This ensures currentBatch > executionPlan.batches.length
                break;

              case 'error':
                setError(data.error || "An unknown error occurred during smart analysis");
                setIsConnecting(false);
                setRunningTools(new Set());
                break;
            }
          },
          (error: Event) => {
            if (!mounted) return;
            console.error('Smart WebSocket error:', error);
            setError("Connection error occurred during smart analysis");
            setIsConnecting(false);
          },
          (event: CloseEvent) => {
            if (!mounted) return;
            console.log('Smart WebSocket closed:', event.code, event.reason);
            if (event.code !== 1000 && !isCompleted) {
              setError(`Connection closed unexpectedly (${event.code})`);
            }
            setIsConnecting(false);
          }
        );

        wsRef.current = ws;

      } catch (err) {
        if (!mounted) return;
        console.error('Error starting smart analysis:', err);
        setError(err instanceof Error ? err.message : "Failed to start smart analysis");
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
  }, [repository, context, options]);

  const handleRetry = () => {
    setError(null);
    setIsCompleted(false);
    setProgress(0);
    setCurrentStep("Initializing smart analysis...");
    setIsConnecting(true);
    setResults(null);
    setTaskId(null);
    setExecutionPlan(null);
    setCurrentBatch(0);
    setCompletedTools(new Set());
    setFailedTools(new Set());
    setRunningTools(new Set());
  };

  const handleCancel = () => {
    if (wsRef.current) {
      WhisperAPI.cancelTask(wsRef.current);
    }
  };

  const repoName = extractRepoName(repository);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 p-6">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-6">
            <Button 
              variant="ghost" 
              onClick={onBack}
              className="p-2"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </Button>
            <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
              <span className="text-white font-bold">W</span>
            </div>
            <div>
              <h1 className="text-3xl font-bold text-gray-900">
                🧠 Smart Analysis
              </h1>
              <p className="text-gray-600">
                Analyzing <strong>{repoName}</strong> with AI-powered tool selection
              </p>
              {taskId && (
                <p className="text-xs text-gray-500 font-mono">
                  Task ID: {taskId}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* Context Display */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-lg">Analysis Context</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-gray-700 bg-gray-50 p-3 rounded-lg italic">
              "{context}"
            </p>
            {options.scope && (
              <div className="mt-3 flex gap-2">
                <Badge variant="outline">Scope: {options.scope.replace('_', ' ')}</Badge>
                {options.depth && (
                  <Badge variant="outline">Depth: {options.depth}</Badge>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {error ? (
          <Card className="border-red-200 bg-red-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-800">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                Smart Analysis Failed
              </CardTitle>
              <CardDescription className="text-red-700">
                {error}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-2">
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
          <div className="space-y-6">
            {/* Current Progress */}
            <Card>
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    <span className="text-2xl">⚡</span>
                    Current Status
                  </CardTitle>
                  {!isCompleted && !error && (
                    <Button onClick={handleCancel} variant="outline" size="sm">
                      Cancel
                    </Button>
                  )}
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center gap-3">
                    {isConnecting ? (
                      <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                    ) : isCompleted ? (
                      <div className="w-6 h-6 bg-green-500 rounded-full flex items-center justify-center">
                        <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                        </svg>
                      </div>
                    ) : (
                      <div className="w-6 h-6 bg-blue-500 rounded-full flex items-center justify-center">
                        <div className="w-2 h-2 bg-white rounded-full"></div>
                      </div>
                    )}
                    <span className="font-medium">{currentStep}</span>
                  </div>
                  
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                  <div className="flex justify-between text-sm text-gray-600">
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

            {/* Results */}
            {isCompleted && results && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <span className="text-2xl">📊</span>
                    Analysis Results
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    {/* AI Summary */}
                    <div>
                      <h3 className="text-lg font-semibold mb-3">AI-Generated Summary</h3>
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <p className="text-gray-700 whitespace-pre-wrap">{results.summary}</p>
                      </div>
                    </div>

                    {/* Key Metrics */}
                    {Object.keys(results.metrics).length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mb-3">Key Metrics</h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          {Object.entries(results.metrics).map(([key, value]) => (
                            <div key={key} className="bg-gray-50 p-3 rounded-lg">
                              <div className="text-2xl font-bold text-blue-600">{value}</div>
                              <div className="text-xs text-gray-600">{key.replace(/_/g, ' ')}</div>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Vulnerability Summary */}
                    {results.vulnerability_summary && (
                      <div>
                        <h3 className="text-lg font-semibold mb-3">Security Overview</h3>
                        <div className="bg-red-50 p-4 rounded-lg">
                          <div className="flex items-center gap-4 mb-3">
                            <Badge className={`
                              ${results.vulnerability_summary.risk_level === 'CRITICAL' ? 'bg-red-600' :
                                results.vulnerability_summary.risk_level === 'HIGH' ? 'bg-orange-600' :
                                results.vulnerability_summary.risk_level === 'MEDIUM' ? 'bg-yellow-600' :
                                'bg-green-600'}
                            `}>
                              {results.vulnerability_summary.risk_level} RISK
                            </Badge>
                            <span className="text-sm text-gray-600">
                              {results.vulnerability_summary.total_vulnerabilities} vulnerabilities found
                            </span>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="text-center">
                              <div className="text-lg font-bold text-red-600">
                                {results.vulnerability_summary.critical_vulnerabilities}
                              </div>
                              <div className="text-xs text-gray-600">Critical</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-orange-600">
                                {results.vulnerability_summary.high_vulnerabilities}
                              </div>
                              <div className="text-xs text-gray-600">High</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-yellow-600">
                                {results.vulnerability_summary.medium_vulnerabilities}
                              </div>
                              <div className="text-xs text-gray-600">Medium</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-green-600">
                                {results.vulnerability_summary.low_vulnerabilities}
                              </div>
                              <div className="text-xs text-gray-600">Low</div>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}

                    {/* Recommendations */}
                    {results.recommendations.length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mb-3">Recommendations</h3>
                        <div className="space-y-2">
                          {results.recommendations.slice(0, 10).map((rec, index) => (
                            <div key={index} className="flex items-start gap-2">
                              <span className="text-blue-500 mt-1">•</span>
                              <span className="text-gray-700">{rec}</span>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Tool Results Summary */}
                    <div>
                      <h3 className="text-lg font-semibold mb-3">Tool Execution Summary</h3>
                      <div className="bg-gray-50 p-4 rounded-lg">
                        <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                          <div>
                            <div className="text-lg font-bold text-green-600">{completedTools.size}</div>
                            <div className="text-xs text-gray-600">Tools Completed</div>
                          </div>
                          <div>
                            <div className="text-lg font-bold text-red-600">{failedTools.size}</div>
                            <div className="text-xs text-gray-600">Tools Failed</div>
                          </div>
                          <div>
                            <div className="text-lg font-bold text-blue-600">
                              {results.execution_info.execution_plan?.estimated_total_time || "N/A"}
                            </div>
                            <div className="text-xs text-gray-600">Total Time</div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Individual Tool Results */}
                    {results.tool_results && Object.keys(results.tool_results).length > 0 && (
                      <div>
                        <h3 className="text-lg font-semibold mb-3">Detailed Tool Results</h3>
                        <div className="space-y-4">
                          {Object.entries(results.tool_results).map(([toolName, toolResult]: [string, any]) => (
                            <Card key={toolName} className="border-l-4 border-l-blue-500">
                              <CardHeader className="pb-3">
                                <div className="flex items-center justify-between">
                                  <CardTitle className="text-base flex items-center gap-2">
                                    <span className="text-lg">
                                      {toolName.includes('vulnerability') ? '🔍' : 
                                       toolName.includes('explorer') ? '📁' : 
                                       toolName.includes('performance') ? '⚡' : 
                                       toolName.includes('security') ? '🔒' : '🔧'}
                                    </span>
                                    {toolName.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                                  </CardTitle>
                                  <Badge variant={toolResult.success ? "default" : "destructive"}>
                                    {toolResult.success ? "✅ Success" : "❌ Failed"}
                                  </Badge>
                                </div>
                                {toolResult.execution_time && (
                                  <p className="text-sm text-muted-foreground">
                                    Execution time: {toolResult.execution_time.toFixed(2)}s
                                  </p>
                                )}
                              </CardHeader>
                              <CardContent>
                                {toolResult.success && toolResult.results ? (
                                  <div className="space-y-3">
                                    {/* Display tool results in a formatted way */}
                                    {typeof toolResult.results === 'object' ? (
                                      <div className="space-y-2">
                                        {Object.entries(toolResult.results).map(([key, value]: [string, any]) => (
                                          <div key={key} className="border-l-2 border-gray-200 pl-3">
                                            <div className="text-sm font-medium text-gray-700 capitalize">
                                              {key.replace(/_/g, ' ')}
                                            </div>
                                            <div className="text-sm text-gray-600 mt-1">
                                              {typeof value === 'object' ? (
                                                <pre className="bg-gray-50 p-2 rounded text-xs overflow-x-auto">
                                                  {JSON.stringify(value, null, 2)}
                                                </pre>
                                              ) : (
                                                <span>{String(value)}</span>
                                              )}
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    ) : (
                                      <div className="bg-gray-50 p-3 rounded-lg">
                                        <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                                          {String(toolResult.results)}
                                        </pre>
                                      </div>
                                    )}
                                  </div>
                                ) : (
                                  <div className="bg-red-50 p-3 rounded-lg">
                                    <p className="text-red-700 text-sm">
                                      {toolResult.errors ? toolResult.errors.join(', ') : 'Tool execution failed'}
                                    </p>
                                  </div>
                                )}
                              </CardContent>
                            </Card>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 