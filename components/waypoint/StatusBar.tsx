import {
  CheckCircle,
  Play,
  AlertCircle,
  Loader2,
  ShieldCheck,
  Info,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { WaypointConnection, WaypointNode } from "@/lib/interface";
import { cn } from "@/lib/utils";

interface StatusBarProps {
  nodes: WaypointNode[];
  connections: WaypointConnection[];
  onVerifyConfiguration: () => void;
  onStart: () => void;
  verificationStatus: "idle" | "verifying" | "success" | "error";
  verificationMessage?: string;
  isStartEnabled: boolean;
}

const StatusBar = ({
  nodes,
  connections,
  onVerifyConfiguration,
  onStart,
  verificationStatus,
  verificationMessage,
  isStartEnabled,
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

  return (
    <div className="bg-gradient-to-r from-gray-50 via-slate-50 to-gray-50 border-t border-gray-200/60 px-6 py-4 backdrop-blur-sm">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4 text-sm text-gray-600">
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
            <Button
              onClick={onVerifyConfiguration}
              disabled={
                verificationStatus === "verifying" || nodes.length === 0
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
          </div>
        </div>
      </div>
    </div>
  );
};

export default StatusBar;
