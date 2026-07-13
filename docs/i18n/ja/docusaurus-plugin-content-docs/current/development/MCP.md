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

| ツール | 説明 |
| --- | --- |
| `generate_research_queries` | 研究トピックから論文検索クエリを生成 |
| `search_paper_titles` | AIRAS論文データベース（主要ML国際会議）のBM25検索。APIキー不要 |
| `retrieve_papers` | arXiv経由で論文を取得し、構造化された研究データを抽出 |
| `generate_hypothesis` | トピックと関連研究から新規の研究仮説を生成 |

典型的なフロー: `generate_research_queries` → `search_paper_titles` → `retrieve_papers` → `generate_hypothesis`

## 開発

チェックアウトからサーバーを起動する場合：

```bash
cd backend
uv sync --extra mcp
uv run airas-mcp
```

サーバーはstdioトランスポートを使用し、MCPクライアントがオンデマンドで起動します。データベースやWebサーバーは不要です。
