import logging
from datetime import datetime

from dependency_injector.wiring import Provide, register_loader_containers
from tqdm import tqdm

from airas.services.api_client.api_clients_container import (
    AsyncContainer,
    SyncContainer,
    async_container,
    sync_container,
)

# Register import hook before importing features to enable automatic dependency injection
register_loader_containers(sync_container)
register_loader_containers(async_container)


from airas.features import (  # noqa: E402
    AnalyticSubgraph,
    CreateBibfileSubgraph,
    # CreateBranchSubgraph,
    CreateCodeSubgraph,
    CreateExperimentalDesignSubgraph,
    CreateHypothesisSubgraph,
    CreateMethodSubgraph,
    ExecuteExperimentSubgraph,
    ExtractReferenceTitlesSubgraph,
    GenerateQueriesSubgraph,
    GetPaperTitlesFromDBSubgraph,
    GithubDownloadSubgraph,
    GithubUploadSubgraph,
    HtmlSubgraph,
    LatexSubgraph,
    PrepareRepositorySubgraph,
    ReadmeSubgraph,
    RetrieveCodeSubgraph,
    RetrieveHuggingFaceSubgraph,
    RetrievePaperContentSubgraph,
    SummarizePaperSubgraph,
    WriterSubgraph,
)
from airas.scripts.settings import Settings  # noqa: E402
from airas.types.github import GitHubRepositoryInfo  # noqa: E402
from airas.utils.logging_utils import setup_logging  # noqa: E402

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
    qdrant_client=Provide[SyncContainer.qdrant_client],
    llm_client=Provide[AsyncContainer.gemini_embedding_001],
    max_results_per_query=settings.get_paper_titles_from_db.max_results_per_query,
    semantic_search=settings.get_paper_titles_from_db.semantic_search,
)
retrieve_paper_content = RetrievePaperContentSubgraph(
    target_study_list_source="research_study_list",
    llm_mapping={
        "search_arxiv_id_from_title": settings.llm_mapping.search_arxiv_id_from_title,
    },
    arxiv_client=Provide[SyncContainer.arxiv_client],
    ss_client=Provide[SyncContainer.semantic_scholar_client],
    llm_client=Provide[AsyncContainer.gpt_5_mini_2025_08_07],
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
    arxiv_client=Provide[SyncContainer.arxiv_client],
    ss_client=Provide[SyncContainer.semantic_scholar_client],
    llm_client=Provide[AsyncContainer.gpt_5_mini_2025_08_07],
    paper_provider=settings.retrieve_paper_content.paper_provider,
)

create_hypothesis = CreateHypothesisSubgraph(
    qdrant_client=Provide[SyncContainer.qdrant_client],
    llm_client=Provide[AsyncContainer.llm_facade_client],
    llm_mapping={
        "generate_idea_and_research_summary": settings.llm_mapping.generate_idea_and_research_summary,
        "evaluate_novelty_and_significance": settings.llm_mapping.evaluate_novelty_and_significance,
        "refine_idea_and_research_summary": settings.llm_mapping.refine_idea_and_research_summary,
        "search_arxiv_id_from_title": settings.llm_mapping.search_arxiv_id_from_title,
    },
    refinement_rounds=settings.create_hypothesis.refinement_rounds,
    num_retrieve_related_papers=settings.create_hypothesis.num_retrieve_related_papers,
)

create_method = CreateMethodSubgraph(
    llm_mapping={
        "improve_method": settings.llm_mapping.improve_method,
    },
)

create_experimental_design = CreateExperimentalDesignSubgraph(
    runner_type=settings.runner_type,
    num_models_to_use=settings.create_experimental_design.num_models_to_use,
    num_datasets_to_use=settings.create_experimental_design.num_datasets_to_use,
    num_comparative_methods=settings.create_experimental_design.num_comparative_methods,
    llm_mapping={
        "generate_experiment_design": settings.llm_mapping.generate_experiment_design,
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
    wandb_info=settings.wandb.to_wandb_info(),
    llm_mapping={
        "generate_run_config": settings.llm_mapping.generate_run_config,
        "generate_experiment_code": settings.llm_mapping.generate_experiment_code,
        "validate_experiment_code": settings.llm_mapping.validate_experiment_code,
    },
    max_code_validations=settings.create_code.max_code_validations,
)

executor = ExecuteExperimentSubgraph(
    runner_type=settings.runner_type,
)

analysis = AnalyticSubgraph(
    llm_mapping={
        "analytic_node": settings.llm_mapping.analytic_node,
        "evaluate_method": settings.llm_mapping.evaluate_method,
    },
    max_method_iterations=settings.analytic.max_method_iterations,
)
create_bibfile = CreateBibfileSubgraph(
    llm_mapping={
        "filter_references": settings.llm_mapping.filter_references,
    },
    latex_template_name=settings.latex_template_name,
    max_filtered_references=settings.create_bibfile.max_filtered_references,
)
writer = WriterSubgraph(
    llm_mapping={
        "write_paper": settings.llm_mapping.write_paper,
        "refine_paper": settings.llm_mapping.refine_paper,
    },
    writing_refinement_rounds=settings.writer.writing_refinement_rounds,
)
latex = LatexSubgraph(
    llm_mapping={
        "convert_to_latex": settings.llm_mapping.convert_to_latex,
    },
    latex_template_name=settings.latex_template_name,
)
html = HtmlSubgraph(
    llm_mapping={
        "convert_to_html": settings.llm_mapping.convert_to_html,
    }
)
readme = ReadmeSubgraph()
uploader = GithubUploadSubgraph()


# Subgraph lists organized by workflow phase
initial_subgraph_list = [
    # --- Search & Investigation ---
    generate_queries,
    get_paper_titles,
    retrieve_paper_content,
    summarize_paper,
    retrieve_code,
    # --- Hypothesis Creation ---
    create_hypothesis,
]

# Method iteration loop subgraphs
iteration_subgraph_list = [
    create_method,
    create_experimental_design,
    retrieve_hugging_face,
    coder,
    executor,
    analysis,
]

# Final publication subgraphs
final_subgraph_list = [
    reference_extractor,
    retrieve_reference_paper_content,
    create_bibfile,
    writer,
    latex,
    html,
    readme,
]

subgraph_list = initial_subgraph_list + iteration_subgraph_list + final_subgraph_list


def run_subgraphs(subgraph_list, state):
    for subgraph in tqdm(subgraph_list, desc="Executing AIRAS"):
        subgraph_name = subgraph.__class__.__name__
        print(f"--- Running Subgraph: {subgraph_name} ---")

        state = subgraph.run(state)
        _ = uploader.run(state)
        print(f"--- Finished Subgraph: {subgraph_name} ---\n")

    return state


def execute_workflow(
    github_owner: str,
    repository_name: str,
    research_topic: str,
    branch_name: str = "main",
):
    method_iteration_attempts = settings.method_iteration_attempts

    state = {
        "github_repository_info": GitHubRepositoryInfo(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
        ),
        "research_topic": research_topic,
    }

    _ = PrepareRepositorySubgraph().run(state)

    # Download existing state if available (for resuming from a specific subgraph)
    logger.info("Attempting to download existing research state...")
    state = GithubDownloadSubgraph().run(state)

    try:
        # Phase 1: Initial phase (research + hypothesis)
        logger.info("=== Phase 1: Initial Research & Hypothesis Creation ===")
        state = run_subgraphs(initial_subgraph_list, state)

        # Phase 2: Method iteration loop
        logger.info(
            f"=== Phase 2: Method Iteration Loop ({method_iteration_attempts} iterations) ==="
        )
        for iteration in range(method_iteration_attempts):
            logger.info(
                f"--- Method Iteration {iteration + 1}/{method_iteration_attempts} ---"
            )
            state = run_subgraphs(iteration_subgraph_list, state)

            # After analysis, create a new iteration in research_session
            if iteration < method_iteration_attempts - 1:
                logger.info("Preparing for next iteration...")
                # The next iteration will be created by create_method subgraph

        # Phase 3: Final publication phase
        logger.info("=== Phase 3: Final Publication ===")
        state = run_subgraphs(final_subgraph_list, state)

    except Exception:
        raise


# def resume_workflow(
#     github_owner: str,
#     repository_name: str,
#     source_branch_name: str,
#     start_subgraph_name: str,
#     target_branch_name: str,
#     subgraph_list: list = subgraph_list,
# ):
#     start_index = None
#     for i, subgraph in enumerate(subgraph_list):
#         if subgraph.__class__.__name__ == start_subgraph_name:
#             start_index = i
#             break

#     if start_index is None:
#         raise ValueError(
#             f"Subgraph '{start_subgraph_name}' not found in subgraph_list. "
#             f"Available: {[sg.__class__.__name__ for sg in subgraph_list]}"
#         )

#     logger.info(
#         f"Resuming workflow from subgraph: {start_subgraph_name} (index {start_index})"
#     )

#     state = {
#         "github_repository_info": GitHubRepositoryInfo(
#             github_owner=github_owner,
#             repository_name=repository_name,
#             branch_name=source_branch_name,
#         ),
#     }

#     logger.info(
#         f"Creating new branch '{target_branch_name}' from '{source_branch_name}' "
#         f"at subgraph '{start_subgraph_name}'"
#     )
#     state = CreateBranchSubgraph(
#         new_branch_name=target_branch_name,
#         start_subgraph_name=start_subgraph_name,
#     ).run(state)

#     logger.info(f"Downloading existing state from branch: {target_branch_name}")
#     state = GithubDownloadSubgraph().run(state)

#     remaining_subgraphs = subgraph_list[start_index:]
#     logger.info(
#         f"Executing {len(remaining_subgraphs)} subgraphs starting from {start_subgraph_name}"
#     )

#     try:
#         run_subgraphs(remaining_subgraphs, state)
#     except Exception:
#         raise


if __name__ == "__main__":
    github_owner = "auto-res2"
    suffix = "tanaka"
    exec_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    repository_name = f"airas-{exec_time}-{suffix}"

    research_topic_list = "Improving fine-tuning performance of language models."

    try:
        execute_workflow(
            github_owner, repository_name, research_topic=research_topic_list
        )

        # resume_workflow(
        #     github_owner=github_owner,
        #     repository_name="experiment_matsuzawa_251002",
        #     source_branch_name="research-0-retry-5",
        #     target_branch_name="research-0-retry-5-opencode-latex",
        #     start_subgraph_name="LatexSubgraph",
        #     subgraph_list=subgraph_list,
        # )

        # TODO: The current CreateBranchSubgraph traces the f"[subgraph: {subgraph_name}]" marker in the commit message.
        # However, if ExecuteExperimentSubgraph stops with an error,
        # for example, no commit will exist, forcing a re-execution from the previous subgraph (CreateCodeSubgraph).
        # It seems desirable to change the specification to absorb the changes up to the previous marker into a new branch.
    finally:
        logger.info("Shutting down DI container resources...")
        sync_container.shutdown_resources()
        logger.info("Resource cleanup completed.")
