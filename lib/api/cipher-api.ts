import {
  AIAnalysisRequest,
  AIAnalysisResponse,
  StandardWebSocketMessage,
} from "../interface/cipher-interface";
import { API_BASE_URL } from "../utils";

export class CipherAPI {
  static async createTask(
    request: AIAnalysisRequest
  ): Promise<AIAnalysisResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/cipher/`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `Failed to create AI task: ${response.status} ${response.statusText}${
            errorData.detail ? ` - ${errorData.detail}` : ""
          }`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Error creating AI task:", error);
      throw error;
    }
  }

  static connectWebSocket(
    websocketUrl: string,
    taskId: string,
    request: AIAnalysisRequest,
    onMessage: (data: StandardWebSocketMessage) => void,
    onError: (error: Event) => void,
    onClose: (event: CloseEvent) => void
  ): WebSocket {
    const ws = new WebSocket(websocketUrl);

    ws.onopen = () => {
      ws.send(JSON.stringify(request));
    };

    ws.onmessage = (event) => {
      try {
        const data: StandardWebSocketMessage = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error("Error parsing AI WebSocket message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("AI WebSocket error:", error);
      onError(error);
    };

    ws.onclose = (event) => {
      onClose(event);
    };

    return ws;
  }

  static cancelTask(ws: WebSocket): void {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: "cancel" }));
    }
  }
}
