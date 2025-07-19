import React, { useState, useEffect, useCallback } from "react";
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";
import { WaypointNode } from "@/lib/interface/waypoint-interface";

interface WorkflowNodeProps {
  node: WaypointNode;
  isSelected: boolean;
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

  return (
    <div
      data-node-id={node.id}
      className={`absolute bg-white border-2 rounded-lg py-3 px-6 cursor-move shadow-lg select-none  ${
        isSelected ? "border-blue-500 shadow-blue-200" : "border-gray-300"
      } ${isDragging ? "opacity-80" : ""}`}
      style={{
        left: node.position.x,
        top: node.position.y,
        zIndex: isSelected ? 20 : 10,
      }}
      onMouseDown={handleMouseDown}
      onContextMenu={handleContextMenu}
    >
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
        </div>
      </div>

      {/* Action Icons */}
      {showActions && (
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
