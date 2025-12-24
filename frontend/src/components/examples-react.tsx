/**
 * ReactコンポーネントでのAPIクライアント使用例
 * 
 * このファイルは、生成されたAPIクライアントをReactコンポーネントで
 * 使用する実践的な例を示しています。
 */

import { useState, useCallback } from 'react';
import { 
  PapersService, 
  BibfileService,
  OpenAPI,
  type RetrievePaperSubgraphRequestBody,
  type RetrievePaperSubgraphResponseBody,
  type GenerateBibfileSubgraphRequestBody,
} from '../lib/api/index';

// ============================================
// 1. 論文検索コンポーネントの例
// ============================================

/**
 * 論文検索コンポーネントの例
 */
export function PaperSearchExample() {
  const [queries, setQueries] = useState<string[]>(['']);
  const [maxResults, setMaxResults] = useState(10);
  const [loading, setLoading] = useState(false);
  const [papers, setPapers] = useState<RetrievePaperSubgraphResponseBody | null>(null);
  const [error, setError] = useState<string | null>(null);

  // APIのベースURLを設定（初回のみ）
  useState(() => {
    OpenAPI.BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  });

  const handleSearch = useCallback(async () => {
    setLoading(true);
    setError(null);
    setPapers(null);

    try {
      const requestBody: RetrievePaperSubgraphRequestBody = {
        query_list: queries.filter(q => q.trim() !== ''),
        max_results_per_query: maxResults,
      };

      const response = await PapersService.getPaperTitleAirasV1PapersGet(requestBody);
      setPapers(response);
    } catch (err: any) {
      setError(err.message || '論文の検索に失敗しました');
      console.error('論文検索エラー:', err);
    } finally {
      setLoading(false);
    }
  }, [queries, maxResults]);

  const addQuery = useCallback(() => {
    setQueries([...queries, '']);
  }, [queries]);

  const updateQuery = useCallback((index: number, value: string) => {
    const newQueries = [...queries];
    newQueries[index] = value;
    setQueries(newQueries);
  }, [queries]);

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">論文検索</h2>
      
      <div className="space-y-2">
        {queries.map((query, index) => (
          <input
            key={index}
            type="text"
            value={query}
            onChange={(e) => updateQuery(index, e.target.value)}
            placeholder={`検索クエリ ${index + 1}`}
            className="w-full p-2 border rounded"
          />
        ))}
        <button
          onClick={addQuery}
          className="px-4 py-2 bg-gray-200 rounded hover:bg-gray-300"
        >
          + クエリを追加
        </button>
      </div>

      <div className="flex items-center gap-2">
        <label>
          最大結果数:
          <input
            type="number"
            value={maxResults}
            onChange={(e) => setMaxResults(Number(e.target.value))}
            min={1}
            max={100}
            className="ml-2 p-1 border rounded w-20"
          />
        </label>
        <button
          onClick={handleSearch}
          disabled={loading || queries.every(q => q.trim() === '')}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
        >
          {loading ? '検索中...' : '検索'}
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-100 text-red-700 rounded">
          エラー: {error}
        </div>
      )}

      {papers && (
        <div className="p-3 bg-green-100 rounded">
          <h3 className="font-bold mb-2">検索結果:</h3>
          <pre className="text-sm overflow-auto">
            {JSON.stringify(papers, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

// ============================================
// 2. カスタムフックの例
// ============================================

/**
 * 論文検索用のカスタムフック
 */
export function usePaperSearch() {
  const [papers, setPapers] = useState<RetrievePaperSubgraphResponseBody | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const searchPapers = useCallback(async (queries: string[], maxResults = 10) => {
    setLoading(true);
    setError(null);
    setPapers(null);

    try {
      const requestBody: RetrievePaperSubgraphRequestBody = {
        query_list: queries.filter(q => q.trim() !== ''),
        max_results_per_query: maxResults,
      };

      const response = await PapersService.getPaperTitleAirasV1PapersGet(requestBody);
      setPapers(response);
      return response;
    } catch (err) {
      const error = err as Error;
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  return { papers, loading, error, searchPapers };
}

/**
 * Bibfile生成用のカスタムフック
 */
export function useBibfileGeneration() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [bibfile, setBibfile] = useState<string | null>(null);

  const generateBibfile = useCallback(async (researchStudyList: any[]) => {
    setLoading(true);
    setError(null);
    setBibfile(null);

    try {
      const requestBody: GenerateBibfileSubgraphRequestBody = {
        research_study_list: researchStudyList,
      };

      const response = await BibfileService.generateBibfileAirasV1BibfileGenerationsPost(requestBody);
      setBibfile(response.references_bib || null);
      return response;
    } catch (err) {
      const error = err as Error;
      setError(error);
      throw error;
    } finally {
      setLoading(false);
    }
  }, []);

  return { bibfile, loading, error, generateBibfile };
}

// ============================================
// 3. カスタムフックを使用したコンポーネント例
// ============================================

/**
 * カスタムフックを使用したコンポーネント例
 */
export function PaperSearchWithHook() {
  const [query, setQuery] = useState('');
  const { papers, loading, error, searchPapers } = usePaperSearch();

  const handleSearch = useCallback(() => {
    if (query.trim()) {
      searchPapers([query], 10);
    }
  }, [query, searchPapers]);

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">論文検索（フック使用）</h2>
      
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="検索クエリを入力"
          className="flex-1 p-2 border rounded"
        />
        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
        >
          {loading ? '検索中...' : '検索'}
        </button>
      </div>

      {error && (
        <div className="p-3 bg-red-100 text-red-700 rounded">
          エラー: {error.message}
        </div>
      )}

      {papers && (
        <div className="p-3 bg-green-100 rounded">
          <h3 className="font-bold mb-2">検索結果:</h3>
          <pre className="text-sm overflow-auto">
            {JSON.stringify(papers, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

// ============================================
// 4. エラーハンドリング付きコンポーネント例
// ============================================

/**
 * 詳細なエラーハンドリングを含むコンポーネント例
 */
export function PaperSearchWithErrorHandling() {
  const [query, setQuery] = useState('');
  const [papers, setPapers] = useState<RetrievePaperSubgraphResponseBody | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<{ message: string; status?: number } | null>(null);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setPapers(null);

    try {
      const requestBody: RetrievePaperSubgraphRequestBody = {
        query_list: [query],
        max_results_per_query: 10,
      };

      const response = await PapersService.getPaperTitleAirasV1PapersGet(requestBody);
      setPapers(response);
    } catch (err: any) {
      // エラーの種類に応じた処理
      if (err.status === 422) {
        setError({
          message: '入力データが不正です。検索クエリを確認してください。',
          status: 422,
        });
      } else if (err.status === 404) {
        setError({
          message: 'APIエンドポイントが見つかりません。',
          status: 404,
        });
      } else if (err.status >= 500) {
        setError({
          message: 'サーバーエラーが発生しました。しばらくしてから再試行してください。',
          status: err.status,
        });
      } else {
        setError({
          message: err.message || '予期しないエラーが発生しました。',
        });
      }
    } finally {
      setLoading(false);
    }
  }, [query]);

  return (
    <div className="p-4 space-y-4">
      <h2 className="text-xl font-bold">論文検索（エラーハンドリング付き）</h2>
      
      <div className="flex gap-2">
        <input
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          placeholder="検索クエリを入力"
          className="flex-1 p-2 border rounded"
        />
        <button
          onClick={handleSearch}
          disabled={loading || !query.trim()}
          className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:bg-gray-400"
        >
          {loading ? '検索中...' : '検索'}
        </button>
      </div>

      {error && (
        <div className={`p-3 rounded ${
          error.status === 422 
            ? 'bg-yellow-100 text-yellow-700'
            : error.status && error.status >= 500
            ? 'bg-red-100 text-red-700'
            : 'bg-red-100 text-red-700'
        }`}>
          <div className="font-bold">エラー</div>
          <div>{error.message}</div>
          {error.status && (
            <div className="text-sm mt-1">ステータスコード: {error.status}</div>
          )}
        </div>
      )}

      {papers && (
        <div className="p-3 bg-green-100 rounded">
          <h3 className="font-bold mb-2">検索結果:</h3>
          <pre className="text-sm overflow-auto">
            {JSON.stringify(papers, null, 2)}
          </pre>
        </div>
      )}
    </div>
  );
}

