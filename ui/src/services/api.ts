const API_BASE_URL = 'http://localhost:8000';

export class ApiService {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      const error = await response.text();
      throw new Error(`API Error: ${response.status} - ${error}`);
    }

    return response.json();
  }

  async createJob(jobData: any): Promise<any> {
    return this.request('/jobs/', {
      method: 'POST',
      body: JSON.stringify(jobData),
    });
  }

  async getJob(jobId: string): Promise<any> {
    return this.request(`/jobs/${jobId}`);
  }

  async getJobs(limit: number = 100): Promise<any[]> {
    return this.request(`/jobs/?limit=${limit}`);
  }

  async deleteJob(jobId: string): Promise<void> {
    return this.request(`/jobs/${jobId}`, {
      method: 'DELETE',
    });
  }

  async cancelJob(jobId: string): Promise<void> {
    return this.request(`/jobs/${jobId}/cancel`, {
      method: 'POST',
    });
  }

  async getJobResult(jobId: string): Promise<any> {
    return this.request(`/jobs/${jobId}/result`);
  }

  async getStatistics(): Promise<any> {
    return this.request('/statistics');
  }

  async cleanup(days: number = 30): Promise<void> {
    return this.request(`/cleanup?days=${days}`, {
      method: 'POST',
    });
  }
}

export const apiService = new ApiService();