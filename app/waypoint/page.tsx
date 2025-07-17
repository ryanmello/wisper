"use client";

import { useState } from "react";
import { AuthLoadingScreen } from "@/components/AuthLoadingScreen";
import Canvas from "@/components/waypoint/Canvas";
import ToolSidebar from "@/components/waypoint/ToolSidebar";
import StatusBar from "@/components/waypoint/StatusBar";
import { useAuth } from "@/context/auth-context";
import {
  ResizableHandle,
  ResizablePanel,
  ResizablePanelGroup,
} from "@/components/ui/resizable";
import {
  WaypointConnection,
  WaypointNode,
} from "@/lib/interface/waypoint-interface";

export default function Waypoint() {
  const [nodes, setNodes] = useState<WaypointNode[]>([]);
  const [connections, setConnections] = useState<WaypointConnection[]>([]);
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);
  const [draggedTool, setDraggedTool] = useState<any>(null);
  const [isConnecting, setIsConnecting] = useState(false);
  const [connectionStart, setConnectionStart] = useState<{
    nodeId: string;
    handle: string;
  } | null>(null);
  const [tempConnection, setTempConnection] = useState<{
    start: { x: number; y: number };
    end: { x: number; y: number };
  } | null>(null);
  const [verificationStatus, setVerificationStatus] = useState<
    "idle" | "verifying" | "success" | "error"
  >("idle");
  const [verificationMessage, setVerificationMessage] = useState<string>("");
  const [isStartEnabled, setIsStartEnabled] = useState(false);
  const [nodeActionsVisible, setNodeActionsVisible] = useState<string | null>(
    null
  );

  const { isLoading: isAuthLoading, isAuthenticated } = useAuth();

  if (isAuthLoading) return <AuthLoadingScreen />;
  if (!isAuthenticated) return null;

  const resetVerificationStatus = () => {
    setVerificationStatus("idle");
    setVerificationMessage("");
    setIsStartEnabled(false);
  };

  const handleToolDragStart = (tool: any) => {
    setDraggedTool(tool);
  };

  const handleCanvasDrop = (e: React.DragEvent) => {
    e.preventDefault();

    if (!draggedTool) return;

    const canvas = document.getElementById("workflow-canvas");
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const position = {
      x: e.clientX - rect.left - 75,
      y: e.clientY - rect.top - 30,
    };

    const newNode: WaypointNode = {
      id: `${draggedTool.id}-${Date.now()}`,
      tool_name: draggedTool.id,
      position,
      data: {
        label: draggedTool.label,
        icon: draggedTool.icon,
        iconColor: draggedTool.iconColor,
        category: draggedTool.category,
      },
    };

    setNodes((prev) => [...prev, newNode]);
    setDraggedTool(null);

    // Reset verification status since workflow has changed
    resetVerificationStatus();
  };

  const handleNodeSelect = (id: string) => {
    setSelectedNodeId(id);
  };

  const handleNodeMove = (id: string, position: { x: number; y: number }) => {
    setNodes((prev) =>
      prev.map((node) => (node.id === id ? { ...node, position } : node))
    );
  };

  const handleCanvasClick = () => {
    setSelectedNodeId(null);
    setIsConnecting(false);
    setConnectionStart(null);
    setTempConnection(null);
  };

  const handleDeleteConnection = (connectionId: string) => {
    setConnections((prev) => prev.filter((conn) => conn.id !== connectionId));

    // Reset verification status since workflow has changed
    resetVerificationStatus();
  };

  const handleDeleteNode = (nodeId: string) => {
    // Remove the node
    setNodes((prev) => prev.filter((node) => node.id !== nodeId));

    // Remove all connections involving this node
    setConnections((prev) =>
      prev.filter(
        (conn) => conn.source_id !== nodeId && conn.target_id !== nodeId
      )
    );

    // Clear selection if deleted node was selected
    if (selectedNodeId === nodeId) {
      setSelectedNodeId(null);
    }

    // Reset verification status since workflow has changed
    resetVerificationStatus();
  };

  const handleHideNodeActions = () => {
    setNodeActionsVisible(null);
  };

  const handleShowNodeActions = (nodeId: string) => {
    setNodeActionsVisible(nodeId);
  };

  const handleStartConnection = (
    nodeId: string,
    handle: string,
    position: { x: number; y: number }
  ) => {
    setIsConnecting(true);
    setConnectionStart({ nodeId, handle });
    setTempConnection({ start: position, end: position });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isConnecting || !tempConnection) return;

    const canvas = document.getElementById("workflow-canvas");
    if (!canvas) return;

    const rect = canvas.getBoundingClientRect();
    const mousePos = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    };

    setTempConnection({
      start: tempConnection.start,
      end: mousePos,
    });
  };

  const handleEndConnection = (targetNodeId: string, targetHandle: string) => {
    if (!connectionStart || !isConnecting) {
      return;
    }

    // Don't allow connection to same node
    if (connectionStart.nodeId === targetNodeId) {
      setIsConnecting(false);
      setConnectionStart(null);
      setTempConnection(null);
      return;
    }

    // Only allow output to input connections
    if (
      (connectionStart.handle === "output" && targetHandle === "input") ||
      (connectionStart.handle === "input" && targetHandle === "output")
    ) {
      // Determine source and target based on connection direction
      const sourceNodeId =
        connectionStart.handle === "output"
          ? connectionStart.nodeId
          : targetNodeId;
      const targetNodeId_final =
        connectionStart.handle === "output"
          ? targetNodeId
          : connectionStart.nodeId;

      // Check for existing connections to prevent duplicates
      const existingConnection = connections.find(
        (conn) =>
          conn.source_id === sourceNodeId &&
          conn.target_id === targetNodeId_final
      );

      if (existingConnection) {
        // Connection already exists, don't create a duplicate
        setIsConnecting(false);
        setConnectionStart(null);
        setTempConnection(null);
        return;
      }

      // Create the new connection
      const newConnection: WaypointConnection = {
        id: `${sourceNodeId}-${targetNodeId_final}-${Date.now()}`,
        source_id: sourceNodeId,
        target_id: targetNodeId_final,
        source_tool_name:
          nodes.find((n) => n.id === sourceNodeId)?.tool_name || "",
        target_tool_name:
          nodes.find((n) => n.id === targetNodeId_final)?.tool_name || "",
        sourceHandle: "output",
        targetHandle: "input",
      };

      setConnections((prev) => [...prev, newConnection]);

      // Reset verification status since workflow has changed
      resetVerificationStatus();
    }

    setIsConnecting(false);
    setConnectionStart(null);
    setTempConnection(null);
  };

  const handleVerifyConfiguration = async () => {
    if (nodes.length === 0) {
      setVerificationStatus("error");
      setVerificationMessage("No nodes in workflow");
      setIsStartEnabled(false);
      return;
    }

    setVerificationStatus("verifying");
    setVerificationMessage("");
    setIsStartEnabled(false);

    try {
      const waypointData = {
        nodes: nodes.map((node) => ({
          id: node.id,
          tool_name: node.tool_name,
        })),
        connections: connections.map((conn) => ({
          id: conn.id,
          source_id: conn.source_id,
          source_tool_name: conn.source_tool_name,
          target_id: conn.target_id,
          target_tool_name: conn.target_tool_name,
        })),
      };

      const response = await fetch("http://localhost:8000/verify", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(waypointData),
      });

      const result = await response.json();

      if (response.ok && result.success) {
        setVerificationStatus("success");
        setVerificationMessage(
          result.message || "Workflow configuration is valid"
        );
        setIsStartEnabled(true);
      } else {
        setVerificationStatus("error");
        setVerificationMessage(
          result.message || "Workflow configuration is invalid"
        );
        setIsStartEnabled(false);
      }
    } catch (error) {
      console.error("Verification failed:", error);
      setVerificationStatus("error");
      setVerificationMessage("Failed to verify configuration");
      setIsStartEnabled(false);
    }
  };

  const handleStart = async () => {
    if (!isStartEnabled) return;

    try {
      const workflowData = {
        nodes: nodes.map((node) => ({
          id: node.id,
          tool_name: node.tool_name,
          label: node.data.label,
          category: node.data.category,
        })),
        connections: connections.map((conn) => ({
          id: conn.id,
          source: conn.source_id,
          target: conn.target_id,
        })),
      };

      console.log(workflowData);

      // Simulate some delay for realistic feel
      await new Promise((resolve) => setTimeout(resolve, 500));

      const mockResult = {
        success: true,
        executionId: `exec_${Date.now()}`,
        message: "Workflow execution started successfully",
      };

      console.log(mockResult);

      // Reset verification status after starting
      resetVerificationStatus();
    } catch (error) {
      console.error("Failed to start workflow:", error);
    }
  };

  return (
    <div className="h-screen flex flex-col bg-white">
      <ResizablePanelGroup direction="horizontal" className="flex-1">
        <ResizablePanel defaultSize={15} minSize={15} maxSize={40}>
          <ToolSidebar onDragStart={handleToolDragStart} />
        </ResizablePanel>
        <ResizableHandle />
        <ResizablePanel defaultSize={80}>
          <div className="flex-1 flex flex-col h-full">
            <Canvas
              nodes={nodes}
              connections={connections}
              selectedNodeId={selectedNodeId}
              onNodeSelect={handleNodeSelect}
              onNodeMove={handleNodeMove}
              onCanvasClick={handleCanvasClick}
              onDrop={handleCanvasDrop}
              onStartConnection={handleStartConnection}
              onEndConnection={handleEndConnection}
              onMouseMove={handleMouseMove}
              onConnectionDelete={handleDeleteConnection}
              onNodeDelete={handleDeleteNode}
              onHideNodeActions={handleHideNodeActions}
              onShowNodeActions={handleShowNodeActions}
              nodeActionsVisible={nodeActionsVisible}
              tempConnection={tempConnection}
            />
            <StatusBar
              nodes={nodes}
              connections={connections}
              onVerifyConfiguration={handleVerifyConfiguration}
              onStart={handleStart}
              verificationStatus={verificationStatus}
              verificationMessage={verificationMessage}
              isStartEnabled={isStartEnabled}
            />
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
