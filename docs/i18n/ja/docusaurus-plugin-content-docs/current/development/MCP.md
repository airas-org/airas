---
title: MCP
slug: /development/MCP
---

# MCPサーバー

AIRASは、Claude CodeやClaude DesktopなどのMCPクライアントから研究サブグラフをツールとして利用できる、ローカルMCP（Model Context Protocol）サーバーを提供しています。

## セットアップ

インストール作業は不要です。初回実行時に `uvx` がパッケージを取得します。前提条件は [uv](https://docs.astral.sh/uv/) がインストールされていることだけです。

### Claude Code

```bash
claude mcp add airas \
  --env OPENAI_API_KEY=sk-... \
  --env GH_PERSONAL_ACCESS_TOKEN=ghp_... \
  -- uvx --from "airas[mcp]" airas-mcp
```

またはプロジェクトの `.mcp.json` に追加します：

```json
{
  "mcpServers": {
    "airas": {
      "command": "uvx",
      "args": ["--from", "airas[mcp]", "airas-mcp"],
      "env": {
        "OPENAI_API_KEY": "sk-...",
        "GH_PERSONAL_ACCESS_TOKEN": "ghp_..."
      }
    }
  }
}
```

### 環境変数

| 変数 | 必須 | 用途 |
| --- | --- | --- |
| `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `GEMINI_API_KEY` | いずれか1つ | LLM呼び出し（クエリ生成・論文抽出・仮説生成） |
| `GH_PERSONAL_ACCESS_TOKEN` | `retrieve_papers` 使用時 | GitHub APIアクセス |

## ツール

### 論文探索・仮説生成

| ツール | 説明 |
| --- | --- |
| `generate_research_queries` | 研究トピックから論文検索クエリを生成 |
| `search_paper_titles` | AIRAS論文データベース（主要ML国際会議）のBM25検索。APIキー不要 |
| `retrieve_papers` | arXiv経由で論文を取得し、構造化された研究データを抽出 |
| `generate_hypothesis` | トピックと関連研究から新規の研究仮説を生成 |
| `generate_experimental_design` | 仮説を検証する実験を設計 |

### 実験実行（GitHub Actions）

| ツール | 説明 |
| --- | --- |
| `prepare_repository` | 実験用リポジトリの作成・初期化 |
| `set_github_actions_secrets` | ローカル環境変数のLLM APIキーをリポジトリのActionsシークレットに設定 |
| `dispatch_code_generation` | 実験コード生成をGitHub Actionsで開始（非同期） |
| `dispatch_experiment` | サニティチェック／本実験の実行を開始（非同期） |
| `get_workflow_runs` | 直近のワークフロー実行のステータス確認（ノンブロッキング） |
| `fetch_experiment_code` | 生成された実験コードを取得 |
| `fetch_experiment_results` | 実験結果を取得 |
| `download_workflow_artifacts` | 特定のワークフロー実行のアーティファクトを取得 |
| `analyze_experiment` | 仮説・実験設計に照らして結果を解析 |

### 研究履歴の永続化

| ツール | 説明 |
| --- | --- |
| `upload_research_history` | 研究状態を実験リポジトリに保存 |
| `download_research_history` | 保存した研究状態を復元し、別セッションで継続 |

典型的なフロー: `generate_research_queries` → `search_paper_titles` → `retrieve_papers` → `generate_hypothesis` → `generate_experimental_design` → `prepare_repository` → `set_github_actions_secrets` → `dispatch_code_generation` →（`get_workflow_runs` でポーリング）→ `fetch_experiment_code` → `dispatch_experiment` →（ポーリング）→ `fetch_experiment_results` → `analyze_experiment` → `upload_research_history`

時間のかかるステップ（コード生成・実験）はGitHub Actions上で実行され、ツール自体は即座に返ります。完了待ちはせず `get_workflow_runs` で追跡してください。

## 開発

チェックアウトからサーバーを起動する場合：

```bash
cd backend
uv sync --extra mcp
uv run airas-mcp
```

サーバーはstdioトランスポートを使用し、MCPクライアントがオンデマンドで起動します。データベースやWebサーバーは不要です。
