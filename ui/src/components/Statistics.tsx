import React, { useState, useEffect } from 'react';
import { BarChart3, TrendingUp, Clock, CheckCircle, XCircle, AlertCircle, Users } from 'lucide-react';
import { JobStatistics } from '../types/job';
import { apiService } from '../services/api';

export const Statistics: React.FC = () => {
  const [stats, setStats] = useState<JobStatistics | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatistics();
  }, []);

  const fetchStatistics = async () => {
    try {
      const data = await apiService.getStatistics();
      setStats(data);
    } catch (err) {
      setError('Failed to fetch statistics');
    } finally {
      setLoading(false);
    }
  };

  const handleCleanup = async () => {
    if (!window.confirm('Are you sure you want to clean up jobs older than 30 days?')) return;
    
    try {
      await apiService.cleanup(30);
      fetchStatistics(); // Refresh stats
      alert('Cleanup completed successfully');
    } catch (err) {
      alert('Failed to cleanup jobs');
    }
  };

  if (loading) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="bg-white rounded-xl shadow-lg p-8">
        <div className="text-center text-red-600">{error || 'No statistics available'}</div>
      </div>
    );
  }

  const formatDuration = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = Math.floor(seconds % 60);
    
    if (hours > 0) return `${hours}h ${minutes}m ${remainingSeconds}s`;
    if (minutes > 0) return `${minutes}m ${remainingSeconds}s`;
    return `${remainingSeconds}s`;
  };

  const statItems = [
    {
      title: 'Total Jobs',
      value: stats.total_jobs,
      icon: <Users className="w-6 h-6 text-blue-600" />,
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600'
    },
    {
      title: 'Pending',
      value: stats.pending_jobs,
      icon: <Clock className="w-6 h-6 text-yellow-600" />,
      bgColor: 'bg-yellow-50',
      textColor: 'text-yellow-600'
    },
    {
      title: 'Running',
      value: stats.running_jobs,
      icon: <BarChart3 className="w-6 h-6 text-blue-600" />,
      bgColor: 'bg-blue-50',
      textColor: 'text-blue-600'
    },
    {
      title: 'Completed',
      value: stats.completed_jobs,
      icon: <CheckCircle className="w-6 h-6 text-green-600" />,
      bgColor: 'bg-green-50',
      textColor: 'text-green-600'
    },
    {
      title: 'Failed',
      value: stats.failed_jobs,
      icon: <XCircle className="w-6 h-6 text-red-600" />,
      bgColor: 'bg-red-50',
      textColor: 'text-red-600'
    },
    {
      title: 'Cancelled',
      value: stats.cancelled_jobs,
      icon: <AlertCircle className="w-6 h-6 text-gray-600" />,
      bgColor: 'bg-gray-50',
      textColor: 'text-gray-600'
    }
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-lg p-6">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-800">Statistics</h2>
          <button
            onClick={handleCleanup}
            className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
          >
            Cleanup Old Jobs
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {statItems.map((item) => (
            <div
              key={item.title}
              className={`${item.bgColor} rounded-lg p-6 border border-gray-200`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm font-medium text-gray-600">{item.title}</p>
                  <p className={`text-2xl font-bold ${item.textColor}`}>{item.value}</p>
                </div>
                <div className={`p-3 rounded-full ${item.bgColor}`}>
                  {item.icon}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center mb-4">
            <TrendingUp className="w-6 h-6 text-green-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">Success Rate</h3>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-green-600 mb-2">
              {Math.round(stats.success_rate * 100)}%
            </div>
            <p className="text-gray-600">Jobs completed successfully</p>
          </div>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          <div className="flex items-center mb-4">
            <Clock className="w-6 h-6 text-blue-600 mr-2" />
            <h3 className="text-lg font-semibold text-gray-800">Average Duration</h3>
          </div>
          <div className="text-center">
            <div className="text-4xl font-bold text-blue-600 mb-2">
              {formatDuration(stats.average_duration)}
            </div>
            <p className="text-gray-600">Per job completion</p>
          </div>
        </div>
      </div>
    </div>
  );
};