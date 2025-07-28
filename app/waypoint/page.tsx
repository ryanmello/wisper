"use client";

import { useEffect, useState, useRef, useCallback } from "react";
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
  WorkflowExecutionState,
  WebSocketMessage,
  NodeExecutionStatus,
} from "@/lib/interface/waypoint-interface";
import { WaypointAPI } from "@/lib/api/waypoint-api";
import { GitHubRepository } from "@/lib/interface/github-interface";
import { GitHubAPI } from "@/lib/api/github-api";

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
  const [loading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [repositories, setRepositories] = useState<GitHubRepository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<GitHubRepository | null>(null);

  // New execution state management
  const [executionState, setExecutionState] = useState<WorkflowExecutionState>({
    isRunning: false,
    nodeStates: {},
    overallProgress: 0,
    executionOrder: [],
  });
  const [currentTaskId, setCurrentTaskId] = useState<string | null>(null);
  const websocketRef = useRef<WebSocket | null>(null);
  
  // Force connection position updates after execution state changes
  const [connectionUpdateKey, setConnectionUpdateKey] = useState(0);

  useEffect(() => {
    fetchUserRepositories();
    
    // Cleanup WebSocket on unmount
    return () => {
      if (websocketRef.current) {
        websocketRef.current.close();
      }
    };
  }, []);

  // Force connection position recalculation when execution state changes
  useEffect(() => {
    // Use requestAnimationFrame to ensure DOM has updated after execution state changes
    const timeoutId = setTimeout(() => {
      requestAnimationFrame(() => {
        setConnectionUpdateKey(prev => prev + 1);
      });
    }, 50); // Small delay to ensure node DOM updates are complete

    return () => clearTimeout(timeoutId);
  }, [executionState.nodeStates]);

  const fetchUserRepositories = async () => {
    try {
      setIsLoading(true);
      const response = await GitHubAPI.getRepositories();
      setRepositories(response.repositories);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to fetch repositories"
      );
    } finally {
      setIsLoading(false);
    }
  };

  const { isLoading: isAuthLoading, isAuthenticated } = useAuth();

  if (isAuthLoading) return <AuthLoadingScreen />;
  if (!isAuthenticated) return null;

  const resetVerificationStatus = () => {
    setVerificationStatus("idle");
    setVerificationMessage("");
    setIsStartEnabled(false);
  };

  const resetExecutionState = () => {
    setExecutionState({
      isRunning: false,
      nodeStates: {},
      overallProgress: 0,
      executionOrder: [],
    });
    setCurrentTaskId(null);
  };

  // WebSocket connection management - inline handlers to avoid hook order issues
  const connectWebSocket = (taskId: string, websocketUrl: string) => {
    if (websocketRef.current) {
      websocketRef.current.close();
    }

    const ws = new WebSocket(websocketUrl);
    websocketRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected for task:', taskId);
    };

    ws.onmessage = (event: MessageEvent) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        
        console.log('WebSocket message received:', message);
        
        setExecutionState(prev => {
          const newState = { ...prev };
          
          switch (message.type) {
            case 'progress':
              newState.overallProgress = message.progress?.percentage || prev.overallProgress;
              break;
              
            case 'tool_started':
              if (message.tool?.name) {
                // Use current nodes from state instead of closure
                setNodes(currentNodes => {
                  const nodeId = currentNodes.find(node => node.tool_name === message.tool!.name)?.id;
                  if (nodeId) {
                    console.log('🔵 Tool started executing:', nodeId);
                    setExecutionState(prevState => ({
                      ...prevState,
                      nodeStates: {
                        ...prevState.nodeStates,
                        [nodeId]: {
                          nodeId,
                          status: 'executing' as NodeExecutionStatus,
                          startTime: message.timestamp,
                        }
                      },
                      currentTool: message.tool!.name
                    }));
                  }
                  return currentNodes; // Return unchanged nodes
                });
              }
              break;
              
            case 'tool_completed':
              if (message.tool?.name) {
                const toolResult = message.tool.result;
                setNodes(currentNodes => {
                  const nodeId = currentNodes.find(node => node.tool_name === message.tool!.name)?.id;
                  if (nodeId) {
                    setExecutionState(prevState => {
                      const nodeState = prevState.nodeStates[nodeId];
                      if (nodeState) {
                        const startTime = nodeState.startTime;
                        const duration = startTime 
                          ? new Date(message.timestamp).getTime() - new Date(startTime).getTime()
                          : undefined;
                        
                        const updatedStates = {
                          ...prevState.nodeStates,
                          [nodeId]: {
                            ...nodeState,
                            status: 'completed' as NodeExecutionStatus,
                            endTime: message.timestamp,
                            duration,
                            result: toolResult,
                          }
                        };
                        
                        // Mark next tool(s) as queued
                        const currentIndex = prevState.executionOrder.indexOf(nodeId);
                        const nextNodeId = prevState.executionOrder[currentIndex + 1];
                        console.log(`🔄 Tool completed: ${nodeId}, next tool: ${nextNodeId}`);
                        if (nextNodeId && 
                            prevState.nodeStates[nextNodeId] && 
                            prevState.nodeStates[nextNodeId].status === 'pending') {
                          updatedStates[nextNodeId] = {
                            ...prevState.nodeStates[nextNodeId],
                            status: 'queued' as NodeExecutionStatus,
                          };
                          console.log('⏳ Next tool queued:', nextNodeId);
                        }
                        
                        return {
                          ...prevState,
                          nodeStates: updatedStates
                        };
                      }
                      return prevState;
                    });
                  }
                  return currentNodes; // Return unchanged nodes
                });
              }
              break;
              
            case 'tool_error':
              if (message.tool?.name) {
                const toolError = message.tool.error;
                setNodes(currentNodes => {
                  const nodeId = currentNodes.find(node => node.tool_name === message.tool!.name)?.id;
                  if (nodeId) {
                    setExecutionState(prevState => ({
                      ...prevState,
                      nodeStates: {
                        ...prevState.nodeStates,
                        [nodeId]: {
                          ...prevState.nodeStates[nodeId],
                          status: 'failed' as NodeExecutionStatus,
                          endTime: message.timestamp,
                          error: message.error?.message || toolError || 'Unknown error',
                        }
                      }
                    }));
                  }
                  return currentNodes; // Return unchanged nodes
                });
              }
              break;
              
            case 'analysis_completed':
              newState.isRunning = false;
              newState.overallProgress = 100;
              newState.results = message.results;
              break;
              
            case 'analysis_error':
              newState.isRunning = false;
              newState.error = message.error?.message || 'Analysis failed';
              break;
          }
          
          return newState;
        });
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    ws.onclose = (event) => {
      console.log('WebSocket disconnected:', event.code, event.reason);
      websocketRef.current = null;
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
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

    // Reset execution state to clear any previous run visuals
    resetExecutionState();

    setVerificationStatus("verifying");
    setVerificationMessage("");
    setIsStartEnabled(false);

    try {      
      const response = await WaypointAPI.verifyWorkflow({
        nodes: nodes,
        connections: connections,
      });

      if (response.success) {
        setVerificationStatus("success");
        setVerificationMessage(
          response.message || "Workflow configuration is valid"
        );
        setIsStartEnabled(true);
      } else {
        setVerificationStatus("error");
        setVerificationMessage(
          response.message || "Workflow configuration is invalid"
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

  // Helper function to calculate execution order based on connections
  const calculateExecutionOrder = (nodes: WaypointNode[], connections: WaypointConnection[]): string[] => {
    // Build a graph of dependencies
    const inDegree: Record<string, number> = {};
    const outgoing: Record<string, string[]> = {};
    
    // Initialize all nodes
    nodes.forEach(node => {
      inDegree[node.id] = 0;
      outgoing[node.id] = [];
    });
    
    // Build the dependency graph
    connections.forEach(conn => {
      outgoing[conn.source_id].push(conn.target_id);
      inDegree[conn.target_id]++;
    });
    
    // Topological sort to get execution order
    const queue: string[] = [];
    const result: string[] = [];
    
    // Find nodes with no dependencies (starting points)
    Object.keys(inDegree).forEach(nodeId => {
      if (inDegree[nodeId] === 0) {
        queue.push(nodeId);
      }
    });
    
    while (queue.length > 0) {
      const current = queue.shift()!;
      result.push(current);
      
      // Remove this node and update dependencies
      outgoing[current].forEach(neighbor => {
        inDegree[neighbor]--;
        if (inDegree[neighbor] === 0) {
          queue.push(neighbor);
        }
      });
    }
    
    return result;
  };

  const handleStart = async () => {
    if (!isStartEnabled || !selectedRepo) return;

    try {
      // Calculate execution order based on workflow topology
      const executionOrder = calculateExecutionOrder(nodes, connections);
      console.log('🔄 Calculated execution order:', executionOrder);
      
      // Initialize execution state
      const initialNodeStates: Record<string, any> = {};
      nodes.forEach(node => {
        initialNodeStates[node.id] = {
          nodeId: node.id,
          status: 'pending',
        };
      });

      // Mark the first tool(s) in execution order as queued (ready to start)
      executionOrder.slice(0, 1).forEach(nodeId => {
        if (initialNodeStates[nodeId]) {
          initialNodeStates[nodeId].status = 'queued';
          console.log('⏳ Marked as queued:', nodeId);
        }
      });

      setExecutionState({
        isRunning: true,
        nodeStates: initialNodeStates,
        overallProgress: 0,
        executionOrder: executionOrder,
      });

      const response = await WaypointAPI.startWorkflow({
        repository_url: selectedRepo.full_name || "",
        nodes: nodes,
        connections: connections,
      });

      setCurrentTaskId(response.task_id);
      
      // Connect to WebSocket for real-time updates
      connectWebSocket(response.task_id, response.websocket_url);

      // Reset verification status after starting
      resetVerificationStatus();
    } catch (error) {
      console.error("Failed to start workflow:", error);
      resetExecutionState();
    }
  };

  const handleStop = () => {
    if (websocketRef.current) {
      websocketRef.current.close();
    }
    resetExecutionState();
  };

  const handleSavePlaybook = () => {
    if (nodes.length === 0) return;

    // TODO: Implement save playbook logic
    console.log("Saving waypoint playbook with nodes:", nodes);
    console.log("Connections:", connections);
    console.log("Selected repository:", selectedRepo?.full_name);
    
    // For now, just show a simple alert
    alert("Waypoint playbook save functionality will be implemented soon!");
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
              repositories={repositories}
              selectedRepo={selectedRepo}
              repoError={error}
              executionState={executionState}
              connectionUpdateKey={connectionUpdateKey}
              onRepoSelect={setSelectedRepo}
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
              executionState={executionState}
              onVerifyConfiguration={handleVerifyConfiguration}
              onStart={handleStart}
              onStop={handleStop}
              onSavePlaybook={handleSavePlaybook}
              verificationStatus={verificationStatus}
              verificationMessage={verificationMessage}
              isStartEnabled={isStartEnabled}
              hasSelectedRepo={selectedRepo !== null}
            />
          </div>
        </ResizablePanel>
      </ResizablePanelGroup>
    </div>
  );
}
