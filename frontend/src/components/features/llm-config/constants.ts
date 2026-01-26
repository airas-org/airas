const DEFAULT_MODEL = "gpt-5-nano-2025-08-07";
const REASONING_MODEL = "o3-2025-04-16";
const GITHUB_ACTIONS_MODEL = "anthropic/claude-sonnet-4-5";

// TODO: Using an API to retrieve the list of LLMs seems easier to maintain.

export const OPENAI_MODELS = [
  "gpt-5-nano-2025-08-07",
  "gpt-5-mini-2025-08-07",
  "gpt-5-2025-08-07",
  "gpt-5-pro-2025-10-06",
  "gpt-5.1-2025-11-13",
  "gpt-5.2-2025-12-11",
  "gpt-5.2-pro-2025-12-11",
  "gpt-4o-2024-11-20",
  "gpt-4o-mini-2024-07-18",
  "o3-2025-04-16",
  "o3-mini-2025-01-31",
  "o1-2024-12-17",
  "o1-pro-2025-03-19",
] as const;

export const GOOGLE_MODELS = [
  "gemini-3-pro-preview",
  "gemini-2.5-pro",
  "gemini-2.5-flash",
  "gemini-2.5-flash-lite",
  "gemini-2.0-flash",
  "gemini-2.0-flash-lite",
] as const;

export const ANTHROPIC_MODELS = [
  "claude-opus-4-5",
  "claude-sonnet-4-5",
  "claude-haiku-4-5",
  "claude-opus-4-1",
  "claude-opus-4",
  "claude-sonnet-4",
  "claude-3-7-sonnet",
  "claude-3-5-haiku",
] as const;

export const OPENROUTER_MODELS = [
  "anthropic/claude-opus-4.5",
  "anthropic/claude-sonnet-4.5",
  "anthropic/claude-haiku-4.5",
] as const;

export const BEDROCK_MODELS = [
  "jp.anthropic.claude-sonnet-4-5-20250929-v1:0",
  "global.anthropic.claude-opus-4-5-20251101-v1:0",
  "global.anthropic.claude-sonnet-4-5-20250929-v1:0",
] as const;

export const DEFAULT_NODE_LLM_CONFIG = {
  generate_queries: DEFAULT_MODEL,
  search_arxiv_id_from_title: DEFAULT_MODEL,
  summarize_paper: DEFAULT_MODEL,
  extract_github_url_from_text: DEFAULT_MODEL,
  extract_experimental_info: DEFAULT_MODEL,
  extract_reference_titles: DEFAULT_MODEL,
  generate_hypothesis: DEFAULT_MODEL,
  evaluate_novelty_and_significance: DEFAULT_MODEL,
  refine_hypothesis: DEFAULT_MODEL,
  generate_experimental_design: DEFAULT_MODEL,
  analyze_experiment: DEFAULT_MODEL,
  write_paper: DEFAULT_MODEL,
  refine_paper: DEFAULT_MODEL,
  convert_to_latex: DEFAULT_MODEL,

  generate_run_config: REASONING_MODEL,
  generate_experiment_code: REASONING_MODEL,
  validate_experiment_code: REASONING_MODEL,

  compile_latex: GITHUB_ACTIONS_MODEL,
  dispatch_trial_experiment: GITHUB_ACTIONS_MODEL,
  dispatch_full_experiments: GITHUB_ACTIONS_MODEL,
  dispatch_evaluation: GITHUB_ACTIONS_MODEL,
} as const;

export const SUBGRAPH_NODE_CONFIGS = {
  generate_queries: [{ key: "generate_queries", label: "クエリ生成" }],
  retrieve_paper: [
    { key: "search_arxiv_id_from_title", label: "ArXiv ID検索" },
    { key: "summarize_paper", label: "論文要約" },
    { key: "extract_github_url_from_text", label: "GitHub URL抽出" },
    { key: "extract_experimental_info", label: "実験情報抽出" },
    { key: "extract_reference_titles", label: "参考文献抽出" },
  ],
  generate_hypothesis: [
    { key: "generate_hypothesis", label: "仮説生成" },
    { key: "evaluate_novelty_and_significance", label: "新規性・重要性評価" },
    { key: "refine_hypothesis", label: "仮説精緻化" },
  ],
  generate_experimental_design: [
    { key: "generate_experimental_design", label: "実験デザイン生成" },
  ],
  generate_code: [
    { key: "generate_run_config", label: "実行設定生成" },
    { key: "generate_experiment_code", label: "実験コード生成" },
    { key: "validate_experiment_code", label: "コード検証" },
  ],
  analyze_experiment: [{ key: "analyze_experiment", label: "実験分析" }],
  write: [
    { key: "write_paper", label: "論文執筆" },
    { key: "refine_paper", label: "論文精緻化" },
  ],
  generate_latex: [{ key: "convert_to_latex", label: "LaTeX変換" }],
  compile_latex: [{ key: "compile_latex", label: "LaTeXコンパイル" }],
  execute_trial_experiment: [{ key: "dispatch_trial_experiment", label: "試行実験実行" }],
  execute_full_experiment: [{ key: "dispatch_full_experiments", label: "本実験実行" }],
  execute_evaluation: [{ key: "dispatch_evaluation", label: "評価実行" }],
} as const;

export const SUBGRAPH_DISPLAY_CONFIG = [
  { key: "generate_queries", title: "1. クエリ生成" },
  { key: "retrieve_paper", title: "2. 論文取得" },
  { key: "generate_hypothesis", title: "3. 仮説生成" },
  { key: "generate_experimental_design", title: "4. 実験デザイン生成" },
  { key: "generate_code", title: "5. コード生成" },
  { key: "execute_trial_experiment", title: "6. 試行実験実行" },
  { key: "execute_full_experiment", title: "7. 本実験実行" },
  { key: "execute_evaluation", title: "8. 評価実行" },
  { key: "analyze_experiment", title: "9. 実験分析" },
  { key: "write", title: "10. 論文執筆" },
  { key: "generate_latex", title: "11. LaTeX生成" },
  { key: "compile_latex", title: "12. LaTeXコンパイル" },
] as const;
