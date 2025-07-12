import React, { useState } from 'react';
import { Plus, Loader2, AlertCircle } from 'lucide-react';
import { apiService } from '../services/api';
import { JobCreateRequest } from '../types/job';

interface JobFormProps {
  onJobCreated: () => void;
}

export const JobForm: React.FC<JobFormProps> = ({ onJobCreated }) => {
  const [formData, setFormData] = useState<JobCreateRequest>({
    github_repository: '',
    branch_name: '',
    base_queries: [],
    save_dir: '',
    file_path: null,
    llm_name: 'gemini-2.0-flash-001',
    scrape_urls: []
  });

  const [baseQuery, setBaseQuery] = useState('');
  const [scrapeUrl, setScrapeUrl] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setSuccess(false);

    try {
      const submitData = {
        ...formData,
        save_dir: formData.save_dir || new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19)
      };

      await apiService.createJob(submitData);
      setSuccess(true);
      onJobCreated();
      
      // Reset form
      setFormData({
        github_repository: '',
        branch_name: '',
        base_queries: [],
        save_dir: '',
        file_path: null,
        llm_name: 'gemini-2.0-flash-001',
        scrape_urls: []
      });
      setBaseQuery('');
      setScrapeUrl('');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create job');
    } finally {
      setLoading(false);
    }
  };

  const addBaseQuery = () => {
    if (baseQuery.trim()) {
      setFormData(prev => ({
        ...prev,
        base_queries: [...prev.base_queries, baseQuery.trim()]
      }));
      setBaseQuery('');
    }
  };

  const removeBaseQuery = (index: number) => {
    setFormData(prev => ({
      ...prev,
      base_queries: prev.base_queries.filter((_, i) => i !== index)
    }));
  };

  const addScrapeUrl = () => {
    if (scrapeUrl.trim()) {
      setFormData(prev => ({
        ...prev,
        scrape_urls: [...prev.scrape_urls, scrapeUrl.trim()]
      }));
      setScrapeUrl('');
    }
  };

  const removeScrapeUrl = (index: number) => {
    setFormData(prev => ({
      ...prev,
      scrape_urls: prev.scrape_urls.filter((_, i) => i !== index)
    }));
  };

  return (
    <div className="bg-white rounded-xl shadow-lg p-8 mb-8">
      <div className="flex items-center mb-6">
        <Plus className="w-6 h-6 text-blue-600 mr-3" />
        <h2 className="text-2xl font-bold text-gray-800">Create New Job</h2>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-center">
          <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
          <span className="text-red-700">{error}</span>
        </div>
      )}

      {success && (
        <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg">
          <span className="text-green-700">Job created successfully!</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              GitHub Repository *
            </label>
            <input
              type="text"
              required
              value={formData.github_repository}
              onChange={(e) => setFormData(prev => ({ ...prev, github_repository: e.target.value }))}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="auto-res2/onda"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Branch Name *
            </label>
            <input
              type="text"
              required
              value={formData.branch_name}
              onChange={(e) => setFormData(prev => ({ ...prev, branch_name: e.target.value }))}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="main"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Save Directory
            </label>
            <input
              type="text"
              value={formData.save_dir}
              onChange={(e) => setFormData(prev => ({ ...prev, save_dir: e.target.value }))}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="Auto-generated if empty"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              LLM Model
            </label>
            <select
              value={formData.llm_name}
              onChange={(e) => setFormData(prev => ({ ...prev, llm_name: e.target.value }))}
              className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="gemini-2.0-flash-001">Gemini 2.0 Flash 001</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
            </select>
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Base Queries *
          </label>
          <div className="flex gap-2 mb-3">
            <input
              type="text"
              value={baseQuery}
              onChange={(e) => setBaseQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addBaseQuery())}
              className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="diffusion model"
            />
            <button
              type="button"
              onClick={addBaseQuery}
              className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Add
            </button>
          </div>
          <div className="flex flex-wrap gap-2">
            {formData.base_queries.map((query, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm flex items-center gap-1"
              >
                {query}
                <button
                  type="button"
                  onClick={() => removeBaseQuery(index)}
                  className="text-blue-600 hover:text-blue-800"
                >
                  ×
                </button>
              </span>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Scrape URLs
          </label>
          <div className="flex gap-2 mb-3">
            <input
              type="url"
              value={scrapeUrl}
              onChange={(e) => setScrapeUrl(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && (e.preventDefault(), addScrapeUrl())}
              className="flex-1 p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              placeholder="https://icml.cc/virtual/2024/papers.html?filter=title"
            />
            <button
              type="button"
              onClick={addScrapeUrl}
              className="px-4 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Add
            </button>
          </div>
          <div className="space-y-2">
            {formData.scrape_urls.map((url, index) => (
              <div
                key={index}
                className="flex items-center gap-2 p-2 bg-gray-50 rounded-lg"
              >
                <span className="flex-1 text-sm text-gray-700 truncate">{url}</span>
                <button
                  type="button"
                  onClick={() => removeScrapeUrl(index)}
                  className="text-red-600 hover:text-red-800"
                >
                  ×
                </button>
              </div>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            File Path (Optional)
          </label>
          <input
            type="text"
            value={formData.file_path || ''}
            onChange={(e) => setFormData(prev => ({ ...prev, file_path: e.target.value || null }))}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            placeholder="Path to specific file"
          />
        </div>

        <button
          type="submit"
          disabled={loading || formData.base_queries.length === 0}
          className="w-full bg-blue-600 text-white py-3 px-6 rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors flex items-center justify-center gap-2"
        >
          {loading ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Creating Job...
            </>
          ) : (
            <>
              <Plus className="w-5 h-5" />
              Create Job
            </>
          )}
        </button>
      </form>
    </div>
  );
};