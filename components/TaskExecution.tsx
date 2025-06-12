"use client";

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { WhisperAPI, AnalysisProgress, TaskType, extractRepoName } from "@/lib/api";

interface TaskExecutionProps {
  repository: string;
  task: TaskType;
  onBack: () => void;
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

export default function TaskExecution({ repository, task, onBack }: TaskExecutionProps) {
  const [currentStep, setCurrentStep] = useState<string>("Initializing...");
  const [isCompleted, setIsCompleted] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [isConnecting, setIsConnecting] = useState(true);
  const [results, setResults] = useState<AnalysisProgress['results'] | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  
  const wsRef = useRef<WebSocket | null>(null);
  const taskInfo = taskConfig[task] || taskConfig["explore-codebase"];

  useEffect(() => {
    let mounted = true;

    const startAnalysis = async () => {
      try {
        setIsConnecting(true);
        setError(null);

        // Create task
        console.log('Creating task for repository:', repository);
        const taskResponse = await WhisperAPI.createTask(repository, task);
        
        if (!mounted) return;
        
        setTaskId(taskResponse.task_id);
        setCurrentStep("Connecting to analysis service...");

        // Connect WebSocket
        const ws = WhisperAPI.connectWebSocket(
          taskResponse.websocket_url,
          taskResponse.task_id,
          repository,
          task,
          (data: AnalysisProgress) => {
            if (!mounted) return;

            console.log('WebSocket message:', data);

            switch (data.type) {
              case 'task.started':
                setIsConnecting(false);
                setCurrentStep("Analysis started...");
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
                setCurrentStep("Analysis complete!");
                if (data.results) {
                  setResults(data.results);
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
            console.log('WebSocket closed:', event.code, event.reason);
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
  }, [repository, task]);

  const handleRetry = () => {
    setError(null);
    setIsCompleted(false);
    setProgress(0);
    setCurrentStep("Initializing...");
    setIsConnecting(true);
    setResults(null);
    setTaskId(null);
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
                {taskInfo.icon} {taskInfo.title}
              </h1>
              <p className="text-gray-600">
                Analyzing <strong>{repoName}</strong>
              </p>
              {taskId && (
                <p className="text-xs text-gray-500 font-mono">
                  Task ID: {taskId}
                </p>
              )}
            </div>
          </div>
        </div>

        {error ? (
          <Card className="border-red-200 bg-red-50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-800">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                </svg>
                Analysis Failed
              </CardTitle>
              <CardDescription className="text-red-700">
                {error}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex gap-4">
                <Button variant="outline" onClick={handleRetry}>
                  Retry Analysis
                </Button>
                <Button variant="outline" onClick={onBack}>
                  Back to Tasks
                </Button>
              </div>
            </CardContent>
          </Card>
        ) : !isCompleted ? (
          <div className="space-y-6">
            {/* Progress Bar */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <div className="animate-spin w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full"></div>
                  {isConnecting ? "Connecting..." : "Analysis in Progress"}
                </CardTitle>
                <CardDescription>
                  {isConnecting ? "Establishing connection to analysis service..." : taskInfo.description}
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
                <p className="text-sm text-gray-600">{Math.round(progress)}% complete</p>
              </CardContent>
            </Card>

            {/* Current Step */}
            <Card>
              <CardHeader>
                <CardTitle>Current Step</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-3">
                  <div className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm animate-pulse">
                    <div className="w-2 h-2 bg-white rounded-full"></div>
                  </div>
                  <span className="text-gray-900">{currentStep}</span>
                </div>
              </CardContent>
            </Card>
          </div>
        ) : (
          <div className="space-y-6">
            {/* Results Header */}
            <Card className="border-green-200 bg-green-50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-800">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                  </svg>
                  Analysis Completed Successfully
                </CardTitle>
                <CardDescription className="text-green-700">
                  {results?.summary || "Repository analysis completed successfully"}
                </CardDescription>
              </CardHeader>
            </Card>

            {/* AI Insights */}
            {results?.detailed_results?.whisper_analysis?.analysis && (
              <Card>
                <CardHeader>
                  <CardTitle>🤖 AI-Powered Insights</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="prose prose-sm max-w-none">
                    <div className="whitespace-pre-wrap text-gray-700">
                      {results.detailed_results.whisper_analysis.analysis}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Architecture Patterns */}
            {results?.detailed_results?.whisper_analysis?.architecture_patterns && 
             results.detailed_results.whisper_analysis.architecture_patterns.length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>🏗️ Architecture Patterns</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2">
                    {results.detailed_results.whisper_analysis.architecture_patterns.map((pattern: string, index: number) => (
                      <Badge key={index} variant="secondary" className="text-sm">
                        {pattern}
                      </Badge>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Language Analysis */}
            {results?.detailed_results?.whisper_analysis?.language_analysis && (
              <Card>
                <CardHeader>
                  <CardTitle>📊 Language Analysis</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <p className="text-2xl font-bold text-gray-900">
                        {(results.detailed_results.whisper_analysis.language_analysis as any)?.primary_language || 'N/A'}
                      </p>
                      <p className="text-sm text-gray-600">Primary Language</p>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <p className="text-2xl font-bold text-gray-900">
                        {Object.keys((results.detailed_results.whisper_analysis.language_analysis as any)?.languages || {}).length}
                      </p>
                      <p className="text-sm text-gray-600">Languages Used</p>
                    </div>
                    <div className="text-center p-4 bg-gray-50 rounded-lg">
                      <p className="text-2xl font-bold text-gray-900">
                        {(results.detailed_results.whisper_analysis.language_analysis as any)?.total_code_files || 0}
                      </p>
                      <p className="text-sm text-gray-600">Code Files</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* File Structure Statistics */}
            {results?.detailed_results?.whisper_analysis?.file_structure && (
              <Card>
                <CardHeader>
                  <CardTitle>📁 Repository Statistics</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    {results.statistics && Object.entries(results.statistics).map(([key, value]) => (
                      <div key={key} className="text-center p-4 bg-gray-50 rounded-lg">
                        <p className="text-2xl font-bold text-gray-900">{String(value)}</p>
                        <p className="text-sm text-gray-600">{key}</p>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Dependency Audit Results */}
            {(results?.detailed_results as any)?.dependency_audit && (() => {
              const auditResults = (results!.detailed_results as any).dependency_audit;
              return (
                <Card>
                  <CardHeader>
                    <CardTitle>🔍 Dependency Audit Results</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      {/* Vulnerability Summary */}
                      {auditResults.vulnerability_scan?.scan_summary && (
                        <div className="bg-red-50 p-4 rounded-lg">
                          <h3 className="font-semibold mb-2">Security Scan Summary</h3>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            <div className="text-center">
                              <div className="text-2xl font-bold text-red-600">
                                {auditResults.vulnerability_scan.scan_summary.vulnerabilities_found}
                              </div>
                              <div className="text-xs text-gray-600">Total Vulnerabilities</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-gray-800">
                                {auditResults.vulnerability_scan.scan_summary.risk_level}
                              </div>
                              <div className="text-xs text-gray-600">Risk Level</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-blue-600">
                                {auditResults.vulnerability_scan.scan_summary.total_modules}
                              </div>
                              <div className="text-xs text-gray-600">Modules Scanned</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-gray-600">
                                {auditResults.primary_language}
                              </div>
                              <div className="text-xs text-gray-600">Language</div>
                            </div>
                          </div>
                        </div>
                      )}

                      {/* GitHub PR Status */}
                      {auditResults.github_pr && (
                        <div className={`p-4 rounded-lg ${
                          auditResults.github_pr.success 
                            ? (auditResults.github_pr.action === 'none_needed' 
                                ? 'bg-green-50 border border-green-200' 
                                : 'bg-green-50 border border-green-200')
                            : 'bg-red-50 border border-red-200'
                        }`}>
                          <h3 className="font-semibold mb-2">
                            {auditResults.github_pr.success 
                              ? (auditResults.github_pr.action === 'none_needed' 
                                  ? '✅ No Action Required' 
                                  : '✅ PR Created Successfully')
                              : '❌ PR Creation Failed'}
                          </h3>
                          {auditResults.github_pr.success ? (
                            <div className="space-y-2">
                              {auditResults.github_pr.action === 'none_needed' ? (
                                <div className="text-green-700">
                                  {auditResults.github_pr.message || 'No vulnerabilities found - repository is secure'}
                                </div>
                              ) : (
                                <>
                                  {auditResults.github_pr.pr_url && (
                                    <div>
                                      <strong>PR URL:</strong>{' '}
                                      <a 
                                        href={auditResults.github_pr.pr_url} 
                                        target="_blank" 
                                        rel="noopener noreferrer"
                                        className="text-blue-600 hover:underline"
                                      >
                                        {auditResults.github_pr.pr_url}
                                      </a>
                                    </div>
                                  )}
                                  <div>
                                    <strong>Vulnerabilities Fixed:</strong> {auditResults.github_pr.vulnerabilities_fixed || 0}
                                  </div>
                                </>
                              )}
                            </div>
                          ) : (
                            <div className="text-red-700">
                              {auditResults.github_pr.error || 'Unknown error occurred'}
                            </div>
                          )}
                        </div>
                      )}

                      {/* Summary */}
                      <div className="bg-blue-50 p-4 rounded-lg">
                        <p className="text-gray-700">{auditResults.summary}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              );
            })()}

            {/* Dependencies */}
            {results?.detailed_results?.whisper_analysis?.dependencies && 
             Object.keys(results.detailed_results.whisper_analysis.dependencies).length > 0 && (
              <Card>
                <CardHeader>
                  <CardTitle>📦 Dependencies</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {Object.entries(results.detailed_results.whisper_analysis.dependencies).map(([lang, deps]: [string, string[]]) => (
                      <div key={lang}>
                        <h4 className="font-semibold text-gray-900 mb-2">{lang}</h4>
                        <div className="flex flex-wrap gap-1">
                          {deps.slice(0, 10).map((dep: string, index: number) => (
                            <Badge key={index} variant="outline" className="text-xs">
                              {dep}
                            </Badge>
                          ))}
                          {deps.length > 10 && (
                            <Badge variant="outline" className="text-xs">
                              +{deps.length - 10} more
                            </Badge>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Action Buttons */}
            {isCompleted && (
              <div className="flex flex-col sm:flex-row gap-2 mt-6">
                <Button onClick={onBack} variant="outline" size="sm">
                  ← Back to Analysis
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
} 