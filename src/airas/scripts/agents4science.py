import logging

from tqdm import tqdm

from airas.config.workflow_config import DEFAULT_WORKFLOW_CONFIG
from airas.features import (
    AnalyticSubgraph,
    CreateBibfileSubgraph,
    CreateCodeSubgraph,
    CreateExperimentalDesignSubgraph,
    CreateMethodSubgraphV2,
    EvaluateExperimentalConsistencySubgraph,
    EvaluatePaperResultsSubgraph,
    ExtractReferenceTitlesSubgraph,
    FixCodeSubgraph,
    FixCodeWithDevinSubgraph,
    GenerateQueriesSubgraph,
    GetPaperTitlesFromDBSubgraph,
    GitHubActionsExecutorSubgraph,
    GithubUploadSubgraph,
    HtmlSubgraph,
    JudgeExecutionSubgraph,
    LatexSubgraph,
    PrepareRepositorySubgraph,
    ReadmeSubgraph,
    RetrieveCodeSubgraph,
    RetrieveExternalResourcesSubgraph,
    RetrievePaperContentSubgraph,
    ReviewPaperSubgraph,
    SummarizePaperSubgraph,
    WriterSubgraph,
)
from airas.types.github import GitHubRepositoryInfo
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

AVAILABLE_MODELS = [
    # gpt
    "o4-mini-2025-04-16",
    "o3-2025-04-16",
    "o3-mini-2025-01-31",
    "o1-pro-2025-03-19",
    "o1-2024-12-17",
    "gpt-5-2025-08-07",
    "gpt-5-mini-2025-08-07",
    "gpt-5-nano-2025-08-07",
    "gpt-4.1-2025-04-14",
    "gpt-4o-2024-11-20",
    "gpt-4o-mini-2024-07-18",
    # gemini
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite-preview-06-17",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite-001",
    "gemini-embedding-001",
    # claude
    # NOTE: Claude cannot be used for processing that requires structured output.
    "claude-opus-4-1-20250805",
    "claude-opus-4-20250514",
    "claude-sonnet-4-20250514",
    "claude-3-7-sonnet-20250219",
    "claude-3-5-haiku-20241022",
]

RUNNER_TYPE = ["ubuntu-latest", "gpu-runner", "A100_80GM×1", "A100_80GM×8"]


runner_type = "A100_80GM×1"

n_queries = 2  # 論文検索時のサブクエリの数
max_results_per_query = 3  # 論文検索時の各サブクエリに対する論文数
num_reference_paper = 5  # 論文作成時に追加で参照する論文数
method_refinement_rounds = 2  # 新規手法の改良回数
num_retrieve_related_papers = 3  # 新規手法作成時に新規性を確認するのに取得する論文数
max_huggingface_results_per_search = (
    10  # modelやdatasetごとのHuggingFaceからの候補の取得数
)
writing_refinement_rounds = 2  # 論文の改良回数
max_filtered_references = 5  # 論文中で引用する参考文献の最大数
max_chktex_revisions = 3  # LaTeXの文法チェックの修正回数
max_compile_revisions = 3  # LaTeXのコンパイルエラー修正


generate_queries = GenerateQueriesSubgraph(
    llm_mapping={
        "generate_queries": "o4-mini-2025-04-16",
    },
    n_queries=n_queries,
)
get_paper_titles = GetPaperTitlesFromDBSubgraph(
    max_results_per_query=max_results_per_query, semantic_search=True
)
retrieve_paper_content = RetrievePaperContentSubgraph(
    target_study_list_source="research_study_list",
    llm_mapping={
        "search_arxiv_id_from_title": "gpt-5-mini-2025-08-07",  # Only openAI models are available.
    },
    paper_provider="arxiv",
)
summarize_paper = SummarizePaperSubgraph(
    llm_mapping={"summarize_paper": "gemini-2.5-flash"}
)
retrieve_code = RetrieveCodeSubgraph(
    llm_mapping={
        "extract_github_url_from_text": "gemini-2.5-flash",
        "extract_experimental_info": "gemini-2.5-flash",
    }
)
reference_extractor = ExtractReferenceTitlesSubgraph(
    llm_mapping={"extract_reference_titles": "gemini-2.5-flash"},
    num_reference_paper=num_reference_paper,
)
retrieve_reference_paper_content = RetrievePaperContentSubgraph(
    target_study_list_source="reference_research_study_list",
    llm_mapping={
        "search_arxiv_id_from_title": "gpt-5-mini-2025-08-07",  # Only openAI models are available.
    },
    paper_provider="arxiv",
)

create_method = CreateMethodSubgraphV2(
    llm_mapping={
        "generate_ide_and_research_summary": "o3-2025-04-16",
        "evaluate_novelty_and_significance": "o3-2025-04-16",
        "refine_idea_and_research_summary": "o3-2025-04-16",
        "search_arxiv_id_from_title": "gpt-5-mini-2025-08-07",  # Only openAI models are available.
    },
    method_refinement_rounds=method_refinement_rounds,
    num_retrieve_related_papers=num_retrieve_related_papers,
)
create_experimental_design = CreateExperimentalDesignSubgraph(
    runner_type=runner_type,
    llm_mapping={
        "generate_experiment_strategy": "o3-2025-04-16",
        "generate_experiment_details": "o3-2025-04-16",
    },
)
retrieve_external_resources = RetrieveExternalResourcesSubgraph(
    llm_mapping={"select_external_resources": "gemini-2.5-flash"},
    max_huggingface_results_per_search=max_huggingface_results_per_search,
)
coder = CreateCodeSubgraph(
    runner_type=runner_type,
    llm_mapping={
        "generate_experiment_code": "o3-2025-04-16",
        "convert_code_to_scripts": "o3-2025-04-16",
    },
)
executor = GitHubActionsExecutorSubgraph(runner_type=runner_type)
judge_execution = JudgeExecutionSubgraph(
    llm_mapping={
        "judge_execution": "gpt-5-2025-08-07",
    }
)
fixer = FixCodeWithDevinSubgraph(runner_type=runner_type)
# fixer = FixCodeSubgraph(
#     runner_type=runner_type,
#     llm_mapping={
#         "fix_code": "o3-2025-04-16",
#     },
# )
evaluate_consistency = EvaluateExperimentalConsistencySubgraph(
    llm_mapping={
        "evaluate_experimental_consistency": "o3-2025-04-16",
    }
)
analysis = AnalyticSubgraph(
    llm_mapping={
        "analytic_node": "o3-2025-04-16",
    }
)
create_bibfile = CreateBibfileSubgraph(
    llm_mapping={
        "filter_references": "gemini-2.5-flash",
    },
    latex_template_name="agents4science_2025",
    max_filtered_references=max_filtered_references,
)
writer = WriterSubgraph(
    llm_mapping={
        "write_paper": "gpt-5-2025-08-07",
        "refine_paper": "o3-2025-04-16",
    },
    writing_refinement_rounds=writing_refinement_rounds,
)
evaluate_paper = EvaluatePaperResultsSubgraph(
    llm_mapping={
        "evaluate_paper_results": "gpt-5-2025-08-07",
    }
)
review = ReviewPaperSubgraph(
    llm_mapping={
        "review_paper": "o3-2025-04-16",
    }
)
latex = LatexSubgraph(
    llm_mapping={
        "convert_to_latex": "gpt-5-2025-08-07",
        "check_execution_successful": "gpt-5-2025-08-07",
        "fix_latex_text": "o3-2025-04-16",
    },
    latex_template_name="agents4science_2025",
    max_chktex_revisions=max_chktex_revisions,
    max_compile_revisions=max_compile_revisions,
)
readme = ReadmeSubgraph()
html = HtmlSubgraph(
    llm_mapping={
        "convert_to_html": "gpt-5-2025-08-07",
    }
)
uploader = GithubUploadSubgraph()


subgraph_list = [
    generate_queries,
    get_paper_titles,
    retrieve_paper_content,
    summarize_paper,
    retrieve_code,
    create_method,
    create_experimental_design,
    retrieve_external_resources,
    coder,
    executor,
    judge_execution,
    fixer,
    evaluate_consistency,
    analysis,
    reference_extractor,
    retrieve_reference_paper_content,
    create_bibfile,
    writer,
    evaluate_paper,
    review,
    latex,
    html,
    readme,
]


def _run_fix_loop(state, workflow_config):
    for _ in range(workflow_config.max_fix_attempts):
        state = executor.run(state)
        state = judge_execution.run(state)
        if state.get("is_experiment_successful"):
            _ = uploader.run(state)
            return state
        state = fixer.run(state)
    _ = uploader.run(state)
    print("Fix attempts exhausted, proceeding with current state")
    return state


def _run_experiment_consistent_loop(state, workflow_config):
    for _ in range(workflow_config.max_consistency_attempts):
        state = create_experimental_design.run(state)
        state = coder.run(state)
        state = _run_fix_loop(state, workflow_config)

        state = evaluate_consistency.run(state)
        if state.get("is_experiment_consistent"):
            _ = uploader.run(state)
            return state
        print("Experimental consistency failed → redesign.")
    _ = uploader.run(state)
    return state


def run_subgraphs(subgraph_list, state, workflow_config=DEFAULT_WORKFLOW_CONFIG):
    for subgraph in tqdm(subgraph_list, desc="Executing Research Workflow"):
        subgraph_name = subgraph.__class__.__name__
        print(f"--- Running Subgraph: {subgraph_name} ---")

        if isinstance(subgraph, CreateExperimentalDesignSubgraph):
            state = _run_experiment_consistent_loop(state, workflow_config)
            state = analysis.run(state)

        elif isinstance(
            subgraph,
            (
                CreateExperimentalDesignSubgraph,
                RetrieveExternalResourcesSubgraph,
                CreateCodeSubgraph,
                GitHubActionsExecutorSubgraph,
                JudgeExecutionSubgraph,
                FixCodeSubgraph,
                AnalyticSubgraph,
            ),
        ):
            continue

        else:
            state = subgraph.run(state)

        _ = uploader.run(state)
        print(f"--- Finished Subgraph: {subgraph_name} ---\n")


def execute_workflow(
    github_owner: str,
    repository_name: str,
    research_topic_list: list[str],
    subgraph_list: list = subgraph_list,
):
    for index, research_topic in enumerate(research_topic_list):
        print(f"index:{index}")
        state = {
            "github_repository_info": GitHubRepositoryInfo(
                github_owner=github_owner,
                repository_name=repository_name,
                branch_name=f"test-{index}",
            ),
            "research_topic": research_topic,
        }

        _ = PrepareRepositorySubgraph().run(state)
        try:
            _ = run_subgraphs(subgraph_list, state)
        except Exception:
            raise


if __name__ == "__main__":
    github_owner = "auto-res2"
    repository_name = "tanaka-20250912"
    research_topic_list = [
        # "Graph Attention Networkの学習の高速化",
        # "Transformerを用いた時系列データの新規手法",
        # "Diffusion Transformersの速度改善",
        "Diffusion Transformersの改善"
    ]
    execute_workflow(
        github_owner, repository_name, research_topic_list=research_topic_list
    )
