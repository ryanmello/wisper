import {
  CipherRequest,
  CipherResponse,
  StandardWebSocketMessage,
} from "../interface/cipher-interface";
import { API_BASE_URL } from "../utils";

export class CipherAPI {
  static async startAnalysis(
    request: CipherRequest
  ): Promise<CipherResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/cipher`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `Failed to start AI analysis: ${response.status} ${response.statusText}${
            errorData.detail ? ` - ${errorData.detail}` : ""
          }`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Error starting AI analysis:", error);
      throw error;
    }
  }

  static connectWebSocket(
    websocketUrl: string,
    taskId: string,
    onMessage: (data: StandardWebSocketMessage) => void,
    onError: (error: Event) => void,
    onClose: (event: CloseEvent) => void
  ): WebSocket {
    const ws = new WebSocket(websocketUrl);

    ws.onopen = () => {
      console.log(`Connected to Cipher WebSocket for task: ${taskId}`);
      // No need to send request data - task is already started by REST endpoint
    };

    ws.onmessage = (event) => {
      try {
        const data: StandardWebSocketMessage = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error("Error parsing Cipher WebSocket message:", error);
      }
    };

    ws.onerror = (error) => {
      console.error("Cipher WebSocket error:", error);
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
