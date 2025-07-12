import { useState, useEffect } from 'react';
import { RefreshCw, Plus, BarChart3, List } from 'lucide-react';
import { JobForm } from './components/JobForm';
import { JobList } from './components/JobList';
import { JobDetail } from './components/JobDetail';
import { Statistics } from './components/Statistics';
import { Job } from './types/job';
import { apiService } from './services/api';

type View = 'jobs' | 'create' | 'statistics' | 'detail';

function App() {
  const [view, setView] = useState<View>('jobs');
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchJobs();
    
    // Set up auto-refresh every 5 seconds
    const interval = setInterval(() => {
      if (view === 'jobs' || (view === 'detail' && selectedJob)) {
        fetchJobs();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [view, selectedJob]);

  const fetchJobs = async () => {
    try {
      const data = await apiService.getJobs();
      // APIレスポンスの構造に応じて適切に処理
      const jobsData = Array.isArray(data) ? data : ((data as any).jobs || []);
      setJobs(jobsData);
      
      // Update selected job if it exists
      if (selectedJob) {
        const updatedJob = jobsData.find((job: any) => job.job_id === selectedJob.job_id);
        if (updatedJob) {
          setSelectedJob(updatedJob);
        }
      }
      
      setError(null);
    } catch (err) {
      setError('Failed to fetch jobs');
    } finally {
      setLoading(false);
    }
  };

  const handleJobCreated = () => {
    fetchJobs();
    setView('jobs');
  };

  const handleJobSelect = (job: Job) => {
    setSelectedJob(job);
    setView('detail');
  };

  const handleJobUpdate = (job: Job) => {
    setSelectedJob(job);
    fetchJobs();
  };

  const navItems = [
    { key: 'jobs', label: 'Jobs', icon: List },
    { key: 'create', label: 'Create', icon: Plus },
    { key: 'statistics', label: 'Statistics', icon: BarChart3 },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <h1 className="text-xl font-bold text-gray-800">Airas E2E</h1>
            </div>
            
            <div className="flex space-x-1">
              {navItems.map((item) => (
                <button
                  key={item.key}
                  onClick={() => setView(item.key as View)}
                  className={`flex items-center px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                    view === item.key
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <item.icon className="w-4 h-4 mr-2" />
                  {item.label}
                </button>
              ))}
            </div>

            <button
              onClick={fetchJobs}
              disabled={loading}
              className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 transition-colors"
            >
              <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
            <div className="text-red-700">{error}</div>
          </div>
        )}

        {view === 'create' && (
          <JobForm onJobCreated={handleJobCreated} />
        )}

        {view === 'jobs' && (
          <JobList
            jobs={jobs}
            onJobsChange={fetchJobs}
            onJobSelect={handleJobSelect}
          />
        )}

        {view === 'statistics' && (
          <Statistics />
        )}

        {view === 'detail' && selectedJob && (
          <JobDetail
            job={selectedJob}
            onBack={() => setView('jobs')}
            onJobUpdate={handleJobUpdate}
          />
        )}
      </main>
    </div>
  );
}

export default App;