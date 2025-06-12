# OpenAI Web Search タイトル検索ノード

このドキュメントは、新しく追加されたOpenAI API web search機能を使ったタイトル検索ノードの使い方を説明します。

## 概要

従来の方法：
```
web_scrape_node → extract_paper_title_node → search_arxiv_node
```

OpenAI Web Search使用時：
```
openai_websearch_titles_node → search_arxiv_node
```

## 主な特徴

- **直接タイトル検索**: ウェブスクレイピングを経由せずに、OpenAI APIのweb search機能を使って直接論文タイトルを検索
- **除外キーワード**: survey、review、overview、systematic reviewなどを自動除外
- **レート制限対応**: クエリ間で60秒の待機時間を設定
- **最大結果数制限**: デフォルトで5件のタイトルを取得

## 使用方法

### 1. 従来の方法（デフォルト）

```python
from airas.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph import RetrievePaperFromQuerySubgraph

result = RetrievePaperFromQuerySubgraph(
    llm_name="o3-mini-2025-01-31",
    save_dir="/workspaces/airas/data",
    scrape_urls=[
        "https://icml.cc/virtual/2024/papers.html?filter=title",
        "https://iclr.cc/virtual/2024/papers.html?filter=title",
    ],
    # use_openai_websearch=False,  # デフォルトはFalse
).run(input)
```

### 2. OpenAI Web Search使用時

```python
from airas.retrieve.retrieve_paper_from_query_subgraph.retrieve_paper_from_query_subgraph import RetrievePaperFromQuerySubgraph

result = RetrievePaperFromQuerySubgraph(
    llm_name="o3-mini-2025-01-31",
    save_dir="/workspaces/airas/data",
    scrape_urls=[],  # OpenAI使用時は無視されるが互換性のため残す
    use_openai_websearch=True,  # これをTrueにするだけで切り替え可能
).run(input)
```

### 3. main.py での簡単切り替え

`main.py`の該当部分で、コメントアウトを外すだけで簡単に切り替えできます：

```python
def main():
    # 従来の方法（デフォルト）
    result = RetrievePaperFromQuerySubgraph(
        llm_name=llm_name,
        save_dir=save_dir,
        scrape_urls=scrape_urls,
    ).run(input)
    
    # OpenAI Web Search使用時（下記のコメントアウトを外すだけ）
    # result = RetrievePaperFromQuerySubgraph(
    #     llm_name=llm_name,
    #     save_dir=save_dir,
    #     scrape_urls=scrape_urls,
    #     use_openai_websearch=True,  # この行を有効にする
    # ).run(input)
```

## パラメータ

| パラメータ | デフォルト値 | 説明 |
|------------|-------------|------|
| `max_results` | 5 | 取得するタイトル数の上限 |
| `sleep_sec` | 60.0 | クエリ間の待機時間（秒） |
| `use_openai_websearch` | False | OpenAI web searchを使用するかどうか |

## 必要な環境変数

OpenAI API keyが必要です：
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

## 処理フロー

1. **クエリ実行**: 各クエリに対してOpenAI APIのweb search機能を使用
2. **タイトル抽出**: JSONレスポンスからtitlesを抽出
3. **フィルタリング**: 除外キーワードを含むタイトルを除去
4. **重複排除**: setを使用してユニークなタイトルのみを保持
5. **arXiv検索**: 取得したタイトルでarXivを検索

## エラーハンドリング

- API呼び出し失敗時は警告ログを出力してスキップ
- JSON解析エラー時も同様にスキップ
- 全クエリで結果が得られない場合はNoneを返す

## ログ出力例

```
INFO - Searching papers with OpenAI web search for query: 'vision transformer image recognition'
INFO - Waiting 60.0 seconds before next query...
WARNING - OpenAI web search failed for 'invalid query': API error message
```

## 注意事項

- OpenAI APIの利用料金が発生します
- web search機能は比較的新しい機能のため、利用可能性を事前に確認してください
- レート制限により、複数クエリの処理には時間がかかる場合があります
