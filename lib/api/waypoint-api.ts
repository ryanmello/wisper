import {
  VerifyWorkflowRequest,
  VerifyWorkflowResponse,
  GetToolsResponse,
} from "../interface/waypoint-interface";
import { API_BASE_URL } from "../utils";

export class WaypointAPI {
  static async verifyWorkflow(
    request: VerifyWorkflowRequest
  ): Promise<VerifyWorkflowResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/verify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        throw new Error(
          `Failed to verify workflow: ${response.status} ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Error verifying workflow:", error);
      throw error;
    }
  }

  static async getTools(): Promise<GetToolsResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/tools/`, {
        method: "GET",
        headers: {
          "Content-Type": "application/json",
        },
      });

      if (!response.ok) {
        throw new Error(
          `Failed to fetch tools: ${response.status} ${response.statusText}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Error fetching tools:", error);
      throw error;
    }
  }
}
