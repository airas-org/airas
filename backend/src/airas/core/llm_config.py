from pydantic import BaseModel

from airas.infra.llm_specs import (
    LLMParams,
)


class NodeLLMConfig(BaseModel):
    # Use str instead of LLM_MODEL_S to allow model names compatible with
    # litellm and opencode rather than our custom defined literals.
    llm_name: str
    params: LLMParams | None = None


BASE_MODEL_CONFIG = NodeLLMConfig(llm_name="gpt-5.2")
ADVANCE_MODEL_CONFIG = NodeLLMConfig(llm_name="gpt-5.4-2026-03-05")
BUDGET_MODEL_CONFIG = NodeLLMConfig(llm_name="gemini-2.5-flash")
EMBEDDING_MODEL_CONFIG = NodeLLMConfig(llm_name="gemini/gemini-embedding-001")
AGENT_MODEL_CONFIG = NodeLLMConfig(llm_name="anthropic/claude-sonnet-4-5")

DEFAULT_NODE_LLM_CONFIG: dict[str, NodeLLMConfig] = {
    # retrieve/
    # GenerateQueriesSubgraph
    "generate_queries": BASE_MODEL_CONFIG,
    # SearchPaperTitlesFromQdrantSubgraph
    "search_paper_titles_from_qdrant": EMBEDDING_MODEL_CONFIG,
    # RetrievePaperSubgraph
    "search_arxiv_id_from_title": BUDGET_MODEL_CONFIG,
    "summarize_paper": BASE_MODEL_CONFIG,
    "extract_github_url_from_text": BUDGET_MODEL_CONFIG,
    "select_experimental_files": BASE_MODEL_CONFIG,
    "extract_reference_titles": BUDGET_MODEL_CONFIG,
    # generators/
    # GenerateHypothesisV0Subgraph
    "generate_hypothesis": ADVANCE_MODEL_CONFIG,
    "evaluate_novelty_and_significance": BASE_MODEL_CONFIG,
    "refine_hypothesis": ADVANCE_MODEL_CONFIG,
    # GenerateExperimentalDesignSubgraph
    "generate_experimental_design": ADVANCE_MODEL_CONFIG,
    # RefineExperimentalDesignSubgraph
    "refine_experimental_design": ADVANCE_MODEL_CONFIG,
    # DispatchCodeGenerationSubgraph
    "dispatch_code_generation": AGENT_MODEL_CONFIG,
    # executors/
    # DispatchExperimentValidationSubgraph
    "dispatch_experiment_validation": AGENT_MODEL_CONFIG,
    # analyzers/
    "analyze_experiment": ADVANCE_MODEL_CONFIG,
    # DecideExperimentCycleSubgraph
    "decide_experiment_cycle": ADVANCE_MODEL_CONFIG,
    # writes/
    # WriterSubgraph
    "write_paper": ADVANCE_MODEL_CONFIG,
    "refine_paper": ADVANCE_MODEL_CONFIG,
    # publication/
    # GenerateLatexSubgraph
    "convert_to_latex": BASE_MODEL_CONFIG,
    # CompileLatexSubgraph
    "compile_latex": AGENT_MODEL_CONFIG,
    # GenerateHtmlSubgraph
    "convert_to_html": BASE_MODEL_CONFIG,
    # DispatchDiagramGenerationSubgraph
    "dispatch_diagram_generation": AGENT_MODEL_CONFIG,
    # assisted_research/
    # DispatchInteractiveRepoAgentSubgraph
    "dispatch_interactive_repo_agent": AGENT_MODEL_CONFIG,
    # verification/
    # ProposeVerificationPolicySubgraph
    "propose_verification_policy": ADVANCE_MODEL_CONFIG,
    # GenerateVerificationMethodSubgraph
    "generate_verification_method": ADVANCE_MODEL_CONFIG,
    # GenerateExperimentCodeSubgraph
    "dispatch_experiment_code_generation": AGENT_MODEL_CONFIG,
}
