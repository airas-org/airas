import React, { useState, useEffect } from 'react';
import { Play, Pause, Trash2, Eye, Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react';
import { Job } from '../types/job';
import { apiService } from '../services/api';

interface JobListProps {
  jobs: Job[];
  onJobsChange: () => void;
  onJobSelect: (job: Job) => void;
}

export const JobList: React.FC<JobListProps> = ({ jobs, onJobsChange, onJobSelect }) => {
  const [loading, setLoading] = useState<string | null>(null);
  
  // Ensure jobs is always an array
  const safeJobs = Array.isArray(jobs) ? jobs : [];

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'running':
        return <Play className="w-4 h-4 text-blue-500" />;
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      case 'cancelled':
        return <Pause className="w-4 h-4 text-gray-500" />;
      default:
        return <AlertCircle className="w-4 h-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'running':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'completed':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'failed':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const handleCancel = async (jobId: string) => {
    if (!window.confirm('Are you sure you want to cancel this job?')) return;
    
    setLoading(jobId);
    try {
      await apiService.cancelJob(jobId);
      onJobsChange();
    } catch (error) {
      console.error('Failed to cancel job:', error);
      alert('Failed to cancel job');
    } finally {
      setLoading(null);
    }
  };

  const handleDelete = async (jobId: string) => {
    if (!window.confirm('Are you sure you want to delete this job?')) return;
    
    setLoading(jobId);
    try {
      await apiService.deleteJob(jobId);
      onJobsChange();
    } catch (error) {
      console.error('Failed to delete job:', error);
      alert('Failed to delete job');
    } finally {
      setLoading(null);
    }
  };

  const formatDate = (dateString: string | null) => {
    if (!dateString) return '-';
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (startTime: string | null, endTime: string | null) => {
    if (!startTime) return '-';
    
    const start = new Date(startTime);
    const end = endTime ? new Date(endTime) : new Date();
    const diff = end.getTime() - start.getTime();
    
    const hours = Math.floor(diff / (1000 * 60 * 60));
    const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
    const seconds = Math.floor((diff % (1000 * 60)) / 1000);
    
    if (hours > 0) return `${hours}h ${minutes}m ${seconds}s`;
    if (minutes > 0) return `${minutes}m ${seconds}s`;
    return `${seconds}s`;
  };

  return (
    <div className="bg-white rounded-xl shadow-lg overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-xl font-bold text-gray-800">Jobs</h2>
      </div>
      
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Job ID
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Repository
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Progress
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Duration
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {safeJobs.map((job) => (
              <tr key={job.job_id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm font-medium text-gray-900">
                    {job.job_id.split('-')[0]}...
                  </div>
                  <div className="text-sm text-gray-500">
                    {formatDate(job.created_at)}
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(job.status)}`}>
                    {getStatusIcon(job.status)}
                    <span className="ml-1 capitalize">{job.status}</span>
                  </span>
                  {job.current_step && (
                    <div className="text-xs text-gray-500 mt-1">
                      Step: {job.current_step}
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="text-sm text-gray-900">{job.github_repository}</div>
                  <div className="text-sm text-gray-500">{job.branch_name}</div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                      style={{ width: `${(job.progress || 0) * 100}%` }}
                    />
                  </div>
                  <div className="text-xs text-gray-500 mt-1">
                    {Math.round((job.progress || 0) * 100)}%
                  </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {formatDuration(job.started_at, job.completed_at)}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  <div className="flex space-x-2">
                    <button
                      onClick={() => onJobSelect(job)}
                      className="text-blue-600 hover:text-blue-900 transition-colors"
                      title="View Details"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    {job.status === 'running' && (
                      <button
                        onClick={() => handleCancel(job.job_id)}
                        disabled={loading === job.job_id}
                        className="text-yellow-600 hover:text-yellow-900 disabled:opacity-50 transition-colors"
                        title="Cancel Job"
                      >
                        <Pause className="w-4 h-4" />
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(job.job_id)}
                      disabled={loading === job.job_id}
                      className="text-red-600 hover:text-red-900 disabled:opacity-50 transition-colors"
                      title="Delete Job"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        
        {safeJobs.length === 0 && (
          <div className="text-center py-12">
            <div className="text-gray-500">No jobs found</div>
          </div>
        )}
      </div>
    </div>
  );
};