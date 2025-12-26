/**
 * APIクライアントの使用例
 * 
 * このファイルは、生成されたAPIクライアントの使用方法を示す例です。
 * 実際のプロジェクトでは、これらの例を参考にコンポーネントやサービス層で使用してください。
 */

import { 
  PapersService, 
  BibfileService, 
  OpenAPI,
  type RetrievePaperSubgraphRequestBody,
  type GenerateBibfileSubgraphRequestBody,
} from './index';

// ============================================
// 1. 基本的な設定
// ============================================

/**
 * APIのベースURLを設定する例
 * 通常は環境変数や設定ファイルから読み込む
 */
export function configureApi() {
  OpenAPI.BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  // 認証トークンがある場合
  // OpenAPI.TOKEN = 'your-auth-token';
}

// ============================================
// 2. 論文検索の例
// ============================================

/**
 * 論文を検索する例（async/await）
 */
export async function searchPapersExample() {
  try {
    const requestBody: RetrievePaperSubgraphRequestBody = {
      query_list: ['machine learning', 'deep learning'],
      max_results_per_query: 10,
    };

    const response = await PapersService.getPaperTitleAirasV1PapersGet(requestBody);
    console.log('検索結果:', response);
    return response;
  } catch (error) {
    console.error('論文検索エラー:', error);
    throw error;
  }
}

/**
 * 論文を検索する例（Promise）
 */
export function searchPapersPromiseExample() {
  const requestBody: RetrievePaperSubgraphRequestBody = {
    query_list: ['transformer', 'attention mechanism'],
    max_results_per_query: 5,
  };

  return PapersService.getPaperTitleAirasV1PapersGet(requestBody)
    .then((response) => {
      console.log('検索結果:', response);
      return response;
    })
    .catch((error) => {
      console.error('論文検索エラー:', error);
      throw error;
    });
}

// ============================================
// 3. Bibfile生成の例
// ============================================

/**
 * Bibfileを生成する例
 */
export async function generateBibfileExample(researchStudyList: any[]) {
  try {
    const requestBody: GenerateBibfileSubgraphRequestBody = {
      research_study_list: researchStudyList,
    };

    const response = await BibfileService.generateBibfileAirasV1BibfileGenerationsPost(requestBody);
    console.log('生成されたBibfile:', response);
    return response;
  } catch (error) {
    console.error('Bibfile生成エラー:', error);
    throw error;
  }
}

// ============================================
// 4. Reactコンポーネントでの使用例
// ============================================

/**
 * Reactコンポーネントでの使用例（フック形式）
 * 
 * 実際のコンポーネントでは以下のように使用できます：
 * 
 * ```tsx
 * import { useState } from 'react';
 * import { searchPapersExample } from '@/lib/api/examples';
 * 
 * function PaperSearchComponent() {
 *   const [loading, setLoading] = useState(false);
 *   const [papers, setPapers] = useState(null);
 *   const [error, setError] = useState(null);
 * 
 *   const handleSearch = async () => {
 *     setLoading(true);
 *     setError(null);
 *     try {
 *       const result = await searchPapersExample();
 *       setPapers(result);
 *     } catch (err) {
 *       setError(err);
 *     } finally {
 *       setLoading(false);
 *     }
 *   };
 * 
 *   return (
 *     <div>
 *       <button onClick={handleSearch} disabled={loading}>
 *         {loading ? '検索中...' : '論文を検索'}
 *       </button>
 *       {error && <div>エラー: {error.message}</div>}
 *       {papers && <div>結果: {JSON.stringify(papers)}</div>}
 *     </div>
 *   );
 * }
 * ```
 */

// ============================================
// 5. カスタムフックの例
// ============================================

/**
 * 論文検索用のカスタムフック例
 * 
 * 使用例：
 * ```tsx
 * function MyComponent() {
 *   const { papers, loading, error, searchPapers } = usePaperSearch();
 * 
 *   return (
 *     <div>
 *       <button onClick={() => searchPapers(['machine learning'])}>
 *         検索
 *       </button>
 *       {loading && <div>読み込み中...</div>}
 *       {error && <div>エラー: {error.message}</div>}
 *       {papers && <div>結果: {papers.length}件</div>}
 *     </div>
 *   );
 * }
 * ```
 */
export function usePaperSearch() {
  // この例では型定義のみ。実際の実装ではReact hooksを使用
  // import { useState, useCallback } from 'react';
  
  // const [papers, setPapers] = useState<RetrievePaperSubgraphResponseBody | null>(null);
  // const [loading, setLoading] = useState(false);
  // const [error, setError] = useState<Error | null>(null);
  
  // const searchPapers = useCallback(async (queries: string[], maxResults = 10) => {
  //   setLoading(true);
  //   setError(null);
  //   try {
  //     const requestBody: RetrievePaperSubgraphRequestBody = {
  //       query_list: queries,
  //       max_results_per_query: maxResults,
  //     };
  //     const response = await PapersService.getPaperTitleAirasV1PapersGet(requestBody);
  //     setPapers(response);
  //   } catch (err) {
  //     setError(err as Error);
  //   } finally {
  //     setLoading(false);
  //   }
  // }, []);
  
  // return { papers, loading, error, searchPapers };
}

// ============================================
// 6. エラーハンドリングの例
// ============================================

/**
 * エラーハンドリングの詳細例
 */
export async function searchPapersWithErrorHandling() {
  try {
    const requestBody: RetrievePaperSubgraphRequestBody = {
      query_list: ['test query'],
      max_results_per_query: 5,
    };

    const response = await PapersService.getPaperTitleAirasV1PapersGet(requestBody);
    return { success: true, data: response };
  } catch (error: any) {
    // エラーの種類に応じた処理
    if (error.status === 422) {
      console.error('バリデーションエラー:', error.body);
      return { success: false, error: '入力データが不正です', details: error.body };
    } else if (error.status === 404) {
      console.error('リソースが見つかりません');
      return { success: false, error: 'リソースが見つかりません' };
    } else if (error.status >= 500) {
      console.error('サーバーエラー:', error);
      return { success: false, error: 'サーバーエラーが発生しました' };
    } else {
      console.error('予期しないエラー:', error);
      return { success: false, error: '予期しないエラーが発生しました' };
    }
  }
}

// ============================================
// 7. リクエストのキャンセル例
// ============================================

/**
 * リクエストをキャンセルする例
 * 
 * 使用例：
 * ```tsx
 * function SearchComponent() {
 *   const cancelRef = useRef<(() => void) | null>(null);
 * 
 *   const handleSearch = () => {
 *     const promise = PapersService.getPaperTitleAirasV1PapersGet({...});
 *     cancelRef.current = promise.cancel;
 *     
 *     promise.then(result => {
 *       console.log(result);
 *     });
 *   };
 * 
 *   const handleCancel = () => {
 *     if (cancelRef.current) {
 *       cancelRef.current();
 *       cancelRef.current = null;
 *     }
 *   };
 * 
 *   return (
 *     <div>
 *       <button onClick={handleSearch}>検索</button>
 *       <button onClick={handleCancel}>キャンセル</button>
 *     </div>
 *   );
 * }
 * ```
 */


