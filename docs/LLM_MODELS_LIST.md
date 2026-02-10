# AIRASで使用されるLLMモデル一覧

このドキュメントは、AIRAS（研究自動化プラットフォーム）で実験に使用されるLLM（大規模言語モデル）の完全なリストを提供します。

## 概要

AIRASは複数のLLMプロバイダーをサポートしており、研究ワークフローの各ステップに最適なモデルを使用します。

**主要な設定ファイル:**
- **プロバイダーとモデルの定義**: `backend/src/airas/infra/llm_specs.py`
- **ノード別のLLM設定**: `backend/src/airas/core/llm_config.py`

## サポートされているLLMプロバイダー

1. **Google** (Gemini モデル)
2. **OpenAI** (GPT および O シリーズモデル)
3. **Anthropic** (Claude モデル)
4. **OpenRouter** (マルチプロバイダールーティング)
5. **AWS Bedrock** (AWSホスト型モデル)

---

## 1. Google Models (Gemini)

**利用可能なモデル:**

| モデル名 | 説明 |
|---------|------|
| `gemini-3-pro-preview` | Gemini 3 Pro プレビュー版 |
| `gemini-2.5-pro` | Gemini 2.5 Pro - 高性能モデル |
| `gemini-2.5-flash` | Gemini 2.5 Flash - 高速モデル |
| `gemini-2.5-flash-lite` | Gemini 2.5 Flash Lite - 軽量版 |
| `gemini-2.0-flash` | Gemini 2.0 Flash |
| `gemini-2.0-flash-lite` | Gemini 2.0 Flash Lite |
| `gemini-embedding-001` | Gemini 埋め込みモデル |

**特殊パラメータ:**
- `thinking_budget`: 推論予算の設定
  - `0`: オフ
  - `1024-32768`: 固定予算
  - `-1`: 動的予算

**必要な環境変数:**
- `GEMINI_API_KEY`

---

## 2. OpenAI Models (GPT と O シリーズ)

**GPT-5 シリーズ:**

| モデル名 | 説明 |
|---------|------|
| `gpt-5.2-pro-2025-12-11` | GPT-5.2 Pro 最新版 |
| `gpt-5.2-codex` | GPT-5.2 コード特化型 |
| `gpt-5.2` | GPT-5.2 標準版 |
| `gpt-5.1-2025-11-13` | GPT-5.1 |
| `gpt-5-pro-2025-10-06` | GPT-5 Pro |
| `gpt-5-codex` | GPT-5 コード特化型 |
| `gpt-5-2025-08-07` | GPT-5 標準版 |
| `gpt-5-mini-2025-08-07` | GPT-5 Mini - 軽量版 |
| `gpt-5-nano-2025-08-07` | GPT-5 Nano - 超軽量版 |

**GPT-4 シリーズ:**

| モデル名 | 説明 |
|---------|------|
| `gpt-4.1-2025-04-14` | GPT-4.1 |
| `gpt-4o-2024-11-20` | GPT-4 Omni |
| `gpt-4o-mini-2024-07-18` | GPT-4 Omni Mini |

**O シリーズ (推論モデル):**

| モデル名 | 説明 |
|---------|------|
| `o4-mini-2025-04-16` | O4 Mini 推論モデル |
| `o3-2025-04-16` | O3 推論モデル |
| `o3-mini-2025-01-31` | O3 Mini 推論モデル |
| `o1-pro-2025-03-19` | O1 Pro 推論モデル |
| `o1-2024-12-17` | O1 推論モデル |

**特殊パラメータ:**
- `reasoning_effort`: 推論モデルの推論強度
  - `none`: なし
  - `low`: 低
  - `medium`: 中
  - `high`: 高

**必要な環境変数:**
- `OPENAI_API_KEY`

---

## 3. Anthropic Models (Claude)

**利用可能なモデル:**

| モデル名 | 説明 |
|---------|------|
| `claude-opus-4-5` | Claude Opus 4.5 - 最高性能 |
| `claude-sonnet-4-5` | Claude Sonnet 4.5 - バランス型 |
| `claude-haiku-4-5` | Claude Haiku 4.5 - 高速版 |
| `claude-opus-4-1` | Claude Opus 4.1 |
| `claude-opus-4` | Claude Opus 4 |
| `claude-sonnet-4` | Claude Sonnet 4 |
| `claude-3-7-sonnet` | Claude 3.7 Sonnet |
| `claude-3-5-haiku` | Claude 3.5 Haiku |

**必要な環境変数:**
- `ANTHROPIC_API_KEY`

---

## 4. OpenRouter Models

OpenRouterは、複数のプロバイダーのモデルへの統一アクセスを提供します。

**利用可能なモデル:**
- すべてのGoogle Geminiモデル（プレフィックス: `google/`）
- すべてのOpenAI GPTモデル
- すべてのAnthropic Claudeモデル（プレフィックス: `anthropic/`）

**例:**
- `google/gemini-2.5-pro`
- `anthropic/claude-sonnet-4.5`

**必要な環境変数:**
- `OPENROUTER_API_KEY`

---

## 5. AWS Bedrock Models

AWS Bedrockを通じてホストされるモデル。

**利用可能なモデル:**

| モデル名 | 説明 |
|---------|------|
| `jp.anthropic.claude-sonnet-4-5-20250929-v1:0` | Claude Sonnet 4.5 (日本リージョン) |
| `global.anthropic.claude-opus-4-5-20251101-v1:0` | Claude Opus 4.5 (グローバル) |
| `global.anthropic.claude-sonnet-4-5-20250929-v1:0` | Claude Sonnet 4.5 (グローバル) |
| `global.anthropic.claude-sonnet-4-20250514-v1:0` | Claude Sonnet 4 (グローバル) |
| `global.anthropic.claude-haiku-4-5-20251001-v1:0` | Claude Haiku 4.5 (グローバル) |
| `openai.gpt-oss-120b-1:0` | GPT-OSS 120B (構造化出力非対応) |

**必要な環境変数:**
- `AWS_BEARER_TOKEN_BEDROCK`

---

## ワークフローノード別のデフォルトLLM設定

AIRASは研究ワークフローの各ステップに最適なモデルを自動選択します。

### 基本設定

| 設定名 | モデル | 用途 |
|--------|--------|------|
| `BASE_CONFIG` | `gpt-5.2` | 一般的なタスク |
| `SEARCH_CONFIG` | `gpt-5-nano-2025-08-07` | 検索・取得タスク |
| `CODING_CONFIG` | `gpt-5.2-codex` (reasoning_effort=high) | コード生成 |

### ノード別の詳細設定

**1. 検索・取得 (Retrieve)**
- `generate_queries`: `gpt-5.2`
- `search_arxiv_id_from_title`: `gpt-5-nano-2025-08-07`
- `summarize_paper`: `gpt-5.2`
- `extract_github_url_from_text`: `gpt-5.2`
- `select_experimental_files`: `gpt-5.2`
- `extract_reference_titles`: `gpt-5.2`

**2. 生成 (Generators)**
- `generate_hypothesis`: `gpt-5.2`
- `evaluate_novelty_and_significance`: `gpt-5.2`
- `refine_hypothesis`: `gpt-5.2`
- `generate_experimental_design`: `gpt-5.2`
- `generate_run_config`: `gpt-5.2-codex` (高推論強度)
- `generate_experiment_code`: `gpt-5.2-codex` (高推論強度)
- `validate_experiment_code`: `gpt-5.2-codex` (高推論強度)

**3. 実行 (Executors)**
- `dispatch_trial_experiment`: `anthropic/claude-sonnet-4-5`
- `dispatch_full_experiments`: `anthropic/claude-sonnet-4-5`
- `dispatch_evaluation`: `anthropic/claude-sonnet-4-5`

**4. 分析 (Analyzers)**
- `analyze_experiment`: `gpt-5.2`

**5. 執筆 (Writers)**
- `write_paper`: `gpt-5.2`
- `refine_paper`: `gpt-5.2`

**6. 出版 (Publication)**
- `convert_to_latex`: `gpt-5.2`
- `compile_latex`: `anthropic/claude-sonnet-4-5`
- `convert_to_html`: `gpt-5.2`

---

## モデルのコンテキストウィンドウ情報

AIRASはLiteLLMを使用してモデルのコンテキストウィンドウ情報を自動取得します。

**カスタムオーバーライド:**
- `gpt-5.2-codex`:
  - 最大入力トークン: 272,000
  - 最大出力トークン: 128,000

---

## 参考リンク

- [Google Gemini Models](https://ai.google.dev/gemini-api/docs/models)
- [OpenAI Models](https://platform.openai.com/docs/models)
- [Anthropic Claude Models](https://platform.claude.com/docs/en/about-claude/models/overview)
- [AWS Bedrock Inference Profiles](https://docs.aws.amazon.com/bedrock/latest/userguide/inference-profiles-support.html)
- [LiteLLM Model Prices and Context Window](https://github.com/BerriAI/litellm/blob/main/model_prices_and_context_window.json)

---

## 更新履歴

- 2026-02-10: 初版作成 - すべてのサポートされているLLMプロバイダーとモデルの一覧を追加
