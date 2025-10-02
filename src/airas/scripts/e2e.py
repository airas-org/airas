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
    ExtractReferenceTitlesSubgraph,
    GenerateQueriesSubgraph,
    GetPaperTitlesFromDBSubgraph,
    GitHubActionsExecutorSubgraph,
    GithubUploadSubgraph,
    HtmlSubgraph,
    LatexSubgraph,
    PrepareRepositorySubgraph,
    ReadmeSubgraph,
    RetrieveCodeSubgraph,
    RetrieveHuggingFaceSubgraph,
    RetrievePaperContentSubgraph,
    ReviewPaperSubgraph,
    SummarizePaperSubgraph,
    WriterSubgraph,
)
from airas.features.github.github_download_subgraph import GithubDownloadSubgraph
from airas.types.github import GitHubRepositoryInfo
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

runner_type = "A100_80GM×8"
# runner_type = "Tesla_T4"
secret_names = ["HF_TOKEN", "ANTHROPIC_API_KEY"]

n_queries = 5  # 論文検索時のサブクエリの数
max_results_per_query = 5  # 論文検索時の各サブクエリに対する論文数
num_reference_paper = 2  # 論文作成時に追加で参照する論文数
method_refinement_rounds = 0  # 新規手法の改良回数
num_retrieve_related_papers = 20  # 新規手法作成時に新規性を確認するのに取得する論文数
num_experiments = 2  # 生成する実験数
max_huggingface_results_per_search = (
    10  # modelやdatasetごとのHuggingFaceからの候補の取得数
)
# CreateCodeSubgraph parameters
max_base_code_validations = 10  # 全実験で共通するコードの最大改善回数
max_experiment_code_validations = 10  # 各実験コードの最大改善回数
consistency_score_threshold = 1  # 実験に一貫性スコア（1-10）
writing_refinement_rounds = 2  # 論文の推敲回数
max_filtered_references = 20  # 論文中で引用する参考文献の最大数
max_chktex_revisions = 3  # LaTeXの文法チェックの最大修正回数
max_compile_revisions = 3  # LaTeXのコンパイルエラーの最大修正回数


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
    llm_mapping={"extract_reference_titles": "gemini-2.5-flash-lite-preview-06-17"},
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
    num_experiments=num_experiments,
    llm_mapping={
        "generate_experiment_strategy": "o3-2025-04-16",
        "generate_experiments": "o3-2025-04-16",
    },
)
retrieve_hugging_face = RetrieveHuggingFaceSubgraph(
    include_gated=False,
    llm_mapping={
        "select_resources": "gemini-2.5-flash",
    },
)
coder = CreateCodeSubgraph(
    runner_type=runner_type,
    secret_names=secret_names,
    llm_mapping={
        "generate_base_code": "o3-2025-04-16",
        "derive_specific_experiments": "o3-2025-04-16",
        "validate_base_code": "o3-2025-04-16",
        "validate_experiment_code": "o3-2025-04-16",
    },
    max_base_code_validations=max_base_code_validations,
    max_experiment_code_validations=max_experiment_code_validations,
)
executor = GitHubActionsExecutorSubgraph(runner_type=runner_type)
evaluate_consistency = EvaluateExperimentalConsistencySubgraph(
    consistency_score_threshold=1,
    llm_mapping={
        "evaluate_experimental_consistency": "o3-2025-04-16",
    },
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
    retrieve_hugging_face,
    coder,
    executor,
    evaluate_consistency,  # TODO 現状イテレーションできない
    analysis,
    reference_extractor,
    retrieve_reference_paper_content,
    create_bibfile,
    writer,
    review,
    latex,
    html,
    readme,
]


def run_subgraphs(subgraph_list, state, workflow_config=DEFAULT_WORKFLOW_CONFIG):
    for subgraph in tqdm(subgraph_list, desc="Executing Research Workflow"):
        subgraph_name = subgraph.__class__.__name__
        print(f"--- Running Subgraph: {subgraph_name} ---")

        state = subgraph.run(state)
        _ = uploader.run(state)
        print(f"--- Finished Subgraph: {subgraph_name} ---\n")

        # # TODO: Implement iteration logic based on experiment evaluation
        # if subgraph_name == "EvaluateExperimentalConsistencySubgraph":
        #     # Count experiments selected for paper
        #     if state.get("new_method") and state["new_method"].experimental_design:
        #         selected_count = sum(
        #             1 for exp in state["new_method"].experimental_design.experiments
        #             if exp.evaluation and exp.evaluation.is_selected_for_paper
        #         )
        #
        #         MIN_SELECTED_EXPERIMENTS = 1  # Minimum number of experiments to proceed
        #         MAX_ITERATIONS = 3  # Maximum number of iteration attempts
        #
        #         if selected_count < MIN_SELECTED_EXPERIMENTS:
        #             iteration_count = state.get("consistency_iteration_count", 0) + 1
        #
        #             if iteration_count < MAX_ITERATIONS:
        #                 logger.warning(
        #                     f"Only {selected_count} experiments selected (minimum: {MIN_SELECTED_EXPERIMENTS}). "
        #                     f"Restarting from CreateExperimentalDesignSubgraph (iteration {iteration_count}/{MAX_ITERATIONS})"
        #                 )
        #                 state["consistency_iteration_count"] = iteration_count
        #
        #                 # Find index of CreateExperimentalDesignSubgraph and restart from there
        #                 restart_index = next(
        #                     (i for i, sg in enumerate(subgraph_list)
        #                      if sg.__class__.__name__ == "CreateExperimentalDesignSubgraph"),
        #                     None
        #                 )
        #                 if restart_index is not None:
        #                     return run_subgraphs(subgraph_list[restart_index:], state, workflow_config)
        #             else:
        #                 logger.warning(
        #                     f"Maximum iterations ({MAX_ITERATIONS}) reached with {selected_count} selected experiments. "
        #                     f"Proceeding to next subgraph..."
        #                 )
        #         else:
        #             logger.info(f"{selected_count} experiments selected for paper. Proceeding to analysis...")


def execute_workflow(
    github_owner: str,
    repository_name: str,
    research_topic_list: list[str],
    subgraph_list: list = subgraph_list,
):
    for index, research_topic in enumerate(research_topic_list):
        state = {
            "github_repository_info": GitHubRepositoryInfo(
                github_owner=github_owner,
                repository_name=repository_name,
                branch_name=f"research-{index}",
            ),
            "research_topic": research_topic,
        }

        _ = PrepareRepositorySubgraph().run(state)
        try:
            _ = run_subgraphs(subgraph_list, state)
        except Exception:
            raise


def resume_workflow(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    start_subgraph_name: str,
    subgraph_list: list = subgraph_list,
):
    start_index = None
    for i, subgraph in enumerate(subgraph_list):
        if subgraph.__class__.__name__ == start_subgraph_name:
            start_index = i
            break

    if start_index is None:
        raise ValueError(
            f"Subgraph '{start_subgraph_name}' not found in subgraph_list. "
            f"Available: {[sg.__class__.__name__ for sg in subgraph_list]}"
        )

    logger.info(
        f"Resuming workflow from subgraph: {start_subgraph_name} (index {start_index})"
    )

    state = {
        "github_repository_info": GitHubRepositoryInfo(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
        ),
    }

    logger.info(f"Downloading existing state from branch: {branch_name}")
    download_subgraph = GithubDownloadSubgraph()
    state = download_subgraph.run(state)

    remaining_subgraphs = subgraph_list[start_index:]
    logger.info(
        f"Executing {len(remaining_subgraphs)} subgraphs starting from {start_subgraph_name}"
    )

    try:
        run_subgraphs(remaining_subgraphs, state)
    except Exception:
        raise


if __name__ == "__main__":
    github_owner = "auto-res2"
    repository_name = "experiment_matsuzawa_251002"
    research_topic_list = [
        "Improving efficiency of hyperparameter optimization",
    ]

    # execute_workflow(
    #     github_owner, repository_name, research_topic_list=research_topic_list
    # )

    resume_workflow(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name="research-0",
        start_subgraph_name="CreateCodeSubgraph",
        subgraph_list=subgraph_list,
    )
