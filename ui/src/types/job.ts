export interface Job {
  job_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  current_step: string | null;
  progress: number;
  result: any;
  error: string | null;
  github_repository?: string;
  branch_name?: string;
  base_queries?: string[];
  save_dir?: string;
  file_path?: string | null;
  llm_name?: string;
  scrape_urls?: string[];
}

export interface JobCreateRequest {
  github_repository: string;
  branch_name: string;
  base_queries: string[];
  save_dir: string;
  file_path?: string | null;
  llm_name: string;
  scrape_urls: string[];
}

export interface JobStatistics {
  total_jobs: number;
  pending_jobs: number;
  running_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  cancelled_jobs: number;
  average_duration: number;
  success_rate: number;
}

export interface CreateJobResponse {
  job_id: string;
  status: string;
  message: string;
}