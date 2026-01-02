"use client";

import React from "react";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetDescription,
} from "@/components/ui/sheet";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  CheckCircle,
  XCircle,
  Clock,
  Play,
  AlertCircle,
  FileText,
  Copy,
  RotateCcw,
} from "lucide-react";
import { cn, formatSummaryText } from "@/lib/utils";
import {
  WorkflowExecutionState,
  NodeExecutionState,
  WaypointNode,
} from "@/lib/interface/waypoint-interface";
import { toast } from "sonner";

interface WorkflowResultsSheetProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  executionState: WorkflowExecutionState;
  nodes: WaypointNode[];
  onRunAgain?: () => void;
}

const WorkflowResultsSheet: React.FC<WorkflowResultsSheetProps> = ({
  open,
  onOpenChange,
  executionState,
  nodes,
  onRunAgain,
}) => {
  const getExecutionStats = () => {
    const completed = Object.values(executionState.nodeStates).filter(
      (state) => state.status === "completed"
    ).length;
    const failed = Object.values(executionState.nodeStates).filter(
      (state) => state.status === "failed"
    ).length;
    const total = nodes.length;

    return { completed, failed, total };
  };

  const formatDuration = (ms?: number) => {
    if (!ms) return "N/A";
    const seconds = Math.floor(ms / 1000);
    const minutes = Math.floor(seconds / 60);
    if (minutes > 0) {
      return `${minutes}m ${seconds % 60}s`;
    }
    return `${seconds}s`;
  };

  const getStatusIcon = (status: NodeExecutionState["status"]) => {
    switch (status) {
      case "completed":
        return <CheckCircle className="w-4 h-4 text-emerald-600" />;
      case "failed":
        return <XCircle className="w-4 h-4 text-red-500" />;
      case "executing":
        return <Play className="w-4 h-4 text-blue-500" />;
      default:
        return <Clock className="w-4 h-4 text-slate-400" />;
    }
  };

  const getStatusColor = (status: NodeExecutionState["status"]) => {
    switch (status) {
      case "completed":
        return "bg-gradient-to-r from-emerald-50 to-emerald-100 text-emerald-700 border-emerald-200";
      case "failed":
        return "bg-gradient-to-r from-red-50 to-red-100 text-red-700 border-red-200";
      case "executing":
        return "bg-gradient-to-r from-blue-50 to-blue-100 text-blue-700 border-blue-200";
      default:
        return "bg-gradient-to-r from-slate-50 to-slate-100 text-slate-700 border-slate-200";
    }
  };

  const stats = getExecutionStats();
  const totalExecutionTime = executionState.completedAt
    ? new Date(executionState.completedAt).getTime() -
      new Date(
        Math.min(
          ...Object.values(executionState.nodeStates)
            .filter((state) => state.startTime)
            .map((state) => new Date(state.startTime!).getTime())
        )
      ).getTime()
    : undefined;

  const copyResultsToClipboard = async () => {
    try {
      const resultsData = {
        workflowResults: {
          status: stats.failed > 0 ? "Partially Failed" : "Successfully Completed",
          executionTime: formatDuration(totalExecutionTime),
          toolsExecuted: stats.total,
          successfulTools: stats.completed,
          failedTools: stats.failed,
          completedAt: executionState.completedAt,
        },
        toolExecutionDetails: executionState.executionOrder.map((nodeId, index) => {
          const node = nodes.find((n) => n.id === nodeId);
          const nodeState = executionState.nodeStates[nodeId];
          return {
            step: index + 1,
            toolName: node?.data.label || "Unknown",
            status: nodeState?.status || "unknown",
            duration: formatDuration(nodeState?.duration),
            result: nodeState?.result?.summary || null,
            error: nodeState?.error || null,
          };
        }),
        analysisResults: executionState.results ? {
          summary: executionState.results.summary,
          toolsUsed: executionState.results.execution_info?.tools_used || [],
          totalToolsExecuted: executionState.results.execution_info?.total_tools_executed || 0,
        } : null,
        exportedAt: new Date().toISOString(),
      };
      
      await navigator.clipboard.writeText(JSON.stringify(resultsData, null, 2));
      toast.success("Results copied to clipboard!", {
        description: "Workflow execution data has been copied in JSON format"
      });
    } catch {
      toast.error("Failed to copy results", {
        description: "Please try again or check browser permissions"
      });
    }
  };

  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-[700px] sm:max-w-[700px] bg-gradient-to-br from-slate-50 via-white to-slate-50 p-4">
        <SheetHeader className="pb-6 border-b border-slate-200/60">
          <SheetTitle className="flex items-center gap-3 text-xl font-semibold bg-gradient-to-r from-slate-800 to-slate-600 bg-clip-text text-transparent">
            <div className="p-2 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-lg shadow-lg">
              <FileText className="w-5 h-5 text-white" />
            </div>
            Workflow Results
          </SheetTitle>
          <SheetDescription className="text-slate-600 mt-1">
            Comprehensive execution analysis and detailed tool outputs from your workflow
          </SheetDescription>
        </SheetHeader>

        <div className="flex-1 overflow-y-auto space-y-6 px-1">
          {/* Execution Summary */}
          <Card className="shadow-lg border-0 bg-gradient-to-br from-white via-slate-50/50 to-white backdrop-blur-sm">
            <CardHeader className="pb-4 border-b border-slate-200/50">
              <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                <div className="w-2 h-2 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-full"></div>
                Execution Summary
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6 p-6">
              <div className="grid grid-cols-2 gap-6">
                <div className="space-y-3">
                  <div className="text-sm font-medium text-slate-600">Overall Status</div>
                  <Badge
                    className={cn(
                      "px-4 py-2 text-sm font-semibold shadow-sm",
                      stats.failed > 0
                        ? "bg-gradient-to-r from-red-50 to-red-100 text-red-700 border-red-200 shadow-red-100"
                        : "bg-gradient-to-r from-emerald-50 to-emerald-100 text-emerald-700 border-emerald-200 shadow-emerald-100"
                    )}
                  >
                    {stats.failed > 0 ? "Partially Failed" : "Successfully Completed"}
                  </Badge>
                </div>
                <div className="space-y-3">
                  <div className="text-sm font-medium text-slate-600">Execution Time</div>
                  <div className="text-lg font-bold text-slate-800 bg-gradient-to-r from-slate-100 to-slate-50 px-3 py-2 rounded-lg border border-slate-200">
                    {formatDuration(totalExecutionTime)}
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div className="text-center p-4 bg-gradient-to-br from-emerald-50 to-emerald-100/50 rounded-xl border border-emerald-200/50 shadow-sm">
                  <div className="text-3xl font-bold text-emerald-600 mb-1">
                    {stats.completed}
                  </div>
                  <div className="text-sm font-medium text-emerald-700">Completed</div>
                </div>
                <div className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100/50 rounded-xl border border-red-200/50 shadow-sm">
                  <div className="text-3xl font-bold text-red-600 mb-1">
                    {stats.failed}
                  </div>
                  <div className="text-sm font-medium text-red-700">Failed</div>
                </div>
                <div className="text-center p-4 bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-xl border border-slate-200/50 shadow-sm">
                  <div className="text-3xl font-bold text-slate-600 mb-1">
                    {stats.total}
                  </div>
                  <div className="text-sm font-medium text-slate-700">Total Tools</div>
                </div>
              </div>

              {executionState.completedAt && (
                <div className="mt-4 p-3 bg-slate-50/50 rounded-lg border border-slate-200/50">
                  <div className="text-xs font-medium text-slate-500 uppercase tracking-wide mb-1">Completion Time</div>
                  <div className="text-sm text-slate-700 font-medium">
                    {new Date(executionState.completedAt).toLocaleString()}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Tool Results */}
          <Card className="shadow-lg border-0 bg-gradient-to-br from-white via-slate-50/30 to-white">
            <CardHeader className="pb-4 border-b border-slate-200/50">
              <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                <div className="w-2 h-2 bg-gradient-to-r from-indigo-500 to-purple-600 rounded-full"></div>
                Tool Execution Timeline
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 p-6">
              {executionState.executionOrder.map((nodeId, index) => {
                const node = nodes.find((n) => n.id === nodeId);
                const nodeState = executionState.nodeStates[nodeId];

                if (!node || !nodeState) return null;

                return (
                  <div key={nodeId} className="relative">
                    <div className="flex items-start gap-4 p-4 bg-gradient-to-r from-slate-50/50 to-white rounded-xl border border-slate-200/50 shadow-sm hover:shadow-md transition-shadow duration-200">
                      {/* Step number and status indicator */}
                      <div className="flex flex-col items-center gap-2 flex-shrink-0">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center text-sm font-semibold text-slate-600 border border-slate-300/50">
                          {index + 1}
                        </div>
                        {index < executionState.executionOrder.length - 1 && (
                          <div className="w-px h-6 bg-gradient-to-b from-slate-300 to-slate-200"></div>
                        )}
                      </div>

                      {/* Tool details */}
                      <div className="flex-1 space-y-3">
                        <div className="flex items-center justify-between">
                          <div className="flex items-center gap-3">
                            <div className="flex items-center gap-2">
                              {getStatusIcon(nodeState.status)}
                              <span className="font-semibold text-slate-800">{node.data.label}</span>
                            </div>
                            <Badge
                              className={cn(
                                "text-xs font-medium px-2 py-1 shadow-sm",
                                getStatusColor(nodeState.status)
                              )}
                            >
                              {nodeState.status.toUpperCase()}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2">
                            <Clock className="w-3 h-3 text-slate-400" />
                            <span className="text-sm font-medium text-slate-600">
                              {formatDuration(nodeState.duration)}
                            </span>
                          </div>
                        </div>

                        {nodeState.error && (
                          <div className="p-3 bg-gradient-to-r from-red-50 to-red-100/50 border-l-4 border-red-400 rounded-r-lg">
                            <div className="flex items-start gap-2">
                              <AlertCircle className="w-4 h-4 text-red-500 mt-0.5 flex-shrink-0" />
                              <div>
                                <div className="font-medium text-red-800 text-sm">Execution Error</div>
                                <div className="text-red-700 text-sm mt-1">{nodeState.error}</div>
                              </div>
                            </div>
                          </div>
                        )}

                        {nodeState.result && (
                          <div className="p-3 bg-gradient-to-r from-emerald-50 to-emerald-100/30 border-l-4 border-emerald-400 rounded-r-lg">
                            <div className="font-medium text-emerald-800 text-sm mb-2">Execution Result</div>
                            <div className="text-emerald-700 text-sm leading-relaxed">
                              {nodeState.result.summary || "Tool executed successfully with no additional details"}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })}
            </CardContent>
          </Card>

          {/* Analysis Results */}
          {executionState.results && (
            <Card className="shadow-lg border-0 bg-gradient-to-br from-white via-blue-50/20 to-white">
              <CardHeader className="pb-4 border-b border-slate-200/50">
                <CardTitle className="text-lg font-semibold text-slate-800 flex items-center gap-2">
                  <div className="w-2 h-2 bg-gradient-to-r from-blue-500 to-cyan-600 rounded-full"></div>
                  AI Analysis Results
                </CardTitle>
              </CardHeader>
              <CardContent className="p-6">
                <div className="space-y-4">
                  <div className="p-4 bg-gradient-to-br from-blue-50 via-blue-50/50 to-cyan-50/30 border border-blue-200/50 rounded-xl shadow-sm">
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-3 h-3 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full"></div>
                      <div className="font-semibold text-blue-900 text-sm uppercase tracking-wide">Executive Summary</div>
                    </div>
                    <div className="text-sm text-blue-800 leading-relaxed space-y-3">
                      {formatSummaryText(executionState.results.summary)}
                    </div>
                  </div>

                  {executionState.results.execution_info && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="p-4 bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-lg border border-slate-200/50">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Tools Utilized</div>
                        <div className="text-sm text-slate-700 font-medium">
                          {executionState.results.execution_info.tools_used?.join(" → ") || "None"}
                        </div>
                      </div>
                      <div className="p-4 bg-gradient-to-br from-slate-50 to-slate-100/50 rounded-lg border border-slate-200/50">
                        <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Total Executed</div>
                        <div className="text-lg font-bold text-slate-800">
                          {executionState.results.execution_info.total_tools_executed} tools
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Actions */}
        <div className="border-t border-slate-200/60 bg-gradient-to-r from-slate-50/50 to-white pt-6 mt-2 px-1">
          <div className="flex gap-3">
            <Button
              onClick={onRunAgain}
              variant="outline"
              className="flex-1 bg-gradient-to-r from-emerald-50 to-emerald-100/50 hover:from-emerald-100 hover:to-emerald-200/50 border-emerald-200 text-emerald-700 hover:text-emerald-800 shadow-sm hover:shadow-md transition-all duration-200 font-semibold"
              disabled={!onRunAgain}
            >
              <RotateCcw className="w-4 h-4 mr-2" />
              Run Workflow Again
            </Button>
            <Button
              onClick={copyResultsToClipboard}
              variant="outline"
              className="bg-gradient-to-r from-slate-50 to-slate-100/50 hover:from-slate-100 hover:to-slate-200/50 border-slate-200 text-slate-700 hover:text-slate-800 shadow-sm hover:shadow-md transition-all duration-200 px-4"
              title="Copy results to clipboard"
            >
              <Copy className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </SheetContent>
    </Sheet>
  );
};

export default WorkflowResultsSheet;
