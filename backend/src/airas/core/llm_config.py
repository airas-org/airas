from pydantic import BaseModel

from airas.infra.llm_specs import (
    LLMParams,
)


class NodeLLMConfig(BaseModel):
    # Use str instead of LLM_MODELS to allow model names compatible with
    # litellm and opencode rather than our custom defined literals.
    llm_name: str
    params: LLMParams | None = None


BASE_CONFIG = NodeLLMConfig(llm_name="gpt-5.2")
SEARCH_CONFIG = NodeLLMConfig(llm_name="gemini-2.5-flash")
CODING_CONFIG = NodeLLMConfig(llm_name="gpt-5.2-codex")
EMBEDDING_CONFIG = NodeLLMConfig(llm_name="gemini/gemini-embedding-001")

DEFAULT_NODE_LLM_CONFIG: dict[str, NodeLLMConfig] = {
    # retrieve/
    # GenerateQueriesSubgraph
    "generate_queries": BASE_CONFIG,
    # SearchPaperTitlesFromQdrantSubgraph
    "search_paper_titles_from_qdrant": EMBEDDING_CONFIG,
    # RetrievePaperSubgraph
    "search_arxiv_id_from_title": SEARCH_CONFIG,
    "summarize_paper": BASE_CONFIG,
    "extract_github_url_from_text": BASE_CONFIG,
    "select_experimental_files": BASE_CONFIG,
    "extract_reference_titles": BASE_CONFIG,
    # generators/
    # GenerateHypothesisV0Subgraph
    "generate_hypothesis": BASE_CONFIG,
    "evaluate_novelty_and_significance": BASE_CONFIG,
    "refine_hypothesis": BASE_CONFIG,
    # GenerateExperimentalDesignSubgraph
    "generate_experimental_design": BASE_CONFIG,
    # GenerateCodeSubgraph
    "generate_run_config": CODING_CONFIG,
    "generate_experiment_code": CODING_CONFIG,
    "validate_experiment_code": CODING_CONFIG,
    # generators/
    # DispatchCodeGenerationSubgraph
    "dispatch_code_generation": NodeLLMConfig(llm_name="anthropic/claude-sonnet-4-5"),
    # executors/
    # DispatchExperimentValidationSubgraph
    "dispatch_experiment_validation": NodeLLMConfig(
        llm_name="anthropic/claude-sonnet-4-5"
    ),
    # executors/
    # ExecuteTrialExperimentSubgraph
    # NOTE: GitHub Actions nodes use "provider/model" format for LiteLLM compatibility.
    # All nodes will migrate to this format when fully transitioning to LiteLLM.
    "dispatch_trial_experiment": NodeLLMConfig(llm_name="claude-sonnet-4-5"),
    # ExecuteFullExperimentSubgraph
    "dispatch_full_experiments": NodeLLMConfig(llm_name="claude-sonnet-4-5"),
    # ExecuteEvaluationSubgraph
    "dispatch_evaluation": NodeLLMConfig(llm_name="claude-sonnet-4-5"),
    # analyzers/
    # AnalyzeExperimentSubgraph
    "analyze_experiment": BASE_CONFIG,
    # writes/
    # WriterSubgraph
    "write_paper": BASE_CONFIG,
    "refine_paper": BASE_CONFIG,
    # publication/
    # GenerateLatexSubgraph
    "convert_to_latex": BASE_CONFIG,
    # CompileLatexSubgraph
    "compile_latex": NodeLLMConfig(llm_name="anthropic/claude-sonnet-4-5"),
    # GenerateHtmlSubgraph
    "convert_to_html": BASE_CONFIG,
    # DispatchDiagramGenerationSubgraph
    "dispatch_diagram_generation": NodeLLMConfig(
        llm_name="anthropic/claude-sonnet-4-5"
    ),
}
