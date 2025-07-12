import React, { useState, useEffect } from 'react';
import { ArrowLeft, Download, RefreshCw, CheckCircle, Circle, Loader2 } from 'lucide-react';
import { Job } from '../types/job';
import { apiService } from '../services/api';

interface JobDetailProps {
  job: Job;
  onBack: () => void;
  onJobUpdate: (job: Job) => void;
}

const EXECUTION_STEPS = [
  'prepare',
  'retriever',
  'retriever2',
  'retriever3',
  'creator',
  'creator2',
  'coder',
  'executor',
  'fixer',
  'analysis',
  'writer',
  'citation',
  'latex',
  'readme',
  'html'
];

export const JobDetail: React.FC<JobDetailProps> = ({ job, onBack, onJobUpdate }) => {
  const [result, setResult] = useState<any>(null);
  const [loadingResult, setLoadingResult] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (job.status === 'completed') {
      fetchResult();
    }
  }, [job.status]);

  const fetchResult = async () => {
    setLoadingResult(true);
    setError(null);
    try {
      const resultData = await apiService.getJobResult(job.job_id);
      setResult(resultData);
    } catch (err) {
      setError('Failed to fetch job result');
    } finally {
      setLoadingResult(false);
    }
  };

  const getCurrentStepIndex = () => {
    if (!job.current_step) return -1;
    return EXECUTION_STEPS.indexOf(job.current_step);
  };

  const getStepStatus = (stepIndex: number) => {
    const currentIndex = getCurrentStepIndex();
    if (job.status === 'completed') return 'completed';
    if (job.status === 'failed') {
      return stepIndex <= currentIndex ? 'failed' : 'pending';
    }
    if (stepIndex < currentIndex) return 'completed';
    if (stepIndex === currentIndex) return 'running';
    return 'pending';
  };

  const getStepIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-green-500" />;
      case 'running':
        return <Loader2 className="w-5 h-5 text-blue-500 animate-spin" />;
      case 'failed':
        return <Circle className="w-5 h-5 text-red-500" />;
      default:
        return <Circle className="w-5 h-5 text-gray-300" />;
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
      <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
        <div className="flex items-center">
          <button
            onClick={onBack}
            className="mr-4 p-2 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <h2 className="text-xl font-bold text-gray-800">Job Details</h2>
        </div>
        {job.status === 'completed' && (
          <button
            onClick={fetchResult}
            disabled={loadingResult}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            {loadingResult ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            Load Result
          </button>
        )}
      </div>

      <div className="p-6 space-y-6">
        {/* Job Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">Job Information</h3>
            <div className="space-y-2">
              <div>
                <span className="text-sm text-gray-500">Job ID:</span>
                <p className="font-mono text-sm">{job.job_id}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Status:</span>
                <p className="capitalize font-medium">{job.status}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Repository:</span>
                <p>{job.github_repository}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Branch:</span>
                <p>{job.branch_name}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">LLM Model:</span>
                <p>{job.llm_name}</p>
              </div>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="text-lg font-semibold text-gray-800">Timing</h3>
            <div className="space-y-2">
              <div>
                <span className="text-sm text-gray-500">Created:</span>
                <p>{formatDate(job.created_at)}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Started:</span>
                <p>{formatDate(job.started_at)}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Completed:</span>
                <p>{formatDate(job.completed_at)}</p>
              </div>
              <div>
                <span className="text-sm text-gray-500">Duration:</span>
                <p>{formatDuration(job.started_at, job.completed_at)}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Base Queries */}
        {job.base_queries && job.base_queries.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold text-gray-800 mb-2">Base Queries</h3>
            <div className="flex flex-wrap gap-2">
              {job.base_queries.map((query, index) => (
                <span
                  key={index}
                  className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                >
                  {query}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Progress */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Progress</h3>
          <div className="w-full bg-gray-200 rounded-full h-3 mb-4">
            <div
              className="bg-blue-600 h-3 rounded-full transition-all duration-300"
              style={{ width: `${(job.progress || 0) * 100}%` }}
            />
          </div>
          <p className="text-sm text-gray-600 mb-4">
            {Math.round((job.progress || 0) * 100)}% Complete
          </p>
        </div>

        {/* Execution Steps */}
        <div>
          <h3 className="text-lg font-semibold text-gray-800 mb-4">Execution Steps</h3>
          <div className="space-y-3">
            {EXECUTION_STEPS.map((step, index) => {
              const status = getStepStatus(index);
              return (
                <div
                  key={step}
                  className={`flex items-center gap-3 p-3 rounded-lg transition-colors ${
                    status === 'running' ? 'bg-blue-50 border border-blue-200' : 
                    status === 'completed' ? 'bg-green-50 border border-green-200' :
                    status === 'failed' ? 'bg-red-50 border border-red-200' :
                    'bg-gray-50 border border-gray-200'
                  }`}
                >
                  {getStepIcon(status)}
                  <span className={`font-medium ${
                    status === 'running' ? 'text-blue-800' :
                    status === 'completed' ? 'text-green-800' :
                    status === 'failed' ? 'text-red-800' :
                    'text-gray-600'
                  }`}>
                    {step}
                  </span>
                  {status === 'running' && (
                    <span className="text-sm text-blue-600">Running...</span>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Error Display */}
        {job.error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-red-800 mb-2">Error</h3>
            <p className="text-red-700 whitespace-pre-wrap">{job.error}</p>
          </div>
        )}

        {/* Result Display */}
        {result && (
          <div className="bg-green-50 border border-green-200 rounded-lg p-4">
            <h3 className="text-lg font-semibold text-green-800 mb-2">Result</h3>
            <pre className="text-sm text-green-700 whitespace-pre-wrap overflow-x-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <p className="text-red-700">{error}</p>
          </div>
        )}
      </div>
    </div>
  );
};