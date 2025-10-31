from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL

LLM_CONFIG_TYPE = dict[str, LLM_MODEL]

BASE_MODEL: LLM_MODEL = "o3-2025-04-16"


# fmt:off
DEFAULT_NODE_LLMS: LLM_CONFIG_TYPE = {
    # --- features/retrieve ---
    # GenerateQueriesSubgraph
    "generate_queries": BASE_MODEL,
    # GetPaperTitlesFromWebSubgraph
    "openai_websearch_titles": BASE_MODEL,
    # ExtractReferenceTitlesSubgraph
    "extract_reference_titles": BASE_MODEL,
    # RetrieveCodeSubgraph
    "extract_github_url_from_text": BASE_MODEL,
    "extract_experimental_info": BASE_MODEL,
    # SummarizePaperSubgraph
    "summarize_paper": BASE_MODEL,

    # --- features/create ---
    # CreateCodeSubgraph
    "generate_run_config": BASE_MODEL,
    "generate_experiment_code": BASE_MODEL,
    "validate_experiment_code": BASE_MODEL,
    # CreateExperimentalDesignSubgraph
    "generate_experiment_design": BASE_MODEL,
    # CreateMethodSubgraph
    "idea_generator": BASE_MODEL,
    "refine_idea": BASE_MODEL,
    "research_value_judgement": BASE_MODEL,
    # CreateMethodSubgraphV2
    "generate_idea_and_research_summary": BASE_MODEL,
    "evaluate_novelty_and_significance": BASE_MODEL,
    "refine_idea_and_research_summary": BASE_MODEL,
    "search_arxiv_id_from_title": BASE_MODEL,
    # FixCodeSubgraph
    "fix_code": BASE_MODEL,

    # --- features/analysis ---
    # GitHubActionsExecutorSubgraph
    "extract_required_info": BASE_MODEL,

    # --- features/analysis ---
    # AnalyticSubgraph
    "analytic_node": BASE_MODEL,
    "evaluate_methods": BASE_MODEL,

    # --- features/write ---
    # CreateBibfileSubgraph
    "filter_references": BASE_MODEL,
    # WriterSubgraph
    "write_paper": BASE_MODEL,
    "refine_paper": BASE_MODEL,

    # --- features/retrieve ---
    # RetrieveHuggingFaceSubgraph
    "select_resources": BASE_MODEL,
    "extract_code_in_readme": BASE_MODEL,

    # --- features/evaluate ---
    # JudgeExecutionSubgraph
    "judge_execution": BASE_MODEL,
    # EvaluateExperimentalConsistencySubgraph
    "evaluate_experimental_consistency": BASE_MODEL,
    # EvaluatePaperResultsSubgraph
    "evaluate_paper_results": BASE_MODEL,
    # ReviewPaperSubgraph
    "review_paper": BASE_MODEL,

    # --- features/publication ---
    # HtmlSubgraph
    "convert_to_html": BASE_MODEL,
    # LatexSubgraph
    "convert_to_latex": BASE_MODEL,
}
# fmt: on
