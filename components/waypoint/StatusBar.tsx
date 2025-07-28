import {
  CheckCircle,
  Play,
  AlertCircle,
  Loader2,
  ShieldCheck,
  Info,
  Square,
  BookMarked,
  Layers,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";
import {
  WaypointConnection,
  WaypointNode,
  WorkflowExecutionState,
} from "@/lib/interface/waypoint-interface";

interface StatusBarProps {
  nodes: WaypointNode[];
  connections: WaypointConnection[];
  executionState: WorkflowExecutionState;
  onVerifyConfiguration: () => void;
  onStart: () => void;
  onStop?: () => void;
  onSavePlaybook?: () => void;
  verificationStatus: "idle" | "verifying" | "success" | "error";
  verificationMessage?: string;
  isStartEnabled: boolean;
  hasSelectedRepo: boolean;
}

const StatusBar = ({
  nodes,
  connections,
  executionState,
  onVerifyConfiguration,
  onStart,
  onStop,
  onSavePlaybook,
  verificationStatus,
  verificationMessage,
  isStartEnabled,
  hasSelectedRepo,
}: StatusBarProps) => {
  const getStatusIcon = () => {
    switch (verificationStatus) {
      case "verifying":
        return <></>;
      case "success":
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case "error":
        return <AlertCircle className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  const getStatusText = () => {
    switch (verificationStatus) {
      case "verifying":
        return ""; // Don't show text during verification, just the spinner icon
      case "success":
        return verificationMessage || "Configuration Valid";
      case "error":
        return verificationMessage || "Configuration Error";
    }
  };

  const getExecutionStats = () => {
    const completed = Object.values(executionState.nodeStates).filter(
      (state) => state.status === "completed"
    ).length;
    const failed = Object.values(executionState.nodeStates).filter(
      (state) => state.status === "failed"
    ).length;
    const executing = Object.values(executionState.nodeStates).filter(
      (state) => state.status === "executing"
    ).length;

    return { completed, failed, executing, total: nodes.length };
  };

  const stats = getExecutionStats();

  // Check if we're in the "finalizing" state (all tools done but analysis not complete)
  const isFinalizingState =
    executionState.isRunning &&
    stats.total > 0 &&
    stats.completed + stats.failed === stats.total &&
    stats.executing === 0;

  return (
    <div className="bg-gradient-to-r from-gray-50 via-slate-50 to-gray-50 border-t border-gray-200/60 px-6 py-4 backdrop-blur-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 text-sm text-gray-600">
          {onSavePlaybook && (
            <Button
              onClick={onSavePlaybook}
              disabled={
                nodes.length === 0 ||
                executionState.isRunning ||
                isFinalizingState
              }
              variant="outline"
              size="sm"
              className="relative overflow-hidden bg-gradient-to-r from-purple-50 to-purple-50 hover:from-purple-100 hover:to-purple-100 border-purple-200 text-purple-700 hover:text-purple-800 transition-all duration-200 disabled:from-gray-50 disabled:to-gray-50 disabled:text-gray-400 disabled:border-gray-200 shadow-sm hover:shadow-md"
            >
              <Layers className="w-4 h-4" />
            </Button>
          )}
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
            <span className="font-medium">Nodes: {nodes.length}</span>
          </div>
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-green-500 rounded-full"></div>
            <span className="font-medium">
              Connections: {connections.length}
            </span>
          </div>

          {/* Execution Progress */}
          {executionState.isRunning && (
            <>
              <div className="flex items-center space-x-2">
                <div
                  className={cn(
                    "w-2 h-2 rounded-full",
                    isFinalizingState
                      ? "bg-purple-500 animate-pulse"
                      : "bg-blue-500 animate-pulse"
                  )}
                ></div>
                <span className="font-medium">
                  {isFinalizingState
                    ? "Finalizing Analysis..."
                    : `Progress: ${stats.completed}/${stats.total}`}
                </span>
              </div>
              {stats.failed > 0 && (
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-red-500 rounded-full"></div>
                  <span className="font-medium text-red-600">
                    Failed: {stats.failed}
                  </span>
                </div>
              )}
              {!isFinalizingState && (
                <div className="text-xs text-gray-500">
                  {executionState.overallProgress}% complete
                </div>
              )}
              {isFinalizingState && (
                <div className="text-xs text-purple-600">
                  Processing results...
                </div>
              )}
            </>
          )}
        </div>

        <div className="flex items-center space-x-6">
          <div
            className={cn(
              "flex items-center space-x-2 px-3 py-1.5 bg-white/60 rounded-full border border-gray-200/50 shadow-sm",
              !getStatusText() &&
                (verificationStatus === "idle" ||
                  verificationStatus === "verifying") &&
                "hidden"
            )}
          >
            {getStatusIcon()}
            {getStatusText() && (
              <>
                <span className="text-sm font-semibold text-gray-700">
                  {verificationStatus === "success"
                    ? "Successfully verified configuration"
                    : verificationStatus === "error"
                    ? "Configuration Error"
                    : getStatusText()}
                </span>
                {(verificationStatus === "success" ||
                  verificationStatus === "error") && (
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Info className="w-4 h-4 text-gray-500 hover:text-gray-700 cursor-pointer" />
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>{getStatusText()}</p>
                    </TooltipContent>
                  </Tooltip>
                )}
              </>
            )}
          </div>

          <div className="flex items-center space-x-3">
            {/* Verify Configuration Button */}
            <Button
              onClick={onVerifyConfiguration}
              disabled={
                verificationStatus === "verifying" ||
                nodes.length === 0 ||
                !hasSelectedRepo ||
                executionState.isRunning ||
                isFinalizingState
              }
              variant="outline"
              size="sm"
              className="relative overflow-hidden bg-gradient-to-r from-blue-50 to-indigo-50 hover:from-blue-100 hover:to-indigo-100 border-blue-200 text-blue-700 hover:text-blue-800 transition-all duration-200 disabled:from-gray-50 disabled:to-gray-50 disabled:text-gray-400 disabled:border-gray-200 shadow-sm hover:shadow-md"
            >
              {verificationStatus === "verifying" ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  <span className="font-medium">Verifying...</span>
                </>
              ) : (
                <>
                  <ShieldCheck className="w-4 h-4 mr-2" />
                  <span className="font-medium">Verify Configuration</span>
                </>
              )}
            </Button>

            {/* Start/Stop Workflow Button */}
            {executionState.isRunning ? (
              isFinalizingState ? (
                <Button
                  disabled
                  variant="outline"
                  size="sm"
                  className="relative overflow-hidden bg-gradient-to-r from-purple-50 to-purple-100 border-purple-200 text-purple-700 transition-all duration-200 shadow-sm"
                >
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  <span className="font-semibold">Finalizing...</span>
                </Button>
              ) : (
                <Button
                  onClick={onStop}
                  variant="destructive"
                  size="sm"
                  className="relative overflow-hidden bg-gradient-to-r from-red-600 to-red-700 hover:from-red-700 hover:to-red-800 text-white border-0 transition-all duration-200 shadow-sm hover:shadow-lg hover:scale-[1.02] active:scale-[0.98]"
                >
                  <Square className="w-4 h-4 mr-2 fill-current" />
                  <span className="font-semibold">Stop Workflow</span>
                </Button>
              )
            ) : (
              <Button
                onClick={onStart}
                disabled={!isStartEnabled}
                variant="default"
                size="sm"
                className="relative overflow-hidden bg-gradient-to-r from-emerald-600 to-green-600 hover:from-emerald-700 hover:to-green-700 text-white border-0 transition-all duration-200 disabled:from-gray-400 disabled:to-gray-500 shadow-sm hover:shadow-lg hover:scale-[1.02] active:scale-[0.98]"
              >
                <Play className="w-4 h-4 mr-2 fill-current" />
                <span className="font-semibold">Start Workflow</span>
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatusBar;
