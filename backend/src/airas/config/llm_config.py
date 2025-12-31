from airas.services.api_client.llm_specs import LLM_MODELS, OPENAI_MODELS

LLM_CONFIG_TYPE = dict[str, LLM_MODELS | OPENAI_MODELS]

BASE_MODEL: LLM_MODELS = "global.anthropic.claude-haiku-4-5-20251001-v1:0"


# fmt:off
DEFAULT_NODE_LLMS: LLM_CONFIG_TYPE = {
    # --- features/retrievers ---
    # GenerateQueriesSubgraph
    "generate_queries": BASE_MODEL,
    # RetrievePaperSubgraph
    "search_arxiv_id_from_title": "gpt-5-mini-2025-08-07",
    "summarize_paper": "gemini-2.5-flash-lite",
    "extract_github_url_from_text": "gemini-2.5-flash-lite",
    "extract_experimental_info": "gemini-2.5-flash-lite",
    "extract_reference_titles": "gemini-2.5-flash-lite",

    # --- features/generators ---
    # GenerateHypothesisV0Subgraph
    "generate_hypothesis": BASE_MODEL,
    "evaluate_novelty_and_significance": BASE_MODEL,
    "refine_hypothesis": BASE_MODEL,
    # GenerateExperimentalDesignSubgraph
    "generate_experimental_design": BASE_MODEL,
    # GenerateCodeSubgraph
    "generate_run_config": BASE_MODEL,
    "generate_experiment_code": BASE_MODEL,
    "validate_experiment_code": BASE_MODEL,

    # --- features/analyzers ---
    # AnalyzeExperimentSubgraph
    "analyze_experiment": BASE_MODEL,

    # --- features/write ---
    # WriterSubgraph
    "write_paper": BASE_MODEL,
    "refine_paper": BASE_MODEL,

    # --- features/publication ---
    # GenerateLatexSubgraph
    "convert_to_latex": BASE_MODEL,

    # --- others ---
    # RetrieveHuggingFaceSubgraph
    "select_resources": BASE_MODEL,
    "extract_code_in_readme": BASE_MODEL,
    # CreateMethodSubgraph
    "improve_method": BASE_MODEL,
    # GenerateHtmlSubgraph
    "convert_to_html": BASE_MODEL,
}
# fmt: on
