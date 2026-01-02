from pydantic import BaseModel

from airas.infra.llm_specs import (
    LLM_MODELS,
    OPENAI_MODELS,
    LLMParams,
    OpenAIParams,
)

LLM_CONFIG_TYPE = dict[str, LLM_MODELS | OPENAI_MODELS]

BASE_MODEL: LLM_MODELS = "gpt-5-nano-2025-08-07"


class NodeLLMConfig(BaseModel):
    llm_name: LLM_MODELS
    params: LLMParams | None = None


DEFAULT_NODE_LLM_CONFIG: dict[str, NodeLLMConfig] = {
    # GenerateCodeSubgraph
    "generate_run_config": NodeLLMConfig(
        llm_name="o3-2025-04-16",
        params=OpenAIParams(reasoning_effort="high"),
    ),
    "generate_experiment_code": NodeLLMConfig(
        llm_name="o3-2025-04-16",
        params=OpenAIParams(reasoning_effort="high"),
    ),
    "validate_experiment_code": NodeLLMConfig(
        llm_name="o3-2025-04-16",
        params=OpenAIParams(reasoning_effort="high"),
    ),
}


# fmt:off
DEFAULT_NODE_LLMS: LLM_CONFIG_TYPE = {
    # --- features/retrievers ---
    # GenerateQueriesSubgraph
    "generate_queries": BASE_MODEL,
    # RetrievePaperSubgraph
    "search_arxiv_id_from_title": BASE_MODEL,
    "summarize_paper":BASE_MODEL,
    "extract_github_url_from_text":BASE_MODEL,
    "extract_experimental_info":BASE_MODEL,
    "extract_reference_titles":BASE_MODEL,

    # --- features/generators ---
    # GenerateHypothesisV0Subgraph
    "generate_hypothesis": BASE_MODEL,
    "evaluate_novelty_and_significance": BASE_MODEL,
    "refine_hypothesis": BASE_MODEL,
    # GenerateExperimentalDesignSubgraph
    "generate_experimental_design": BASE_MODEL,

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
