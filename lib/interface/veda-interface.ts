export interface VedaRequest {
  pr_id: number;
  repo_owner: string;
  repo_name: string;
  user_comment: string;
  user_login: string;
}

export interface VedaResponse {
  task_id: string;
  status: string;
  message: string;
  analysis_started: boolean;
  estimated_completion_time?: string;
  websocket_url?: string;
}
