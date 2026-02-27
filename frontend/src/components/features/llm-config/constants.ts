const DEFAULT_MODEL = "gpt-5.2";
const REASONING_MODEL = "gpt-5.2-codex";
const GITHUB_ACTIONS_MODEL = "anthropic/claude-sonnet-4-5";

// TODO: Using an API to retrieve the list of LLMs seems easier to maintain.

export const OPENAI_MODELS = [
  "gpt-5-nano-2025-08-07",
  "gpt-5-mini-2025-08-07",
  "gpt-5-2025-08-07",
  "gpt-5-pro-2025-10-06",
  "gpt-5.1-2025-11-13",
  "gpt-5.2-codex",
  "gpt-5.2",
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
  search_paper_titles_from_qdrant: DEFAULT_MODEL,
  search_arxiv_id_from_title: DEFAULT_MODEL,
  summarize_paper: DEFAULT_MODEL,
  extract_github_url_from_text: DEFAULT_MODEL,
  select_experimental_files: DEFAULT_MODEL,
  extract_reference_titles: DEFAULT_MODEL,
  generate_hypothesis: DEFAULT_MODEL,
  evaluate_novelty_and_significance: DEFAULT_MODEL,
  refine_hypothesis: DEFAULT_MODEL,
  generate_experimental_design: DEFAULT_MODEL,
  dispatch_code_generation: REASONING_MODEL,
  dispatch_experiment_validation: GITHUB_ACTIONS_MODEL,
  analyze_experiment: DEFAULT_MODEL,
  write_paper: DEFAULT_MODEL,
  refine_paper: DEFAULT_MODEL,
  convert_to_latex: DEFAULT_MODEL,
  compile_latex: GITHUB_ACTIONS_MODEL,
} as const;

export const SUBGRAPH_NODE_CONFIGS = {
  generate_queries: [{ key: "generate_queries", label: "クエリ生成" }],
  search_paper_titles_from_qdrant: [
    { key: "search_paper_titles_from_qdrant", label: "Qdrant論文検索" },
  ],
  retrieve_paper: [
    { key: "search_arxiv_id_from_title", label: "ArXiv ID検索" },
    { key: "summarize_paper", label: "論文要約" },
    { key: "extract_github_url_from_text", label: "GitHub URL抽出" },
    { key: "select_experimental_files", label: "実験ファイル選択" },
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
  dispatch_code_generation: [{ key: "dispatch_code_generation", label: "コード生成ディスパッチ" }],
  dispatch_experiment_validation: [
    { key: "dispatch_experiment_validation", label: "実験バリデーション" },
  ],
  analyze_experiment: [{ key: "analyze_experiment", label: "実験分析" }],
  write: [
    { key: "write_paper", label: "論文執筆" },
    { key: "refine_paper", label: "論文精緻化" },
  ],
  generate_latex: [{ key: "convert_to_latex", label: "LaTeX変換" }],
  compile_latex: [{ key: "compile_latex", label: "LaTeXコンパイル" }],
} as const;

/**
 * Mapping from display subgraph key to actual nested path in TopicOpenEndedResearchLLMMapping.
 * After #706, `dispatch_code_generation` is nested under `code_generation`,
 * and `generate_latex`/`compile_latex` are nested under `latex`.
 */
export const NESTED_SUBGRAPH_PATHS: Record<string, { topKey: string; nestedKey: string }> = {
  dispatch_code_generation: { topKey: "code_generation", nestedKey: "dispatch_code_generation" },
  generate_latex: { topKey: "latex", nestedKey: "generate_latex" },
  compile_latex: { topKey: "latex", nestedKey: "compile_latex" },
};

export const SUBGRAPH_DISPLAY_CONFIG = [
  { key: "generate_queries", title: "1. クエリ生成" },
  { key: "search_paper_titles_from_qdrant", title: "2. Qdrant論文検索" },
  { key: "retrieve_paper", title: "3. 論文取得" },
  { key: "generate_hypothesis", title: "4. 仮説生成" },
  { key: "generate_experimental_design", title: "5. 実験デザイン生成" },
  { key: "dispatch_code_generation", title: "6. コード生成" },
  { key: "dispatch_experiment_validation", title: "7. 実験バリデーション" },
  { key: "analyze_experiment", title: "8. 実験分析" },
  { key: "write", title: "9. 論文執筆" },
  { key: "generate_latex", title: "10. LaTeX生成" },
  { key: "compile_latex", title: "11. LaTeXコンパイル" },
] as const;

export const HYPOTHESIS_SUBGRAPH_NODE_CONFIGS = {
  generate_experimental_design: [
    { key: "generate_experimental_design", label: "実験デザイン生成" },
  ],
  code_generation: [{ key: "dispatch_code_generation", label: "コード生成ディスパッチ" }],
  dispatch_experiment_validation: [
    { key: "dispatch_experiment_validation", label: "実験バリデーション" },
  ],
  analyze_experiment: [{ key: "analyze_experiment", label: "実験分析" }],
  write: [
    { key: "write_paper", label: "論文執筆" },
    { key: "refine_paper", label: "論文精緻化" },
  ],
  latex: [
    { key: "convert_to_latex", label: "LaTeX変換" },
    { key: "compile_latex", label: "LaTeXコンパイル" },
  ],
} as const;

export const HYPOTHESIS_SUBGRAPH_DISPLAY_CONFIG = [
  { key: "generate_experimental_design", title: "1. 実験デザイン生成" },
  { key: "code_generation", title: "2. コード生成" },
  { key: "dispatch_experiment_validation", title: "3. 実験バリデーション" },
  { key: "analyze_experiment", title: "4. 実験分析" },
  { key: "write", title: "5. 論文執筆" },
  { key: "latex", title: "6. LaTeX生成" },
] as const;
