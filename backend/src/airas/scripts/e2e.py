import asyncio
import logging
import sys
from datetime import datetime

from dependency_injector.wiring import Provide, inject
from tqdm.asyncio import tqdm as atqdm

from airas.core.container import Container, container
from airas.features import (
    AnalyzeExperimentSubgraph,
    CreateBibfileSubgraph,
    CreateCodeSubgraph,
    CreateExperimentalDesignSubgraph,
    CreateHypothesisSubgraph,
    CreateMethodSubgraph,
    ExecuteEvaluationSubgraph,
    ExecuteExperimentSubgraph,
    ExtractReferenceTitlesSubgraph,
    GenerateHtmlSubgraph,
    GenerateLatexSubgraph,
    GenerateQueriesSubgraph,
    GetPaperTitlesFromDBSubgraph,
    GithubDownloadSubgraph,
    GithubUploadSubgraph,
    PrepareRepositorySubgraph,
    PublishHtmlSubgraph,
    PublishLatexSubgraph,
    PushCodeSubgraph,
    ReadmeSubgraph,
    RetrieveCodeSubgraph,
    RetrieveHuggingFaceSubgraph,
    RetrievePaperContentSubgraph,
    SummarizePaperSubgraph,
    WriterSubgraph,
)
from airas.scripts.settings import Settings
from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.hugging_face_client import HuggingFaceClient
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.openalex_client import OpenAlexClient
from airas.services.api_client.qdrant_client import QdrantClient
from airas.services.api_client.semantic_scholar_client import SemanticScholarClient
from airas.types.github import GitHubRepositoryInfo
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@inject
async def create_subgraphs(
    settings: Settings,
    github_client: GithubClient = Provide[Container.github_client],
    arxiv_client: ArxivClient = Provide[Container.arxiv_client],
    semantic_scholar_client: SemanticScholarClient = Provide[
        Container.semantic_scholar_client
    ],
    openalex_client: OpenAlexClient = Provide[Container.openalex_client],
    hugging_face_client: HuggingFaceClient = Provide[Container.hugging_face_client],
    qdrant_client: QdrantClient = Provide[Container.qdrant_client],
    llm_facade_client: LLMFacadeClient = Provide[Container.llm_facade_client],
):
    # GitHub subgraphs
    prepare_repository = PrepareRepositorySubgraph(
        github_client=github_client,
        is_private=False,
    )
    github_downloader = GithubDownloadSubgraph(github_client=github_client)
    github_uploader = GithubUploadSubgraph(github_client=github_client)

    # --- Initial Phase: Research & Investigation ---
    generate_queries = GenerateQueriesSubgraph(
        llm_mapping={
            "generate_queries": settings.llm_mapping.generate_queries,
        },
        llm_client=llm_facade_client,
        n_queries=settings.generate_queries.n_queries,
    )

    get_paper_titles = GetPaperTitlesFromDBSubgraph(
        qdrant_client=qdrant_client,
        llm_client=llm_facade_client,
        max_results_per_query=settings.get_paper_titles_from_db.max_results_per_query,
        semantic_search=settings.get_paper_titles_from_db.semantic_search,
    )

    retrieve_paper_content = RetrievePaperContentSubgraph(
        target_study_list_source="research_study_list",
        llm_mapping={
            "search_arxiv_id_from_title": settings.llm_mapping.search_arxiv_id_from_title,
        },
        arxiv_client=arxiv_client,
        ss_client=semantic_scholar_client,
        llm_client=llm_facade_client,
        paper_provider=settings.retrieve_paper_content.paper_provider,
    )

    summarize_paper = SummarizePaperSubgraph(
        llm_mapping={"summarize_paper": settings.llm_mapping.summarize_paper},
        llm_client=llm_facade_client,
    )

    retrieve_code = RetrieveCodeSubgraph(
        llm_mapping={
            "extract_github_url_from_text": settings.llm_mapping.extract_github_url_from_text,
            "extract_experimental_info": settings.llm_mapping.extract_experimental_info,
        },
        llm_client=llm_facade_client,
        github_client=github_client,
    )

    create_hypothesis = CreateHypothesisSubgraph(
        qdrant_client=qdrant_client,
        arxiv_client=arxiv_client,
        ss_client=semantic_scholar_client,
        llm_client=llm_facade_client,
        llm_mapping={
            "generate_hypothesis": settings.llm_mapping.generate_idea_and_research_summary,
            "evaluate_novelty_and_significance": settings.llm_mapping.evaluate_novelty_and_significance,
            "refine_hypothesis": settings.llm_mapping.refine_idea_and_research_summary,
            "search_arxiv_id_from_title": settings.llm_mapping.search_arxiv_id_from_title,
        },
        refinement_rounds=settings.create_hypothesis.refinement_rounds,
        num_retrieve_related_papers=settings.create_hypothesis.num_retrieve_related_papers,
    )

    # --- Iteration Phase: Method Development ---
    create_method = CreateMethodSubgraph(
        llm_client=llm_facade_client,
        llm_mapping={
            "improve_method": settings.llm_mapping.improve_method,
        },
    )

    create_experimental_design = CreateExperimentalDesignSubgraph(
        llm_client=llm_facade_client,
        runner_type=settings.runner_type,
        num_models_to_use=settings.create_experimental_design.num_models_to_use,
        num_datasets_to_use=settings.create_experimental_design.num_datasets_to_use,
        num_comparative_methods=settings.create_experimental_design.num_comparative_methods,
        llm_mapping={
            "generate_experiment_design": settings.llm_mapping.generate_experiment_design,
        },
    )

    retrieve_hugging_face = RetrieveHuggingFaceSubgraph(
        hf_client=hugging_face_client,
        llm_client=llm_facade_client,
        include_gated=False,
        max_results_per_search=settings.retrieve_hugging_face.max_results_per_search,
        max_models=settings.retrieve_hugging_face.max_models,
        max_datasets=settings.retrieve_hugging_face.max_datasets,
        llm_mapping={
            "select_resources": settings.llm_mapping.select_resources,
        },
    )

    coder = CreateCodeSubgraph(
        llm_client=llm_facade_client,
        runner_type=settings.runner_type,
        wandb_info=settings.wandb.to_wandb_info(),
        llm_mapping={
            "generate_run_config": settings.llm_mapping.generate_run_config,
            "generate_experiment_code": settings.llm_mapping.generate_experiment_code,
            "validate_experiment_code": settings.llm_mapping.validate_experiment_code,
        },
        max_code_validations=settings.create_code.max_code_validations,
    )

    push_code = PushCodeSubgraph(
        github_client=github_client,
        secret_names=settings.secret_names,
    )

    executor = ExecuteExperimentSubgraph(
        llm_client=llm_facade_client,
        github_client=github_client,
        runner_type=settings.runner_type,
    )

    execute_evaluation = ExecuteEvaluationSubgraph(
        github_client=github_client,
    )

    analyze_experiment = AnalyzeExperimentSubgraph(
        llm_client=llm_facade_client,
        llm_mapping={
            "analyze_experiment": settings.llm_mapping.analyze_experiment,
            "evaluate_method": settings.llm_mapping.evaluate_method,
        },
    )

    # --- Final Phase: Publication ---
    reference_extractor = ExtractReferenceTitlesSubgraph(
        llm_client=llm_facade_client,
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
        arxiv_client=arxiv_client,
        ss_client=semantic_scholar_client,
        llm_client=llm_facade_client,
        paper_provider=settings.retrieve_paper_content.paper_provider,
    )

    create_bibfile = CreateBibfileSubgraph(
        llm_client=llm_facade_client,
        github_client=github_client,
        llm_mapping={
            "filter_references": settings.llm_mapping.filter_references,
        },
        latex_template_name=settings.latex_template_name,
        max_filtered_references=settings.create_bibfile.max_filtered_references,
    )

    writer = WriterSubgraph(
        llm_client=llm_facade_client,
        llm_mapping={
            "write_paper": settings.llm_mapping.write_paper,
            "refine_paper": settings.llm_mapping.refine_paper,
        },
        writing_refinement_rounds=settings.writer.writing_refinement_rounds,
    )

    generate_latex = GenerateLatexSubgraph(
        llm_client=llm_facade_client,
        llm_mapping={
            "convert_to_latex": settings.llm_mapping.convert_to_latex,
        },
    )

    publish_latex = PublishLatexSubgraph(
        github_client=github_client,
        latex_template_name=settings.latex_template_name,
    )

    generate_html = GenerateHtmlSubgraph(
        llm_client=llm_facade_client,
        llm_mapping={
            "convert_to_html": settings.llm_mapping.convert_to_html,
        },
    )

    publish_html = PublishHtmlSubgraph(
        github_client=github_client,
    )

    readme = ReadmeSubgraph(
        github_client=github_client,
    )

    # Organize subgraphs by workflow phase
    initial_subgraph_list = [
        generate_queries,
        get_paper_titles,
        retrieve_paper_content,
        summarize_paper,
        retrieve_code,
        create_hypothesis,
    ]

    iteration_subgraph_list = [
        create_method,
        create_experimental_design,
        retrieve_hugging_face,
        coder,
        push_code,
        executor,
        execute_evaluation,
        analyze_experiment,
    ]

    final_subgraph_list = [
        reference_extractor,
        retrieve_reference_paper_content,
        create_bibfile,
        writer,
        generate_latex,
        publish_latex,
        generate_html,
        publish_html,
        readme,
    ]

    return {
        "prepare_repository": prepare_repository,
        "github_downloader": github_downloader,
        "github_uploader": github_uploader,
        "initial_subgraphs": initial_subgraph_list,
        "iteration_subgraphs": iteration_subgraph_list,
        "final_subgraphs": final_subgraph_list,
    }


async def run_subgraphs(subgraph_list, state, uploader, description="Executing AIRAS"):
    for subgraph in atqdm(subgraph_list, desc=description):
        subgraph_name = subgraph.__class__.__name__
        logger.info(f"--- Running Subgraph: {subgraph_name} ---")

        state = await subgraph.arun(state)
        _ = await uploader.arun(state)
        logger.info(f"--- Finished Subgraph: {subgraph_name} ---\n")

    return state


async def execute_workflow(
    github_owner: str,
    repository_name: str,
    research_topic: str,
    branch_name: str = "main",
):
    settings = Settings().apply_profile_overrides()
    method_iteration_attempts = settings.method_iteration_attempts

    # Initialize DI container
    await container.init_resources()

    try:
        subgraphs = await create_subgraphs(settings)

        state = {
            "github_repository_info": GitHubRepositoryInfo(
                github_owner=github_owner,
                repository_name=repository_name,
                branch_name=branch_name,
            ),
            "research_topic": research_topic,
        }

        _ = await subgraphs["prepare_repository"].arun(state)

        logger.info("Attempting to download existing research state...")
        state = await subgraphs["github_downloader"].arun(state)

        phase_1_desc = "Phase 1: Investigation & Hypothesis Creation"
        logger.info(f"=== {phase_1_desc} ===")
        state = await run_subgraphs(
            subgraphs["initial_subgraphs"],
            state,
            subgraphs["github_uploader"],
            phase_1_desc,
        )

        phase_2_header = (
            f"Phase 2: Method Iteration Loop ({method_iteration_attempts} iterations)"
        )
        logger.info(f"=== {phase_2_header} ===")
        for iteration in range(method_iteration_attempts):
            phase_2_desc = (
                f"Method Iteration {iteration + 1}/{method_iteration_attempts}"
            )
            logger.info(f"--- {phase_2_desc} ---")
            state = await run_subgraphs(
                subgraphs["iteration_subgraphs"],
                state,
                subgraphs["github_uploader"],
                phase_2_desc,
            )

            if iteration < method_iteration_attempts - 1:
                logger.info("Preparing for next iteration...")

        phase_3_desc = "Phase 3: Writing & Publication"
        logger.info(f"=== {phase_3_desc} ===")
        state = await run_subgraphs(
            subgraphs["final_subgraphs"],
            state,
            subgraphs["github_uploader"],
            phase_3_desc,
        )

    except Exception:
        raise
    finally:
        logger.info("Shutting down DI container resources...")
        await container.shutdown_resources()
        logger.info("Resource cleanup completed.")


if __name__ == "__main__":
    github_owner = "auto-res2"
    suffix = "matsuzawa"
    exec_time = datetime.now().strftime("%Y%m%d-%H%M%S")
    repository_name = f"airas-{exec_time}-{suffix}"

    research_topic = "Learning rate optimization for fine-tuning Qwen3-0.6B on GSM8K elementary math problems"

    # Wire the container to enable dependency injection
    container.wire(modules=[sys.modules[__name__]])

    try:
        asyncio.run(
            execute_workflow(
                github_owner,
                repository_name,
                research_topic=research_topic,
            )
        )
    except Exception as e:
        logger.exception(f"Workflow execution failed: {e}")
        raise
