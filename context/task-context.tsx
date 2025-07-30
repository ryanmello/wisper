"use client";

import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  useEffect,
  useRef,
} from "react";
import { useAuth } from "./auth-context";
import { createTaskFromResponse, updateToolResults } from "@/lib/utils";
import { CipherRequest, StandardWebSocketMessage, Task, ToolResult } from "@/lib/interface/cipher-interface";
import { CipherAPI } from "@/lib/api/cipher-api";

interface TaskState {
  tasks: Task[];
  archivedTasks: Task[];
  isLoading: boolean;
  error: string | null;
  wsConnections: Map<string, WebSocket>;
}

type TaskAction =
  | { type: "set_loading"; payload: boolean }
  | { type: "set_error"; payload: string | null }
  | { type: "add_task"; payload: Task }
  | { type: "update_task"; payload: { id: string; updates: Partial<Task> } }
  | { type: "update_tool_result"; payload: { taskId: string; toolName: string; updates: Partial<ToolResult> } }
  | { type: "add_ai_message"; payload: { taskId: string; message: string } }
  | { type: "delete_task"; payload: string }
  | { type: "archive_task"; payload: string }
  | { type: "unarchive_task"; payload: string }
  | { type: "set_tasks"; payload: Task[] }
  | { type: "set_archived_tasks"; payload: Task[] }
  | { type: "add_ws_connection"; payload: { taskId: string; ws: WebSocket } }
  | { type: "remove_ws_connection"; payload: string }
  | { type: "clear_all_tasks" };

interface TaskContextType {
  tasks: Task[];
  archivedTasks: Task[];
  isLoading: boolean;
  error: string | null;

  createTask: (request: CipherRequest) => Promise<Task | null>;
  updateTask: (id: string, updates: Partial<Task>) => void;
  deleteTask: (id: string) => void;
  archiveTask: (id: string) => void;
  unarchiveTask: (id: string) => void;
  cancelTask: (id: string) => void;
  clearError: () => void;

  getTaskById: (id: string) => Task | null;
  getActiveTasks: () => Task[];
  getCompletedTasks: () => Task[];
  getFailedTasks: () => Task[];
}

const STORAGE_KEY = "cipher_tasks";
const ARCHIVED_STORAGE_KEY = "cipher_archived_tasks";

function taskReducer(state: TaskState, action: TaskAction): TaskState {
  switch (action.type) {
    case "set_loading":
      return { ...state, isLoading: action.payload };

    case "set_error":
      return { ...state, error: action.payload };

    case "add_task":
      return {
        ...state,
        tasks: [action.payload, ...state.tasks],
      };

    case "update_task": {
      const { id, updates } = action.payload;
      return {
        ...state,
        tasks: state.tasks.map((task) =>
          task.id === id
            ? { ...task, ...updates, updated_at: new Date().toISOString() }
            : task
        ),
        archivedTasks: state.archivedTasks.map((task) =>
          task.id === id
            ? { ...task, ...updates, updated_at: new Date().toISOString() }
            : task
        ),
      };
    }

    case "update_tool_result": {
      const { taskId, toolName, updates } = action.payload;
      const updateTaskToolResults = (task: Task) => {
        if (task.id !== taskId) return task;
        
        const currentResults = task.tool_results || [];
        const updatedResults = updateToolResults(currentResults, toolName, updates);
        
        return {
          ...task,
          tool_results: updatedResults,
          updated_at: new Date().toISOString()
        };
      };

      return {
        ...state,
        tasks: state.tasks.map(updateTaskToolResults),
        archivedTasks: state.archivedTasks.map(updateTaskToolResults),
      };
    }

    case "add_ai_message": {
      const { taskId, message } = action.payload;
      const addMessageToTask = (task: Task) => {
        if (task.id !== taskId) return task;
        
        return {
          ...task,
          ai_messages: [...(task.ai_messages || []), message],
          updated_at: new Date().toISOString()
        };
      };

      return {
        ...state,
        tasks: state.tasks.map(addMessageToTask),
        archivedTasks: state.archivedTasks.map(addMessageToTask),
      };
    }

    case "delete_task":
      return {
        ...state,
        tasks: state.tasks.filter((task) => task.id !== action.payload),
        archivedTasks: state.archivedTasks.filter(
          (task) => task.id !== action.payload
        ),
      };

    case "archive_task": {
      const taskToArchive = state.tasks.find(
        (task) => task.id === action.payload
      );
      if (!taskToArchive) return state;

      return {
        ...state,
        tasks: state.tasks.filter((task) => task.id !== action.payload),
        archivedTasks: [taskToArchive, ...state.archivedTasks],
      };
    }

    case "unarchive_task": {
      const taskToUnarchive = state.archivedTasks.find(
        (task) => task.id === action.payload
      );
      if (!taskToUnarchive) return state;

      return {
        ...state,
        archivedTasks: state.archivedTasks.filter(
          (task) => task.id !== action.payload
        ),
        tasks: [taskToUnarchive, ...state.tasks],
      };
    }

    case "set_tasks":
      return { ...state, tasks: action.payload };

    case "set_archived_tasks":
      return { ...state, archivedTasks: action.payload };

    case "add_ws_connection":
      return {
        ...state,
        wsConnections: new Map(state.wsConnections).set(
          action.payload.taskId,
          action.payload.ws
        ),
      };

    case "remove_ws_connection": {
      const newConnections = new Map(state.wsConnections);
      newConnections.delete(action.payload);
      return { ...state, wsConnections: newConnections };
    }

    case "clear_all_tasks":
      return {
        ...state,
        tasks: [],
        archivedTasks: [],
      };

    default:
      return state;
  }
}

// ========================================
// CONTEXT
// ========================================

const TaskContext = createContext<TaskContextType | undefined>(undefined);

// ========================================
// PROVIDER
// ========================================

interface TaskProviderProps {
  children: React.ReactNode;
}

export function TaskProvider({ children }: TaskProviderProps) {
  const { isAuthenticated } = useAuth();
  const [state, dispatch] = useReducer(taskReducer, {
    tasks: [],
    archivedTasks: [],
    isLoading: false,
    error: null,
    wsConnections: new Map(),
  });

  const persistenceRef = useRef<NodeJS.Timeout | null>(null);

  // ========================================
  // PERSISTENCE
  // ========================================

  // Load tasks from localStorage on mount
  useEffect(() => {
    if (!isAuthenticated) return;

    try {
      const savedTasks = localStorage.getItem(STORAGE_KEY);
      const savedArchivedTasks = localStorage.getItem(ARCHIVED_STORAGE_KEY);

      if (savedTasks) {
        const tasks = JSON.parse(savedTasks);
        dispatch({ type: "set_tasks", payload: tasks });
      }

      if (savedArchivedTasks) {
        const archivedTasks = JSON.parse(savedArchivedTasks);
        dispatch({ type: "set_archived_tasks", payload: archivedTasks });
      }
    } catch (error) {
      console.error("Error loading tasks from localStorage:", error);
    }
  }, [isAuthenticated]);

  // Save tasks to localStorage whenever they change
  useEffect(() => {
    if (!isAuthenticated) return;

    // Debounce saves to avoid excessive localStorage writes
    if (persistenceRef.current) {
      clearTimeout(persistenceRef.current);
    }

    persistenceRef.current = setTimeout(() => {
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(state.tasks));
        localStorage.setItem(
          ARCHIVED_STORAGE_KEY,
          JSON.stringify(state.archivedTasks)
        );
      } catch (error) {
        console.error("Error saving tasks to localStorage:", error);
      }
    }, 1000);

    return () => {
      if (persistenceRef.current) {
        clearTimeout(persistenceRef.current);
      }
    };
  }, [state.tasks, state.archivedTasks, isAuthenticated]);

  // ========================================
  // WEBSOCKET HANDLING
  // ========================================

  const handleWebSocketMessage = useCallback(
    (taskId: string, message: StandardWebSocketMessage) => {
      try {
        // Update task based on message type
        switch (message.type) {
          case "progress":
            // Update task status and progress
            dispatch({
              type: "update_task",
              payload: {
                id: taskId,
                updates: {
                  status: "processing",
                  progress: message.progress,
                },
              },
            });
            // Add AI message separately if present
            if (message.ai_message) {
              dispatch({
                type: "add_ai_message",
                payload: {
                  taskId,
                  message: message.ai_message,
                },
              });
            }
            break;

          case "tool_started":
            if (message.tool) {
              // Update task status
              dispatch({
                type: "update_task",
                payload: {
                  id: taskId,
                  updates: { status: "processing" },
                },
              });
              // Update tool result separately to avoid stale closure
              dispatch({
                type: "update_tool_result",
                payload: {
                  taskId,
                  toolName: message.tool.name,
                  updates: { status: "started", started_at: message.timestamp }
                },
              });
            }
            break;

          case "tool_completed":
            if (message.tool?.result) {
              dispatch({
                type: "update_tool_result",
                payload: {
                  taskId,
                  toolName: message.tool.name,
                  updates: {
                    status: "completed",
                    result: message.tool.result,
                    completed_at: message.timestamp,
                  }
                },
              });
            }
            break;

          case "tool_error":
            if (message.tool?.error) {
              dispatch({
                type: "update_tool_result",
                payload: {
                  taskId,
                  toolName: message.tool.name,
                  updates: {
                    status: "error",
                    error: message.tool.error,
                    completed_at: message.timestamp,
                  }
                },
              });
            }
            break;

          case "analysis_completed":
            dispatch({
              type: "update_task",
              payload: {
                id: taskId,
                updates: {
                  status: "completed",
                  final_results: message.results,
                  progress: message.progress || {
                    percentage: 100,
                    current_step: "Analysis completed",
                  },
                },
              },
            });
            if (message.ai_message) {
              dispatch({
                type: "add_ai_message",
                payload: {
                  taskId,
                  message: message.ai_message,
                },
              });
            }
            break;

          case "analysis_error":
            dispatch({
              type: "update_task",
              payload: {
                id: taskId,
                updates: {
                  status: "failed",
                  error: message.error,
                },
              },
            });
            if (message.ai_message) {
              dispatch({
                type: "add_ai_message",
                payload: {
                  taskId,
                  message: message.ai_message,
                },
              });
            }
            break;

          default:
            console.warn("Unknown message type:", message.type);
        }
      } catch (error) {
        console.error("Error handling WebSocket message:", error);
      }
    },
    []
  );

  const connectWebSocket = useCallback(
    (task: Task) => {
      if (!task.websocket_url) return;

      try {
        const ws = CipherAPI.connectWebSocket(
          task.websocket_url,
          task.id,
          (message) => handleWebSocketMessage(task.id, message),
          (error) => {
            console.error("WebSocket error for task", task.id, error);
            dispatch({
              type: "update_task",
              payload: {
                id: task.id,
                updates: {
                  status: "failed",
                  error: {
                    message: "WebSocket connection failed",
                    details: error.toString(),
                  },
                },
              },
            });
          },
          (event) => {
            dispatch({ type: "remove_ws_connection", payload: task.id });
          }
        );

        dispatch({
          type: "add_ws_connection",
          payload: { taskId: task.id, ws },
        });
      } catch (error) {
        console.error("Error connecting WebSocket:", error);
        dispatch({
          type: "update_task",
          payload: {
            id: task.id,
            updates: {
              status: "failed",
              error: {
                message: "Failed to connect to WebSocket",
                details: String(error),
              },
            },
          },
        });
      }
    },
    [handleWebSocketMessage]
  );

  // ========================================
  // TASK OPERATIONS
  // ========================================

  const createTask = useCallback(
    async (request: CipherRequest): Promise<Task | null> => {
      dispatch({ type: "set_loading", payload: true });
      dispatch({ type: "set_error", payload: null });

      try {
        const response = await CipherAPI.startAnalysis(request);
        const task = createTaskFromResponse(response, request);

        dispatch({ type: "add_task", payload: task });

        connectWebSocket(task);

        return task;
      } catch (error) {
        const errorMessage =
          error instanceof Error ? error.message : "Failed to create task";
        dispatch({ type: "set_error", payload: errorMessage });
        console.error("Error creating task:", error);
        return null;
      } finally {
        dispatch({ type: "set_loading", payload: false });
      }
    },
    [connectWebSocket]
  );

  const updateTask = useCallback((id: string, updates: Partial<Task>) => {
    dispatch({ type: "update_task", payload: { id, updates } });
  }, []);

  const deleteTask = useCallback(
    (id: string) => {
      // Cancel WebSocket connection if exists
      const ws = state.wsConnections.get(id);
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }

      dispatch({ type: "delete_task", payload: id });
      dispatch({ type: "remove_ws_connection", payload: id });
    },
    [state.wsConnections]
  );

  const archiveTask = useCallback((id: string) => {
    dispatch({ type: "archive_task", payload: id });
  }, []);

  const unarchiveTask = useCallback((id: string) => {
    dispatch({ type: "unarchive_task", payload: id });
  }, []);

  const cancelTask = useCallback(
    (id: string) => {
      const ws = state.wsConnections.get(id);
      if (ws && ws.readyState === WebSocket.OPEN) {
        CipherAPI.cancelTask(ws);
      }

      dispatch({
        type: "update_task",
        payload: {
          id,
          updates: { status: "cancelled" },
        },
      });
    },
    [state.wsConnections]
  );

  const clearError = useCallback(() => {
    dispatch({ type: "set_error", payload: null });
  }, []);

  // ========================================
  // UTILITY FUNCTIONS
  // ========================================

  const getTaskById = useCallback(
    (id: string): Task | null => {
      return (
        state.tasks.find((task) => task.id === id) ||
        state.archivedTasks.find((task) => task.id === id) ||
        null
      );
    },
    [state.tasks, state.archivedTasks]
  );

  const getActiveTasks = useCallback(() => {
    return state.tasks.filter(
      (task) =>
        task.status === "created" ||
        task.status === "started" ||
        task.status === "processing"
    );
  }, [state.tasks]);

  const getCompletedTasks = useCallback(() => {
    return state.tasks.filter((task) => task.status === "completed");
  }, [state.tasks]);

  const getFailedTasks = useCallback(() => {
    return state.tasks.filter((task) => task.status === "failed");
  }, [state.tasks]);

  // ========================================
  // CLEANUP
  // ========================================

  useEffect(() => {
    return () => {
      // Close all WebSocket connections on unmount
      state.wsConnections.forEach((ws) => {
        if (ws.readyState === WebSocket.OPEN) {
          ws.close();
        }
      });
    };
  }, [state.wsConnections]);

  // ========================================
  // CONTEXT VALUE
  // ========================================

  const value: TaskContextType = {
    tasks: state.tasks,
    archivedTasks: state.archivedTasks,
    isLoading: state.isLoading,
    error: state.error,

    createTask,
    updateTask,
    deleteTask,
    archiveTask,
    unarchiveTask,
    cancelTask,
    clearError,

    getTaskById,
    getActiveTasks,
    getCompletedTasks,
    getFailedTasks,
  };

  return <TaskContext.Provider value={value}>{children}</TaskContext.Provider>;
}

// ========================================
// HOOK
// ========================================

export function useTask() {
  const context = useContext(TaskContext);
  if (context === undefined) {
    throw new Error("useTask must be used within a TaskProvider");
  }
  return context;
}
