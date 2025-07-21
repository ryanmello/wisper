import { VedaRequest, VedaResponse } from "../interface/veda-interface";
import { API_BASE_URL } from "../utils";

export class VedaAPI {
  static async analyzeComment(
    request: VedaRequest
  ): Promise<VedaResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/analyze_comment`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `Failed to analyze comment: ${response.status} ${
            response.statusText
          }${errorData.detail ? ` - ${errorData.detail}` : ""}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Error analyzing comment:", error);
      throw error;
    }
  }
} 
