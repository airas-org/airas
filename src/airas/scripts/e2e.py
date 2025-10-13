import logging
from datetime import datetime

from tqdm import tqdm

from airas.config.workflow_config import DEFAULT_WORKFLOW_CONFIG
from airas.features import (
    AnalyticSubgraph,
    CreateBibfileSubgraph,
    CreateBranchSubgraph,
    CreateCodeSubgraph,
    CreateExperimentalDesignSubgraph,
    CreateMethodSubgraphV2,
    EvaluateExperimentalConsistencySubgraph,
    ExecuteExperimentSubgraph,
    ExtractReferenceTitlesSubgraph,
    GenerateQueriesSubgraph,
    GetPaperTitlesFromDBSubgraph,
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
from airas.scripts.settings import Settings
from airas.types.github import GitHubRepositoryInfo
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

settings = Settings().apply_profile_overrides()

generate_queries = GenerateQueriesSubgraph(
    llm_mapping={
        "generate_queries": settings.llm_mapping.generate_queries,
    },
    n_queries=settings.generate_queries.n_queries,
)
get_paper_titles = GetPaperTitlesFromDBSubgraph(
    max_results_per_query=settings.get_paper_titles_from_db.max_results_per_query,
    semantic_search=settings.get_paper_titles_from_db.semantic_search,
)
retrieve_paper_content = RetrievePaperContentSubgraph(
    target_study_list_source="research_study_list",
    llm_mapping={
        "search_arxiv_id_from_title": settings.llm_mapping.search_arxiv_id_from_title,
    },
    paper_provider=settings.retrieve_paper_content.paper_provider,
)
summarize_paper = SummarizePaperSubgraph(
    llm_mapping={"summarize_paper": settings.llm_mapping.summarize_paper}
)
retrieve_code = RetrieveCodeSubgraph(
    llm_mapping={
        "extract_github_url_from_text": settings.llm_mapping.extract_github_url_from_text,
        "extract_experimental_info": settings.llm_mapping.extract_experimental_info,
    }
)
reference_extractor = ExtractReferenceTitlesSubgraph(
    llm_mapping={
        "extract_reference_titles": settings.llm_mapping.extract_reference_titles
    },
    num_reference_paper=settings.extract_reference_titles.num_reference_paper,
)
retrieve_reference_paper_content = RetrievePaperContentSubgraph(
    target_study_list_source="reference_research_study_list",
    llm_mapping={
        "search_arxiv_id_from_title": settings.llm_mapping.search_arxiv_id_from_title,
    },
    paper_provider=settings.retrieve_paper_content.paper_provider,
)

create_method = CreateMethodSubgraphV2(
    llm_mapping={
        "generate_ide_and_research_summary": settings.llm_mapping.generate_ide_and_research_summary,
        "evaluate_novelty_and_significance": settings.llm_mapping.evaluate_novelty_and_significance,
        "refine_idea_and_research_summary": settings.llm_mapping.refine_idea_and_research_summary,
        "search_arxiv_id_from_title": settings.llm_mapping.search_arxiv_id_from_title,
    },
    method_refinement_rounds=settings.create_method.method_refinement_rounds,
    num_retrieve_related_papers=settings.create_method.num_retrieve_related_papers,
)
create_experimental_design = CreateExperimentalDesignSubgraph(
    runner_type=settings.runner_type,
    num_models_to_use=settings.create_experimental_design.num_models_to_use,
    num_datasets_to_use=settings.create_experimental_design.num_datasets_to_use,
    num_comparative_methods=settings.create_experimental_design.num_comparative_methods,
    llm_mapping={
        "generate_experiment_strategy": settings.llm_mapping.generate_experiment_strategy,
        "generate_experiments": settings.llm_mapping.generate_experiments,
    },
)
retrieve_hugging_face = RetrieveHuggingFaceSubgraph(
    include_gated=False,
    max_results_per_search=settings.retrieve_hugging_face.max_results_per_search,
    max_models=settings.retrieve_hugging_face.max_models,
    max_datasets=settings.retrieve_hugging_face.max_datasets,
    llm_mapping={
        "select_resources": settings.llm_mapping.select_resources,
    },
)
coder = CreateCodeSubgraph(
    runner_type=settings.runner_type,
    secret_names=settings.secret_names,
    llm_mapping={
        "generate_base_code": settings.llm_mapping.generate_base_code,
        "derive_specific_experiments": settings.llm_mapping.derive_specific_experiments,
        "validate_base_code": settings.llm_mapping.validate_base_code,
        "validate_experiment_code": settings.llm_mapping.validate_experiment_code,
    },
    max_base_code_validations=settings.create_code.max_base_code_validations,
    max_experiment_code_validations=settings.create_code.max_experiment_code_validations,
)
executor = ExecuteExperimentSubgraph(runner_type=settings.runner_type)
evaluate_consistency = EvaluateExperimentalConsistencySubgraph(
    consistency_score_threshold=settings.evaluate_experimental_consistency.consistency_score_threshold,
    llm_mapping={
        "evaluate_experimental_consistency": settings.llm_mapping.evaluate_experimental_consistency,
    },
)
analysis = AnalyticSubgraph(
    llm_mapping={
        "analytic_node": settings.llm_mapping.analytic_node,
    }
)
create_bibfile = CreateBibfileSubgraph(
    llm_mapping={
        "filter_references": settings.llm_mapping.filter_references,
    },
    latex_template_name="iclr2024",
    max_filtered_references=settings.create_bibfile.max_filtered_references,
)
writer = WriterSubgraph(
    llm_mapping={
        "write_paper": settings.llm_mapping.write_paper,
        "refine_paper": settings.llm_mapping.refine_paper,
    },
    writing_refinement_rounds=settings.writer.writing_refinement_rounds,
)
review = ReviewPaperSubgraph(
    llm_mapping={
        "review_paper": settings.llm_mapping.review_paper,
    }
)
latex = LatexSubgraph(
    llm_mapping={
        "convert_to_latex": settings.llm_mapping.convert_to_latex,
    },
    latex_template_name="iclr2024",
)
readme = ReadmeSubgraph()
html = HtmlSubgraph(
    llm_mapping={
        "convert_to_html": settings.llm_mapping.convert_to_html,
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
    for subgraph in tqdm(subgraph_list, desc="Executing AIRAS"):
        subgraph_name = subgraph.__class__.__name__
        print(f"--- Running Subgraph: {subgraph_name} ---")

        state = subgraph.run(state)
        _ = uploader.run(state)
        print(f"--- Finished Subgraph: {subgraph_name} ---\n")


def execute_workflow(
    github_owner: str,
    repository_name: str,
    research_topic: str,
    branch_name: str = "main",
    subgraph_list: list = subgraph_list,
):
    state = {
        "github_repository_info": GitHubRepositoryInfo(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
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
    source_branch_name: str,
    start_subgraph_name: str,
    target_branch_name: str,
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
            branch_name=source_branch_name,
        ),
    }

    logger.info(
        f"Creating new branch '{target_branch_name}' from '{source_branch_name}' "
        f"at subgraph '{start_subgraph_name}'"
    )
    state = CreateBranchSubgraph(
        new_branch_name=target_branch_name,
        start_subgraph_name=start_subgraph_name,
    ).run(state)

    logger.info(f"Downloading existing state from branch: {target_branch_name}")
    state = GithubDownloadSubgraph().run(state)

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
    suffix = "tanaka"
    exec_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    repository_name = f"airas-{exec_time}-{suffix}"
    research_topic_list = "LLMの新しい損失関数"

    # TODO: argparse

    # execute_workflow(github_owner, repository_name, research_topic=research_topic_list)

    resume_workflow(
        github_owner=github_owner,
        repository_name="experiment_matsuzawa_251002",
        source_branch_name="research-0-retry-5",
        target_branch_name="research-0-retry-5-opencode-latex",
        start_subgraph_name="LatexSubgraph",
        subgraph_list=subgraph_list,
    )
