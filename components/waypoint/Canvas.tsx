import { useRef } from "react";
import { WorkflowNode } from "./WorkflowNode";
import { WaypointConnection, WaypointNode } from "@/lib/interface";

const Canvas: React.FC<{
  nodes: WaypointNode[];
  connections: WaypointConnection[];
  selectedNodeId: string | null;
  onNodeSelect: (id: string) => void;
  onNodeMove: (id: string, position: { x: number; y: number }) => void;
  onCanvasClick: () => void;
  onDrop: (e: React.DragEvent) => void;
  onStartConnection: (
    nodeId: string,
    handle: string,
    position: { x: number; y: number }
  ) => void;
  onEndConnection: (nodeId: string, handle: string) => void;
  onMouseMove: (e: React.MouseEvent) => void;
  onConnectionDelete: (connectionId: string) => void;
  onNodeDelete: (id: string) => void;
  onHideNodeActions: () => void;
  onShowNodeActions: (nodeId: string) => void;
  nodeActionsVisible: string | null;
  tempConnection: {
    start: { x: number; y: number };
    end: { x: number; y: number };
  } | null;
}> = ({
  nodes,
  connections,
  selectedNodeId,
  onNodeSelect,
  onNodeMove,
  onCanvasClick,
  onDrop,
  onStartConnection,
  onEndConnection,
  onMouseMove,
  onConnectionDelete,
  onNodeDelete,
  onHideNodeActions,
  onShowNodeActions,
  nodeActionsVisible,
  tempConnection,
}) => {
  const canvasRef = useRef<HTMLDivElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  // Helper function to get actual port positions from DOM
  const getPortPosition = (nodeId: string, portType: "input" | "output") => {
    const nodeElement = document.querySelector(`[data-node-id="${nodeId}"]`);
    if (!nodeElement) return null;

    const canvas = document.getElementById("workflow-canvas");
    if (!canvas) return null;

    const canvasRect = canvas.getBoundingClientRect();
    const nodeRect = nodeElement.getBoundingClientRect();

    // Calculate port position relative to canvas
    const baseX = nodeRect.left - canvasRect.left;
    const baseY = nodeRect.top - canvasRect.top;

    if (portType === "input") {
      return {
        x: baseX - 2, // Left side of node
        y: baseY + nodeRect.height / 2, // Center of node vertically
      };
    } else {
      return {
        x: baseX + nodeRect.width + 2, // Right side of node
        y: baseY + nodeRect.height / 2, // Center of node vertically
      };
    }
  };

  return (
    <div
      id="workflow-canvas"
      ref={canvasRef}
      className="flex-1 relative overflow-hidden bg-gray-100"
      style={{
        backgroundImage: `
            radial-gradient(circle, #d1d5db 1px, transparent 1px)
          `,
        backgroundSize: "20px 20px",
      }}
      onClick={(e) => {
        onCanvasClick();
        onHideNodeActions();
      }}
      onDrop={onDrop}
      onDragOver={handleDragOver}
      onMouseMove={onMouseMove}
    >
      {/* Grid pattern */}
      <div className="absolute inset-0 opacity-30">
        <svg width="100%" height="100%">
          <defs>
            <pattern
              id="grid"
              width="20"
              height="20"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 20 0 L 0 0 0 20"
                fill="none"
                stroke="#e5e7eb"
                strokeWidth="1"
              />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#grid)" />
        </svg>
      </div>

      {/* Connections */}
      <svg
        className="absolute inset-0 z-0"
        style={{
          overflow: "visible",
          pointerEvents: "auto",
        }}
      >
        {connections.map((connection) => {
          const sourceNode = nodes.find((n) => n.id === connection.source_id);
          const targetNode = nodes.find((n) => n.id === connection.target_id);

          if (!sourceNode || !targetNode) {
            return null;
          }

          // Try to get actual port positions from DOM first
          const sourcePortPos = getPortPosition(sourceNode.id, "output");
          const targetPortPos = getPortPosition(targetNode.id, "input");

          // Fallback to calculated positions if DOM lookup fails
          const nodeWidth = 192; // w-48 = 192px
          const nodeHeight = 60;

          const sourceX =
            sourcePortPos?.x ?? sourceNode.position.x + nodeWidth + 2;
          const sourceY =
            sourcePortPos?.y ?? sourceNode.position.y + nodeHeight / 2;
          const targetX = targetPortPos?.x ?? targetNode.position.x - 2;
          const targetY =
            targetPortPos?.y ?? targetNode.position.y + nodeHeight / 2;

          return (
            <g key={connection.id}>
              {/* Invisible thicker line for easier clicking */}
              <path
                d={`M ${sourceX} ${sourceY} C ${sourceX + 50} ${sourceY}, ${
                  targetX - 50
                } ${targetY}, ${targetX} ${targetY}`}
                stroke="transparent"
                strokeWidth="12"
                fill="none"
                style={{ 
                  cursor: 'pointer', 
                  pointerEvents: 'auto'
                }}
                onClick={(e) => {
                  e.stopPropagation();
                  onConnectionDelete(connection.id);
                }}
              />
              {/* Visible connection line */}
              <path
                d={`M ${sourceX} ${sourceY} C ${sourceX + 50} ${sourceY}, ${
                  targetX - 50
                } ${targetY}, ${targetX} ${targetY}`}
                stroke="#3b82f6"
                strokeWidth="3"
                fill="none"
                markerEnd="url(#arrowhead)"
                style={{ 
                  pointerEvents: 'none',
                  cursor: 'pointer'
                }}
                className="hover:stroke-red-500 transition-colors"
              />
            </g>
          );
        })}
      </svg>

      {/* Nodes */}
      {nodes.map((node) => (
        <WorkflowNode
          key={node.id}
          node={node}
          isSelected={selectedNodeId === node.id}
          onSelect={onNodeSelect}
          onMove={onNodeMove}
          onStartConnection={onStartConnection}
          onEndConnection={onEndConnection}
          onDelete={onNodeDelete}
          onHideActions={onHideNodeActions}
          showActions={nodeActionsVisible === node.id}
          onShowActions={onShowNodeActions}
        />
      ))}

      {/* Temporary connection */}
      {tempConnection && (
        <svg className="absolute inset-0 pointer-events-none z-30" width="100%" height="100%">
          <path
            d={`M ${tempConnection.start.x} ${tempConnection.start.y} C ${
              tempConnection.start.x + 50
            } ${tempConnection.start.y}, ${tempConnection.end.x - 50} ${
              tempConnection.end.y
            }, ${tempConnection.end.x} ${tempConnection.end.y}`}
            stroke="#3b82f6"
            strokeWidth="3"
            fill="none"
            strokeDasharray="8,4"
            opacity="0.8"
          />
        </svg>
      )}
    </div>
  );
};

export default Canvas;
