"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import type { ExecutionPlan, ToolBatch } from "@/lib/api";

interface ExecutionPlanProps {
  executionPlan: ExecutionPlan;
  currentBatch?: number;
  completedTools?: Set<string>;
  failedTools?: Set<string>;
  runningTools?: Set<string>;
}

interface ToolProgressProps {
  toolName: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
}

function ToolProgress({ toolName, status }: ToolProgressProps) {
  const getStatusIcon = () => {
    switch (status) {
      case 'completed':
        return '✅';
      case 'running':
        return '⏳';
      case 'failed':
        return '❌';
      default:
        return '⚪';
    }
  };

  const getStatusColor = () => {
    switch (status) {
      case 'completed':
        return 'text-green-600';
      case 'running':
        return 'text-blue-600';
      case 'failed':
        return 'text-red-600';
      default:
        return 'text-gray-400';
    }
  };

  const formatToolName = (name: string) => {
    return name
      .replace(/_/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className={`flex items-center gap-2 p-2 rounded-lg ${
      status === 'running' ? 'bg-blue-50 border border-blue-200' : 
      status === 'completed' ? 'bg-green-50 border border-green-200' :
      status === 'failed' ? 'bg-red-50 border border-red-200' :
      'bg-gray-50 border border-gray-200'
    }`}>
      <span className={`text-lg ${getStatusColor()}`}>
        {getStatusIcon()}
      </span>
      <span className={`font-medium ${getStatusColor()}`}>
        {formatToolName(toolName)}
      </span>
      {status === 'running' && (
        <div className="ml-auto">
          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      )}
    </div>
  );
}

export default function ExecutionPlan({
  executionPlan,
  currentBatch = 0,
  completedTools = new Set(),
  failedTools = new Set(),
  runningTools = new Set()
}: ExecutionPlanProps) {

  const getToolStatus = (toolName: string): 'pending' | 'running' | 'completed' | 'failed' => {
    if (failedTools.has(toolName)) return 'failed';
    if (completedTools.has(toolName)) return 'completed';
    if (runningTools.has(toolName)) return 'running';
    return 'pending';
  };

  const getBatchStatus = (batchIndex: number): 'pending' | 'running' | 'completed' => {
    if (batchIndex < currentBatch) return 'completed';
    if (batchIndex === currentBatch) return 'running';
    return 'pending';
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <span className="text-2xl">📋</span>
              Execution Plan
            </CardTitle>
            <CardDescription>
              {executionPlan.total_tools} tools • {executionPlan.estimated_total_time} estimated time
            </CardDescription>
          </div>
          <Badge variant="outline" className="bg-blue-50 text-blue-700">
            {executionPlan.strategy.replace('_', ' ')}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent>
        <div className="space-y-4">
          {executionPlan.batches.map((batch: ToolBatch, batchIndex: number) => {
            const batchStatus = getBatchStatus(batchIndex);
            
            return (
              <div 
                key={batchIndex}
                className={`border rounded-lg p-4 ${
                  batchStatus === 'running' ? 'border-blue-300 bg-blue-50' :
                  batchStatus === 'completed' ? 'border-green-300 bg-green-50' :
                  'border-gray-200 bg-gray-50'
                }`}
              >
                <div className="flex items-center justify-between mb-3">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-gray-700">
                      Batch {batchIndex + 1}
                    </span>
                    <Badge 
                      variant="secondary" 
                      className={batch.parallel ? "bg-purple-100 text-purple-700" : "bg-orange-100 text-orange-700"}
                    >
                      {batch.parallel ? "Parallel" : "Sequential"}
                    </Badge>
                  </div>
                  <span className="text-sm text-gray-600">
                    {batch.estimated_time}
                  </span>
                </div>
                
                <div className={`grid gap-2 ${
                  batch.parallel && batch.tools.length > 1 
                    ? 'grid-cols-1 md:grid-cols-2' 
                    : 'grid-cols-1'
                }`}>
                  {batch.tools.map((toolName: string, toolIndex: number) => (
                    <ToolProgress
                      key={`${batchIndex}-${toolIndex}`}
                      toolName={toolName}
                      status={getToolStatus(toolName)}
                    />
                  ))}
                </div>
                
                {batch.parallel && batch.tools.length > 1 && (
                  <div className="mt-2 text-xs text-gray-600">
                    ↳ These tools will run simultaneously
                  </div>
                )}
              </div>
            );
          })}
          
          {/* AI Insights Generation Step */}
          <div className={`border rounded-lg p-4 ${
            currentBatch >= executionPlan.batches.length ? 'border-blue-300 bg-blue-50' : 'border-gray-200 bg-gray-50'
          }`}>
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-2">
                <span className="font-semibold text-gray-700">
                  Final Step
                </span>
                <Badge variant="secondary" className="bg-indigo-100 text-indigo-700">
                  AI Processing
                </Badge>
              </div>
              <span className="text-sm text-gray-600">
                30 seconds
              </span>
            </div>
            
            <ToolProgress
              toolName="ai_insights_generation"
              status={
                currentBatch > executionPlan.batches.length ? 'completed' :
                currentBatch === executionPlan.batches.length ? 'running' :
                'pending'
              }
            />
            
            <div className="mt-2 text-xs text-gray-600">
              ↳ Generating comprehensive insights from all tool results
            </div>
          </div>
        </div>
        
        {/* Progress Summary */}
        <div className="mt-6 p-3 bg-gray-100 rounded-lg">
          <div className="flex items-center justify-between text-sm">
            <span className="text-gray-600">Progress</span>
            <span className="font-medium">
              {completedTools.size + failedTools.size} of {executionPlan.total_tools} tools completed
            </span>
          </div>
          <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
            <div 
              className="bg-blue-600 h-2 rounded-full transition-all duration-300"
              style={{ 
                width: `${((completedTools.size + failedTools.size) / executionPlan.total_tools) * 100}%` 
              }}
            />
          </div>
          {failedTools.size > 0 && (
            <div className="mt-2 text-xs text-red-600">
              {failedTools.size} tool{failedTools.size > 1 ? 's' : ''} failed
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
} 