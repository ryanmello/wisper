// ========================================
// GITHUB API MODELS
// ========================================

export interface GitHubRepository {
  id: number;
  name: string;
  full_name: string;
  description?: string;
  language?: string;
  stargazers_count: number;
  forks_count: number;
  updated_at: string;
  private: boolean;
}

export interface GetRepositoriesRequest {
  page?: number;
  per_page?: number;
  sort?: string;
  direction?: string;
}

export interface GetRepositoriesResponse {
  total_count: number;
  repositories: GitHubRepository[];
  page: number;
  per_page: number;
}

export interface GitHubUser {
  login: string;
  avatar_url: string;
}

export interface GitHubLabel {
  name: string;
  color: string;
}

export interface GitHubPullRequest {
  id: number;
  title: string;
  state: string;
  repository: {
    name: string;
    full_name: string;
    owner: string;
  };
  created_at: string;
  updated_at: string;
  html_url: string;
  user: GitHubUser;
  comments: number;
  labels: GitHubLabel[];
}

export interface GetPullRequestsRequest {
  repo_owner: string;
  repo_name: string;
  page?: number;
  per_page?: number;
  state?: string;
}

export interface GetPullRequestsResponse {
  total_count: number;
  items: GitHubPullRequest[];
  page: number;
  per_page: number;
}

export interface GitHubFileChange {
  filename: string;
  status: string;
  additions: number;
  deletions: number;
  changes: number;
  patch: string;
  previous_filename?: string;
  blob_url: string;
  raw_url: string;
}

export interface GetPullRequestFilesRequest {
  pr_id: number;
  repo_owner: string;
  repo_name: string;
}

export interface GetPullRequestFilesResponse {
  pr_id: number;
  repository: string;
  files: GitHubFileChange[];
  total_files: number;
}

export interface GitHubComment {
  id: number;
  body: string;
  user: GitHubUser;
  created_at: string;
  updated_at: string;
  html_url: string;
}

export interface GetPullRequestCommentsRequest {
  pr_id: number;
  repo_owner: string;
  repo_name: string;
  page?: number;
  per_page?: number;
}

export interface GetPullRequestCommentsResponse {
  pr_id: number;
  repository: string;
  comments: GitHubComment[];
  page: number;
  per_page: number;
}

export interface PostPullRequestCommentRequest {
  pr_id: number;
  repo_owner: string;
  repo_name: string;
  body: string;
}

export interface PostPullRequestCommentResponse {
  comment: GitHubComment;
}
