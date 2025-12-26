# APIクライアント使用ガイド

このディレクトリには、OpenAPIスキーマから自動生成されたTypeScriptのAPIクライアントが含まれています。

## 基本的な使い方

### 1. インポート

```typescript
import { 
  PapersService, 
  BibfileService,
  ModelsService,
  OpenAPI,
  type RetrievePaperSubgraphRequestBody,
  type RetrievePaperSubgraphResponseBody,
} from '@/lib/api';
```

### 2. APIのベースURLを設定

```typescript
// 環境変数から読み込む（推奨）
OpenAPI.BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// または直接設定
OpenAPI.BASE = 'https://api.example.com';
```

### 3. APIを呼び出す

#### async/await パターン

```typescript
async function searchPapers() {
  try {
    const requestBody: RetrievePaperSubgraphRequestBody = {
      query_list: ['machine learning'],
      max_results_per_query: 10,
    };

    const response = await PapersService.getPaperTitleAirasV1PapersGet(requestBody);
    console.log('結果:', response);
    return response;
  } catch (error) {
    console.error('エラー:', error);
    throw error;
  }
}
```

#### Promise パターン

```typescript
function searchPapers() {
  const requestBody: RetrievePaperSubgraphRequestBody = {
    query_list: ['deep learning'],
    max_results_per_query: 5,
  };

  return PapersService.getPaperTitleAirasV1PapersGet(requestBody)
    .then((response) => {
      console.log('結果:', response);
      return response;
    })
    .catch((error) => {
      console.error('エラー:', error);
      throw error;
    });
}
```

## Reactコンポーネントでの使用

### 基本的な例

```tsx
import { useState } from 'react';
import { PapersService, OpenAPI } from '@/lib/api';

function PaperSearchComponent() {
  const [loading, setLoading] = useState(false);
  const [papers, setPapers] = useState(null);
  const [error, setError] = useState(null);

  // 初回のみAPIのベースURLを設定
  useState(() => {
    OpenAPI.BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
  });

  const handleSearch = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await PapersService.getPaperTitleAirasV1PapersGet({
        query_list: ['machine learning'],
        max_results_per_query: 10,
      });
      setPapers(response);
    } catch (err) {
      setError(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <button onClick={handleSearch} disabled={loading}>
        {loading ? '検索中...' : '検索'}
      </button>
      {error && <div>エラー: {error.message}</div>}
      {papers && <div>結果: {JSON.stringify(papers)}</div>}
    </div>
  );
}
```

### カスタムフックを使用する例

```tsx
import { usePaperSearch } from '@/lib/api/examples-react';

function MyComponent() {
  const { papers, loading, error, searchPapers } = usePaperSearch();

  return (
    <div>
      <button onClick={() => searchPapers(['machine learning'], 10)}>
        検索
      </button>
      {loading && <div>読み込み中...</div>}
      {error && <div>エラー: {error.message}</div>}
      {papers && <div>結果: {papers.length}件</div>}
    </div>
  );
}
```

## 利用可能なサービス

以下のサービスが利用可能です：

- `PapersService` - 論文関連のAPI
- `BibfileService` - Bibfile生成のAPI
- `ModelsService` - モデル関連のAPI
- `DatasetsService` - データセット関連のAPI
- `HypothesesService` - 仮説関連のAPI
- `ExperimentalSettingsService` - 実験設定関連のAPI
- `ExperimentsService` - 実験関連のAPI
- `CodeService` - コード関連のAPI
- `RepositoriesService` - リポジトリ関連のAPI
- `LatexService` - LaTeX関連のAPI
- `ResearchHistoryService` - 研究履歴関連のAPI
- `GithubActionsService` - GitHub Actions関連のAPI

各サービスのメソッドは、OpenAPIスキーマに基づいて自動生成されています。

## エラーハンドリング

```typescript
try {
  const response = await PapersService.getPaperTitleAirasV1PapersGet(requestBody);
  // 成功時の処理
} catch (error: any) {
  if (error.status === 422) {
    // バリデーションエラー
    console.error('入力データが不正です:', error.body);
  } else if (error.status === 404) {
    // リソースが見つからない
    console.error('リソースが見つかりません');
  } else if (error.status >= 500) {
    // サーバーエラー
    console.error('サーバーエラー:', error);
  } else {
    // その他のエラー
    console.error('予期しないエラー:', error);
  }
}
```

## リクエストのキャンセル

リクエストは `CancelablePromise` を返すため、キャンセル可能です：

```typescript
const promise = PapersService.getPaperTitleAirasV1PapersGet(requestBody);

// キャンセル
promise.cancel();
```

## 型安全性

すべてのリクエストとレスポンスは型定義されています：

```typescript
import type { 
  RetrievePaperSubgraphRequestBody,
  RetrievePaperSubgraphResponseBody,
} from '@/lib/api';

// 型安全なリクエスト
const requestBody: RetrievePaperSubgraphRequestBody = {
  query_list: ['test'],
  max_results_per_query: 10,
};

// 型安全なレスポンス
const response: RetrievePaperSubgraphResponseBody = await PapersService
  .getPaperTitleAirasV1PapersGet(requestBody);
```

## 詳細な例

より詳細な使用例については、以下のファイルを参照してください：

- `examples.ts` - 基本的な使用例
- `examples-react.tsx` - Reactコンポーネントでの使用例

## 注意事項

- このディレクトリ内のファイルは自動生成されているため、直接編集しないでください
- APIスキーマを更新した場合は、`make generate-openapi` を実行してから、フロントエンドのAPIクライアントを再生成してください
- 環境変数 `VITE_API_BASE_URL` を設定することで、APIのベースURLを変更できます


