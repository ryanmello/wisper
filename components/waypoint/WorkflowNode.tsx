import React, { useState, useEffect, useCallback } from "react";
import { Trash2, CheckCircle, AlertCircle, Clock, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { WaypointNode, NodeExecutionStatus } from "@/lib/interface/waypoint-interface";
import { cn } from "@/lib/utils";

interface WorkflowNodeProps {
  node: WaypointNode;
  isSelected: boolean;
  executionStatus?: NodeExecutionStatus;
  duration?: number;
  error?: string;
  onSelect: (id: string) => void;
  onMove: (id: string, position: { x: number; y: number }) => void;
  onStartConnection: (
    nodeId: string,
    handle: string,
    position: { x: number; y: number }
  ) => void;
  onEndConnection: (nodeId: string, handle: string) => void;
  onDelete: (id: string) => void;
  onHideActions: () => void;
  showActions: boolean;
  onShowActions: (nodeId: string) => void;
}

export const WorkflowNode: React.FC<WorkflowNodeProps> = ({
  node,
  isSelected,
  executionStatus = 'pending',
  duration,
  error,
  onSelect,
  onMove,
  onStartConnection,
  onEndConnection,
  onDelete,
  onHideActions,
  showActions,
  onShowActions,
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });

  const handleMouseDown = (e: React.MouseEvent) => {
    // Ignore right-click for drag functionality
    if (e.button === 2) return;
    
    setIsDragging(true);
    const rect = e.currentTarget.getBoundingClientRect();
    setDragOffset({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
    onSelect(node.id);
    onHideActions(); // Hide actions on other nodes
  };

  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    onShowActions(node.id);
  };

  const handleDeleteNode = () => {
    onDelete(node.id);
    onHideActions();
  };

  const handleMouseMove = useCallback(
    (e: MouseEvent) => {
      if (!isDragging) return;

      const canvas = document.getElementById("workflow-canvas");
      if (!canvas) return;

      const rect = canvas.getBoundingClientRect();
      const newPosition = {
        x: e.clientX - rect.left - dragOffset.x,
        y: e.clientY - rect.top - dragOffset.y,
      };

      onMove(node.id, newPosition);
    },
    [isDragging, dragOffset, node.id, onMove]
  );

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
  }, []);

  useEffect(() => {
    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      return () => {
        document.removeEventListener("mousemove", handleMouseMove);
        document.removeEventListener("mouseup", handleMouseUp);
      };
    }
  }, [isDragging, handleMouseMove, handleMouseUp]);

  // Get styles based on execution status
  const getNodeStyles = () => {
    const baseClasses = "absolute bg-white border-2 rounded-lg py-3 px-6 cursor-move shadow-lg select-none transition-[border-color,box-shadow,opacity] duration-300";
    
    switch (executionStatus) {
      case 'executing':
        return cn(baseClasses, 
          "border-blue-500 shadow-blue-200",
          "animate-pulse"
        );
      case 'completed':
        return cn(baseClasses, "border-green-500 shadow-green-200");
      case 'failed':
        return cn(baseClasses, "border-red-500 shadow-red-200");
      case 'queued':
        return cn(baseClasses, 
          "border-orange-400 shadow-orange-200",
          "animate-pulse"
        );
      default:
        return cn(baseClasses, 
          isSelected ? "border-blue-500 shadow-blue-200" : "border-gray-300"
        );
    }
  };

  // Get status indicator
  const getStatusIndicator = () => {
    switch (executionStatus) {
      case 'executing':
        return (
          <div className="absolute -top-2 -left-2 w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center shadow-md">
            <Loader2 className="w-3 h-3 text-white animate-spin" />
          </div>
        );
      case 'completed':
        return (
          <div className="absolute -top-2 -left-2 w-5 h-5 bg-green-500 rounded-full flex items-center justify-center shadow-md">
            <CheckCircle className="w-3 h-3 text-white" />
          </div>
        );
      case 'failed':
        return (
          <div className="absolute -top-2 -left-2 w-5 h-5 bg-red-500 rounded-full flex items-center justify-center shadow-md">
            <AlertCircle className="w-3 h-3 text-white" />
          </div>
        );
      case 'queued':
        return (
          <div className="absolute -top-2 -left-2 w-5 h-5 bg-orange-400 rounded-full flex items-center justify-center shadow-md">
            <Clock className="w-3 h-3 text-white" />
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div
      data-node-id={node.id}
      className={`${getNodeStyles()} ${isDragging ? "opacity-80" : ""}`}
      style={{
        left: node.position.x,
        top: node.position.y,
        zIndex: isSelected ? 20 : 10,
      }}
      onMouseDown={handleMouseDown}
      onContextMenu={handleContextMenu}
      title={error ? `Error: ${error}` : undefined}
    >
      {/* Status Indicator */}
      {getStatusIndicator()}

      {/* Duration Badge */}
      {duration && executionStatus === 'completed' && (
        <div className="absolute -top-2 right-2 px-2 py-0.5 bg-gray-600 text-white text-xs rounded-full shadow-md">
          {duration < 1000 ? `${Math.round(duration)}ms` : `${(duration / 1000).toFixed(1)}s`}
        </div>
      )}

      {/* Input port - positioned on the left side */}
      <div
        className="absolute w-4 h-4 bg-green-400 rounded-full border-2 border-white shadow-sm -left-2 top-1/2 transform -translate-y-1/2 cursor-pointer hover:bg-green-500 hover:scale-110 transition-all"
        onMouseDown={(e) => {
          e.stopPropagation();
          const canvas = document.getElementById("workflow-canvas");
          if (!canvas) return;

          const canvasRect = canvas.getBoundingClientRect();
          const portRect = e.currentTarget.getBoundingClientRect();
          const position = {
            x: portRect.left + portRect.width / 2 - canvasRect.left,
            y: portRect.top + portRect.height / 2 - canvasRect.top,
          };
          onStartConnection(node.id, "input", position);
        }}
        onMouseUp={(e) => {
          e.stopPropagation();
          onEndConnection(node.id, "input");
        }}
        title="Input port - drag to connect"
      />

      {/* Output port - positioned on the right side */}
      <div
        className="absolute w-4 h-4 bg-blue-400 rounded-full border-2 border-white shadow-sm -right-2 top-1/2 transform -translate-y-1/2 cursor-pointer hover:bg-blue-500 hover:scale-110 transition-all"
        onMouseDown={(e) => {
          e.stopPropagation();
          const canvas = document.getElementById("workflow-canvas");
          if (!canvas) return;

          const canvasRect = canvas.getBoundingClientRect();
          const portRect = e.currentTarget.getBoundingClientRect();
          const position = {
            x: portRect.left + portRect.width / 2 - canvasRect.left,
            y: portRect.top + portRect.height / 2 - canvasRect.top,
          };
          onStartConnection(node.id, "output", position);
        }}
        onMouseUp={(e) => {
          e.stopPropagation();
          onEndConnection(node.id, "output");
        }}
        title="Output port - drag to connect"
      />

      {/* Node content */}
      <div className="flex items-center">
        <div className="mr-3">
          <node.data.icon className={`w-6 h-6 ${node.data.iconColor}`} />
        </div>
        <div>
          <div className="font-medium text-sm text-gray-800">
            {node.data.label}
          </div>
          <div className="text-xs text-gray-500">{node.data.category}</div>
          {/* Execution status text */}
          {executionStatus !== 'pending' && (
            <div className={cn(
              "text-xs font-medium mt-1",
              executionStatus === 'executing' && "text-blue-600",
              executionStatus === 'completed' && "text-green-600",
              executionStatus === 'failed' && "text-red-600",
              executionStatus === 'queued' && "text-orange-600"
            )}>
              {executionStatus === 'executing' && "Running..."}
              {executionStatus === 'completed' && "Completed"}
              {executionStatus === 'failed' && "Failed"}
              {executionStatus === 'queued' && "Queued"}
            </div>
          )}
        </div>
      </div>

      {/* Action Icons - only show when not running */}
      {showActions && executionStatus !== 'executing' && (
        <div className="absolute -top-2 -right-2 flex space-x-1 z-30">
          <Button
            variant="default"
            size="icon"
            className="w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full shadow-md transition-colors p-0"
            onClick={(e) => {
              e.stopPropagation();
              handleDeleteNode();
            }}
            onMouseDown={(e) => {
              e.stopPropagation();
            }}
            title="Delete node"
          >
            <Trash2 className="w-3 h-3" />
          </Button>
        </div>
      )}
    </div>
  );
}; 
