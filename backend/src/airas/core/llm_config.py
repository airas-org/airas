from pydantic import BaseModel

from airas.infra.llm_specs import (
    LLM_MODELS,
    LLMParams,
    OpenAIParams,
)


class NodeLLMConfig(BaseModel):
    llm_name: LLM_MODELS
    params: LLMParams | None = None


BASE_CONFIG = NodeLLMConfig(llm_name="gpt-5-nano-2025-08-07")
SEARCH_CONFIG = NodeLLMConfig(llm_name="gpt-5-nano-2025-08-07")
CODING_CONFIG = NodeLLMConfig(
    llm_name="gpt-5-nano-2025-08-07", params=OpenAIParams(reasoning_effort="high")
)

DEFAULT_NODE_LLM_CONFIG: dict[str, NodeLLMConfig] = {
    # retrieve/
    # GenerateQueriesSubgraph
    "generate_queries": BASE_CONFIG,
    # RetrievePaperSubgraph
    "search_arxiv_id_from_title": SEARCH_CONFIG,
    "summarize_paper": BASE_CONFIG,
    "extract_github_url_from_text": BASE_CONFIG,
    "extract_experimental_info": BASE_CONFIG,
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
    # GenerateHtmlSubgraph
    "convert_to_html": BASE_CONFIG,
}
