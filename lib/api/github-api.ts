import {
  GetPullRequestCommentsRequest,
  GetPullRequestCommentsResponse,
  GetPullRequestFilesRequest,
  GetPullRequestFilesResponse,
  GetPullRequestsRequest,
  GetPullRequestsResponse,
  GetRepositoriesRequest,
  GetRepositoriesResponse,
  GetUserRequest,
  GitHubUser,
  PostPullRequestCommentRequest,
  PostPullRequestCommentResponse,
} from "../interface/github-interface";
import { API_BASE_URL } from "../utils";

export class GitHubAPI {
  static async getUser(request: GetUserRequest): Promise<GitHubUser> {
    try {
      const response = await fetch(`${API_BASE_URL}/user`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `Failed to fetch user: ${response.status} ${
            response.statusText
          }${errorData.detail ? ` - ${errorData.detail}` : ""}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Error fetching user:", error);
      throw error;
    }
  }

  static async getRepositories(
    request: GetRepositoriesRequest
  ): Promise<GetRepositoriesResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/repositories`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token: request.token,
          page: request.page || 1,
          per_page: request.per_page || 30,
          sort: request.sort || "updated",
          direction: request.direction || "desc",
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `Failed to fetch repositories: ${response.status} ${
            response.statusText
          }${errorData.detail ? ` - ${errorData.detail}` : ""}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Error fetching repositories:", error);
      throw error;
    }
  }

  static async getPullRequests(
    request: GetPullRequestsRequest
  ): Promise<GetPullRequestsResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/pull_requests`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token: request.token,
          repo_owner: request.repo_owner,
          repo_name: request.repo_name,
          page: request.page || 1,
          per_page: request.per_page || 30,
          state: request.state || "all",
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `Failed to fetch pull requests: ${response.status} ${
            response.statusText
          }${errorData.detail ? ` - ${errorData.detail}` : ""}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Error fetching pull requests:", error);
      throw error;
    }
  }

  static async getPullRequestFiles(
    request: GetPullRequestFilesRequest
  ): Promise<GetPullRequestFilesResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/pull_requests/files`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token: request.token,
          pr_id: request.pr_id,
          repo_owner: request.repo_owner,
          repo_name: request.repo_name,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `Failed to fetch pull request files: ${response.status} ${
            response.statusText
          }${errorData.detail ? ` - ${errorData.detail}` : ""}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Error fetching pull request files:", error);
      throw error;
    }
  }

  static async getPullRequestComments(
    request: GetPullRequestCommentsRequest
  ): Promise<GetPullRequestCommentsResponse> {
    try {
      const response = await fetch(`${API_BASE_URL}/pull_requests/comments`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          token: request.token,
          pr_id: request.pr_id,
          repo_owner: request.repo_owner,
          repo_name: request.repo_name,
          page: request.page || 1,
          per_page: request.per_page || 30,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `Failed to fetch pull request comments: ${response.status} ${
            response.statusText
          }${errorData.detail ? ` - ${errorData.detail}` : ""}`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Error fetching pull request comments:", error);
      throw error;
    }
  }

  static async postPullRequestComment(
    request: PostPullRequestCommentRequest
  ): Promise<PostPullRequestCommentResponse> {
    try {
      const response = await fetch(
        `${API_BASE_URL}/pull_requests/comments/create`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify({
            token: request.token,
            pr_id: request.pr_id,
            repo_owner: request.repo_owner,
            repo_name: request.repo_name,
            body: request.body,
          }),
        }
      );

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(
          `Failed to post comment: ${response.status} ${response.statusText}${
            errorData.detail ? ` - ${errorData.detail}` : ""
          }`
        );
      }

      return await response.json();
    } catch (error) {
      console.error("Error posting comment:", error);
      throw error;
    }
  }
}
