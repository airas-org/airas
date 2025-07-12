# Airas E2E API

Airas E2E処理を実行するためのREST APIです。

## 概要

このAPIは、e2e.pyの処理をWeb APIとして提供します。長時間実行される処理を非同期で実行し、進捗状況を追跡できます。

## 起動方法

```bash
# 依存関係のインストール
pip install fastapi uvicorn

# APIサーバーの起動
python src/airas/services/web_api/app.py
```

または

```bash
uvicorn src.airas.services.web_api.app:app --host 0.0.0.0 --port 8000 --reload
```

## API エンドポイント

### 1. ジョブ作成

**POST** `/jobs/`

新しいE2Eジョブを作成します。

**リクエスト例:**
```json
{
  "github_repository": "auto-res2/onda",
  "branch_name": "test-1",
  "base_queries": ["diffusion model"],
  "save_dir": "20250101_120000",
  "file_path": null,
  "llm_name": "gemini-2.0-flash-001",
  "scrape_urls": [
    "https://icml.cc/virtual/2024/papers.html?filter=title"
  ]
}
```

**レスポンス例:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "pending",
  "message": "Job created successfully"
}
```

### 2. ジョブ状態取得

**GET** `/jobs/{job_id}`

ジョブの現在の状態を取得します。

**レスポンス例:**
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "created_at": "2025-01-01T12:00:00",
  "started_at": "2025-01-01T12:00:05",
  "completed_at": null,
  "current_step": "retriever",
  "progress": 0.1,
  "result": null,
  "error": null
}
```

### 3. ジョブ一覧取得

**GET** `/jobs/`

ジョブ一覧を取得します。

**クエリパラメータ:**
- `limit`: 取得するジョブ数（デフォルト: 100）

### 4. ジョブ削除

**DELETE** `/jobs/{job_id}`

ジョブを削除します。

### 5. ジョブキャンセル

**POST** `/jobs/{job_id}/cancel`

実行中のジョブをキャンセルします。

### 6. ジョブ結果取得

**GET** `/jobs/{job_id}/result`

完了したジョブの結果を取得します。

### 7. 統計情報取得

**GET** `/statistics`

ジョブの統計情報を取得します。

### 8. 古いジョブ削除

**POST** `/cleanup`

古いジョブを削除します。

**クエリパラメータ:**
- `days`: 削除する日数（デフォルト: 30）

## ジョブの状態

- `pending`: 待機中
- `running`: 実行中
- `completed`: 完了
- `failed`: 失敗
- `cancelled`: キャンセル

## 実行ステップ

E2E処理は以下の順序で実行されます：

1. `prepare` - リポジトリの準備
2. `retriever` - 論文の検索
3. `retriever2` - 関連論文の検索
4. `retriever3` - コードの取得
5. `creator` - 手法の作成
6. `creator2` - 実験設計の作成
7. `coder` - コードの作成
8. `executor` - GitHub Actionsでの実行
9. `fixer` - コードの修正（必要に応じて）
10. `analysis` - 結果の分析
11. `writer` - 論文の執筆
12. `citation` - 引用の追加
13. `latex` - LaTeX形式での出力
14. `readme` - READMEの作成
15. `html` - HTML形式での出力

## エラーハンドリング

APIは以下のエラーを返します：

- `400 Bad Request`: リクエストが不正
- `404 Not Found`: ジョブが見つからない
- `500 Internal Server Error`: サーバー内部エラー

## 使用例

### cURLでの使用例

```bash
# ジョブ作成
curl -X POST "http://localhost:8000/jobs/" \
  -H "Content-Type: application/json" \
  -d '{
    "github_repository": "auto-res2/onda",
    "branch_name": "test-1",
    "base_queries": ["diffusion model"]
  }'

# ジョブ状態確認
curl "http://localhost:8000/jobs/{job_id}"

# ジョブ一覧取得
curl "http://localhost:8000/jobs/"

# ジョブキャンセル
curl -X POST "http://localhost:8000/jobs/{job_id}/cancel"
```

### Pythonでの使用例

```python
import requests

# ジョブ作成
response = requests.post("http://localhost:8000/jobs/", json={
    "github_repository": "auto-res2/onda",
    "branch_name": "test-1",
    "base_queries": ["diffusion model"]
})
job_id = response.json()["job_id"]

# 状態確認
while True:
    status_response = requests.get(f"http://localhost:8000/jobs/{job_id}")
    status = status_response.json()
    
    if status["status"] in ["completed", "failed", "cancelled"]:
        break
    
    time.sleep(5)

# 結果取得
if status["status"] == "completed":
    result_response = requests.get(f"http://localhost:8000/jobs/{job_id}/result")
    result = result_response.json()
    print(result)
```

## 注意事項

1. **長時間実行**: E2E処理は長時間実行される可能性があります
2. **リソース使用**: 大量のリソースを使用する可能性があります
3. **エラー処理**: 各ステップでエラーが発生する可能性があります
4. **状態管理**: 処理の状態はファイルに保存されます

## 開発

### 依存関係

- FastAPI
- uvicorn
- pydantic

### ディレクトリ構造

```
src/airas/services/web_api/
├── app.py              # メインアプリケーション
├── models/
│   └── job.py         # データモデル
├── routes/
│   └── jobs.py        # ジョブ関連のルート
├── services/
│   ├── job_manager.py # ジョブ管理サービス
│   └── e2e_executor.py # E2E実行サービス
└── README.md          # このファイル
``` 