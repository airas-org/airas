import asyncio
import logging
from typing import Any
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experimental_analysis import ExperimentalAnalysis
from airas.core.types.experimental_design import ExperimentalDesign, RunnerConfig
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.github import (
    GitHubActionsAgent,
    GitHubActionsConclusion,
    GitHubActionsStatus,
    GitHubConfig,
)
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper import PaperContent, SearchMethod
from airas.core.types.research_history import ResearchHistory
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.core.types.wandb import WandbConfig
from airas.core.utils import to_dict_deep
from airas.infra.arxiv_client import ArxivClient
from airas.infra.db.models.e2e import Status, StepType
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.infra.litellm_client import LiteLLMClient
from airas.infra.qdrant_client import QdrantClient
from airas.usecases.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentLLMMapping,
    AnalyzeExperimentSubgraph,
)
from airas.usecases.autonomous_research.topic_open_ended_research.topic_open_ended_research_service import (
    TopicOpenEndedResearchService,
)
from airas.usecases.executors.dispatch_experiment_validation_subgraph.dispatch_experiment_validation_subgraph import (
    DispatchExperimentValidationLLMMapping,
    DispatchExperimentValidationSubgraph,
)
from airas.usecases.executors.dispatch_main_experiment_subgraph.dispatch_main_experiment_subgraph import (
    DispatchMainExperimentSubgraph,
)
from airas.usecases.executors.dispatch_sanity_check_subgraph.dispatch_sanity_check_subgraph import (
    DispatchSanityCheckSubgraph,
)
from airas.usecases.executors.dispatch_visualization_subgraph.dispatch_visualization_subgraph import (
    DispatchVisualizationSubgraph,
)
from airas.usecases.executors.fetch_experiment_code_subgraph.fetch_experiment_code_subgraph import (
    FetchExperimentCodeSubgraph,
)
from airas.usecases.executors.fetch_experiment_results_subgraph.fetch_experiment_results_subgraph import (
    FetchExperimentResultsSubgraph,
)
from airas.usecases.executors.fetch_run_ids_subgraph.fetch_run_ids_subgraph import (
    FetchRunIdsSubgraph,
)
from airas.usecases.generators.dispatch_code_generation_subgraph.dispatch_code_generation_subgraph import (
    DispatchCodeGenerationLLMMapping,
    DispatchCodeGenerationSubgraph,
)
from airas.usecases.generators.generate_experimental_design_subgraph.generate_experimental_design_subgraph import (
    GenerateExperimentalDesignLLMMapping,
    GenerateExperimentalDesignSubgraph,
)
from airas.usecases.generators.generate_hypothesis_subgraph.generate_hypothesis_subgraph_v0 import (
    GenerateHypothesisSubgraphV0,
    GenerateHypothesisSubgraphV0LLMMapping,
)
from airas.usecases.generators.generate_queries_subgraph.generate_queries_subgraph import (
    GenerateQueriesLLMMapping,
    GenerateQueriesSubgraph,
)
from airas.usecases.github.download_github_actions_artifacts_subgraph.download_github_actions_artifacts_subgraph import (
    DownloadGithubActionsArtifactsSubgraph,
)
from airas.usecases.github.github_upload_subgraph import GithubUploadSubgraph
from airas.usecases.github.nodes.create_branch import create_branches_for_run_ids
from airas.usecases.github.poll_github_actions_subgraph.poll_github_actions_subgraph import (
    PollGithubActionsSubgraph,
)
from airas.usecases.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)
from airas.usecases.github.push_github_subgraph.push_github_subgraph import (
    PushGitHubSubgraph,
)
from airas.usecases.github.set_github_actions_secrets_subgraph.set_github_actions_secrets_subgraph import (
    SetGithubActionsSecretsSubgraph,
)
from airas.usecases.publication.compile_latex_subgraph.compile_latex_subgraph import (
    CompileLatexLLMMapping,
    CompileLatexSubgraph,
)
from airas.usecases.publication.generate_latex_subgraph.generate_latex_subgraph import (
    GenerateLatexLLMMapping,
    GenerateLatexSubgraph,
)
from airas.usecases.publication.push_latex_subgraph.push_latex_subgraph import (
    PushLatexSubgraph,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
    RetrievePaperSubgraphLLMMapping,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.search_paper_titles_from_airas_db_subgraph import (
    SearchPaperTitlesFromAirasDbSubgraph,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.search_paper_titles_from_qdrant_subgraph import (
    SearchPaperTitlesFromQdrantLLMMapping,
    SearchPaperTitlesFromQdrantSubgraph,
)
from airas.usecases.writers.generate_bibfile_subgraph.generate_bibfile_subgraph import (
    GenerateBibfileSubgraph,
)
from airas.usecases.writers.write_subgraph.write_subgraph import (
    WriteLLMMapping,
    WriteSubgraph,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("execute_e2e_v2")(f)  # noqa: E731


class WorkflowExecutionError(Exception):
    pass


class WorkflowValidationError(WorkflowExecutionError):
    pass


class GitHubActionsWorkflowError(WorkflowExecutionError):
    def __init__(
        self,
        message: str,
        workflow_name: str,
        status: str | None = None,
        conclusion: str | None = None,
    ):
        super().__init__(message)
        self.workflow_name = workflow_name
        self.status = status
        self.conclusion = conclusion


class WorkflowTimeouts:
    STANDARD_WORKFLOW = (
        3600  # 1 hour for code gen, sanity, review, main experiment, visualization
    )
    LATEX_COMPILATION = 300  # 5 minutes for LaTeX compilation


class TopicOpenEndedResearchSubgraphV2LLMMapping(BaseModel):
    generate_queries: GenerateQueriesLLMMapping | None = None
    retrieve_paper: RetrievePaperSubgraphLLMMapping | None = None
    generate_hypothesis: GenerateHypothesisSubgraphV0LLMMapping | None = None
    generate_experimental_design: GenerateExperimentalDesignLLMMapping | None = None
    dispatch_code_generation: DispatchCodeGenerationLLMMapping | None = None
    dispatch_experiment_validation: DispatchExperimentValidationLLMMapping | None = None
    analyze_experiment: AnalyzeExperimentLLMMapping | None = None
    write: WriteLLMMapping | None = None
    generate_latex: GenerateLatexLLMMapping | None = None
    compile_latex: CompileLatexLLMMapping | None = None
    search_paper_titles_from_qdrant: SearchPaperTitlesFromQdrantLLMMapping | None = None


class TopicOpenEndedResearchInputStateV2(TypedDict):
    task_id: str | UUID
    github_config: GitHubConfig
    research_topic: str


class TopicOpenEndedResearchOutputStateV2(ExecutionTimeState):
    status: str
    research_history: ResearchHistory | None


class TopicOpenEndedResearchStateV2(
    TopicOpenEndedResearchInputStateV2,
    TopicOpenEndedResearchOutputStateV2,
    total=False,
):
    current_step: StepType
    queries: list[str]
    paper_titles: list[str]
    research_study_list: list[ResearchStudy]
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    experiment_code: ExperimentCode
    experimental_results: ExperimentalResults
    experimental_analysis: ExperimentalAnalysis
    references_bib: str
    paper_content: PaperContent
    latex_text: str
    is_repository_ready: bool
    is_branch_ready: bool
    secrets_set: bool
    retry_counts: dict[str, int]
    # dispatch-based execution states
    code_generation_dispatched: bool
    code_generation_workflow_run_id: int | None
    code_generation_workflow_status: GitHubActionsStatus | None
    code_generation_workflow_conclusion: GitHubActionsConclusion | None
    run_ids: list[str]
    current_run_id_index: int
    sanity_check_dispatched: bool
    sanity_check_workflow_run_id: int | None
    sanity_check_workflow_status: GitHubActionsStatus | None
    sanity_check_workflow_conclusion: GitHubActionsConclusion | None
    experiment_validation_dispatched: bool
    experiment_validation_workflow_run_id: int | None
    experiment_validation_workflow_status: GitHubActionsStatus | None
    experiment_validation_workflow_conclusion: GitHubActionsConclusion | None
    artifact_data: dict
    main_experiment_branches: list[str]
    main_experiment_dispatched: bool
    main_experiment_workflow_status: GitHubActionsStatus | None
    main_experiment_workflow_conclusion: GitHubActionsConclusion | None
    main_experiment_validation_dispatched: bool
    main_experiment_validation_workflow_status: GitHubActionsStatus | None
    main_experiment_validation_workflow_conclusion: GitHubActionsConclusion | None
    visualization_dispatched: bool
    visualization_workflow_run_id: int | None
    visualization_workflow_status: GitHubActionsStatus | None
    visualization_workflow_conclusion: GitHubActionsConclusion | None
    visualization_validation_dispatched: bool
    visualization_validation_workflow_run_id: int | None
    visualization_validation_workflow_status: GitHubActionsStatus | None
    visualization_validation_workflow_conclusion: GitHubActionsConclusion | None
    visualization_retry_count: int
    is_upload_successful: bool
    compile_latex_dispatched: bool
    compile_latex_workflow_status: GitHubActionsStatus | None
    compile_latex_workflow_conclusion: GitHubActionsConclusion | None


class TopicOpenEndedResearchSubgraphV2:
    MAX_RETRY_PER_RUN_ID = 10
    MAX_RETRY_FOR_VISUALIZATION = 10

    def __init__(
        self,
        github_client: GithubClient,
        arxiv_client: ArxivClient,
        langchain_client: LangChainClient,
        litellm_client: LiteLLMClient,
        qdrant_client: QdrantClient | None,
        e2e_service: TopicOpenEndedResearchService,
        runner_config: RunnerConfig,
        wandb_config: WandbConfig,
        task_id: UUID,
        is_github_repo_private: bool = False,
        search_method: SearchMethod = "airas_db",
        search_index: AirasDbPaperSearchIndex | None = None,
        collection_name: str = "airas_database",
        num_paper_search_queries: int = 2,
        papers_per_query: int = 5,
        hypothesis_refinement_iterations: int = 1,
        num_experiment_models: int = 1,
        num_experiment_datasets: int = 1,
        num_comparison_methods: int = 0,
        paper_content_refinement_iterations: int = 2,
        github_actions_agent: GitHubActionsAgent = "open_code",
        latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
        llm_mapping: TopicOpenEndedResearchSubgraphV2LLMMapping | None = None,
        min_success_rate_for_parallel_experiments: float = 1.0,
    ):
        self.search_method = search_method
        self.search_index = search_index
        self.litellm_client = litellm_client
        self.qdrant_client = qdrant_client
        self.collection_name = collection_name
        self.github_client = github_client
        self.arxiv_client = arxiv_client
        self.langchain_client = langchain_client
        self.e2e_service = e2e_service
        self.runner_config = runner_config
        self.wandb_config = wandb_config
        self.task_id = task_id
        self.is_github_repo_private = is_github_repo_private
        self.num_paper_search_queries = num_paper_search_queries
        self.papers_per_query = papers_per_query
        self.hypothesis_refinement_iterations = hypothesis_refinement_iterations
        self.num_experiment_models = num_experiment_models
        self.num_experiment_datasets = num_experiment_datasets
        self.num_comparison_methods = num_comparison_methods
        self.paper_content_refinement_iterations = paper_content_refinement_iterations
        self.latex_template_name = latex_template_name
        self.github_actions_agent = github_actions_agent
        self.llm_mapping = llm_mapping or TopicOpenEndedResearchSubgraphV2LLMMapping()
        self.min_success_rate_for_parallel_experiments = (
            min_success_rate_for_parallel_experiments
        )

    async def _poll_workflow(
        self,
        state: TopicOpenEndedResearchStateV2,
        workflow_name: str,
        recursion_limit: int = WorkflowTimeouts.STANDARD_WORKFLOW,
    ) -> tuple[GitHubActionsStatus | None, GitHubActionsConclusion | None, int | None]:
        logger.info(f"=== Poll {workflow_name} Workflow ===")
        result = (
            await PollGithubActionsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {"github_config": state["github_config"]},
                {"recursion_limit": recursion_limit},
            )
        )

        status = result.get("status")
        conclusion = result.get("conclusion")
        workflow_run_id = result.get("workflow_run_id")
        self._validate_github_actions_completion(workflow_name, status, conclusion)

        return status, conclusion, workflow_run_id

    @record_execution_time
    def _create_record(self, state: TopicOpenEndedResearchStateV2) -> dict[str, Any]:
        github_config = state["github_config"]
        github_url = (
            f"https://github.com/{github_config.github_owner}/"
            f"{github_config.repository_name}/tree/{github_config.branch_name}"
        )
        self.e2e_service.create(
            id=self.task_id,
            title="Untitled E2E Research Task V2",
            created_by=UUID("00000000-0000-0000-0000-000000000001"),
            status=Status.RUNNING,
            current_step=StepType.GENERATE_QUERIES,
            github_url=github_url,
        )
        return {}

    @record_execution_time
    def _update_record(self, state: TopicOpenEndedResearchStateV2) -> dict[str, Any]:
        self.e2e_service.update(
            id=self.task_id,
            current_step=state.get("current_step"),
            result=to_dict_deep(state),
        )
        return {}

    @record_execution_time
    async def _upload_research_history(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, ResearchHistory]:
        logger.info("=== Upload Research History ===")
        research_history = ResearchHistory(
            **{
                k: v
                for k, v in state.items()
                if k in ResearchHistory.model_fields.keys()
            }
        )

        await (
            GithubUploadSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "research_history": research_history,
                    "commit_message": "Update research history",
                }
            )
        )

        return {"research_history": research_history}

    def _validate_github_actions_completion(
        self,
        workflow_name: str,
        status: GitHubActionsStatus | None,
        conclusion: GitHubActionsConclusion | None,
    ) -> None:
        if status is None:
            error_msg = (
                f"{workflow_name} workflow polling timed out or no status available"
            )
            logger.error(error_msg)
            raise GitHubActionsWorkflowError(
                error_msg, workflow_name=workflow_name, status=None, conclusion=None
            )

        if status == GitHubActionsStatus.COMPLETED:
            if conclusion not in {
                GitHubActionsConclusion.SUCCESS,
                GitHubActionsConclusion.NEUTRAL,
                GitHubActionsConclusion.SKIPPED,
            }:
                error_msg = (
                    f"{workflow_name} workflow failed with conclusion: {conclusion}"
                )
                logger.error(error_msg)
                raise GitHubActionsWorkflowError(
                    error_msg,
                    workflow_name=workflow_name,
                    status=str(status),
                    conclusion=str(conclusion),
                )
            logger.info(
                f"{workflow_name} workflow completed successfully with conclusion: {conclusion}"
            )
            return

        if status in {
            GitHubActionsStatus.FAILURE,
            GitHubActionsStatus.STARTUP_FAILURE,
        }:
            error_msg = (
                f"{workflow_name} workflow did not complete successfully. "
                f"Status: {status}, conclusion: {conclusion}"
            )
            logger.error(error_msg)
            raise GitHubActionsWorkflowError(
                error_msg,
                workflow_name=workflow_name,
                status=str(status),
                conclusion=str(conclusion),
            )

        error_msg = (
            f"{workflow_name} workflow ended in unexpected state. "
            f"Status: {status}, conclusion: {conclusion}"
        )
        logger.error(error_msg)
        raise GitHubActionsWorkflowError(
            error_msg,
            workflow_name=workflow_name,
            status=str(status),
            conclusion=str(conclusion),
        )

    @record_execution_time
    async def _prepare_repository(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Repository Preparation ===")
        result = (
            await PrepareRepositorySubgraph(
                github_client=self.github_client,
                is_github_repo_private=self.is_github_repo_private,
            )
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {
            "is_repository_ready": result["is_repository_ready"],
            "is_branch_ready": result["is_branch_ready"],
        }

    @record_execution_time
    async def _set_github_actions_secrets(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, bool]:
        logger.info("=== Set GitHub Actions Secrets ===")
        result = (
            await SetGithubActionsSecretsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {"secrets_set": result["secrets_set"]}

    @record_execution_time
    async def _generate_queries(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Query Generation ===")
        result = (
            await GenerateQueriesSubgraph(
                llm_client=self.langchain_client,
                num_paper_search_queries=self.num_paper_search_queries,
                llm_mapping=self.llm_mapping.generate_queries,
            )
            .build_graph()
            .ainvoke({"research_topic": state["research_topic"]})
        )
        return {
            "queries": result["queries"],
            "current_step": StepType.SEARCH_PAPER_TITLES,
        }

    @record_execution_time
    async def _search_paper_titles(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Search Paper Titles ===")
        subgraph: (
            SearchPaperTitlesFromQdrantSubgraph | SearchPaperTitlesFromAirasDbSubgraph
        )

        match self.search_method:
            case "qdrant":
                if self.qdrant_client is None:
                    raise ValueError(
                        "qdrant_client is required when search_method is 'qdrant'"
                    )
                subgraph = SearchPaperTitlesFromQdrantSubgraph(
                    litellm_client=self.litellm_client,
                    qdrant_client=self.qdrant_client,
                    collection_name=self.collection_name,
                    papers_per_query=self.papers_per_query,
                    llm_mapping=self.llm_mapping.search_paper_titles_from_qdrant,
                )
            case "airas_db":
                if self.search_index is None:
                    raise ValueError(
                        "search_index is required when search_method is 'airas_db'"
                    )
                subgraph = SearchPaperTitlesFromAirasDbSubgraph(
                    search_index=self.search_index,
                    papers_per_query=self.papers_per_query,
                )
            case _:
                raise ValueError(f"Unsupported search_method: {self.search_method}")
        result = await subgraph.build_graph().ainvoke({"queries": state["queries"]})
        return {
            "paper_titles": result["paper_titles"],
            "current_step": StepType.RETRIEVE_PAPERS,
        }

    @record_execution_time
    async def _retrieve_papers(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Paper Retrieval ===")
        result = (
            await RetrievePaperSubgraph(
                langchain_client=self.langchain_client,
                arxiv_client=self.arxiv_client,
                github_client=self.github_client,
                llm_mapping=self.llm_mapping.retrieve_paper,
            )
            .build_graph()
            .ainvoke({"paper_titles": state["paper_titles"]})
        )
        research_study_list = result["research_study_list"]
        logger.info(f"Retrieved {len(research_study_list)} papers")
        return {
            "research_study_list": research_study_list,
            "current_step": StepType.GENERATE_HYPOTHESIS,
        }

    @record_execution_time
    async def _generate_hypothesis(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Hypothesis Generation ===")
        result = (
            await GenerateHypothesisSubgraphV0(
                langchain_client=self.langchain_client,
                refinement_rounds=self.hypothesis_refinement_iterations,
                llm_mapping=self.llm_mapping.generate_hypothesis,
            )
            .build_graph()
            .ainvoke(
                {
                    "research_topic": state["research_topic"],
                    "research_study_list": state["research_study_list"],
                }
            )
        )

        return {
            "research_hypothesis": result["research_hypothesis"],
            "current_step": StepType.GENERATE_EXPERIMENTAL_DESIGN,
        }

    @record_execution_time
    async def _generate_experimental_design(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Experimental Design ===")
        result = (
            await GenerateExperimentalDesignSubgraph(
                langchain_client=self.langchain_client,
                runner_config=self.runner_config,
                num_models_to_use=self.num_experiment_models,
                llm_mapping=self.llm_mapping.generate_experimental_design,
                num_datasets_to_use=self.num_experiment_datasets,
                num_comparative_methods=self.num_comparison_methods,
            )
            .build_graph()
            .ainvoke({"research_hypothesis": state["research_hypothesis"]})
        )

        return {
            "experimental_design": result["experimental_design"],
            "current_step": StepType.GENERATE_CODE,
        }

    @record_execution_time
    async def _dispatch_code_generation(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Dispatch Code Generation ===")
        result = (
            await DispatchCodeGenerationSubgraph(
                github_client=self.github_client,
                llm_mapping=self.llm_mapping.dispatch_code_generation,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "research_topic": state["research_topic"],
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                    "wandb_config": self.wandb_config,
                    "github_actions_agent": self.github_actions_agent,
                }
            )
        )

        return {
            "code_generation_dispatched": result["dispatched"],
            "current_step": StepType.EXECUTE_TRIAL_EXPERIMENT,
        }

    @record_execution_time
    async def _poll_code_generation(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        status, conclusion, workflow_run_id = await self._poll_workflow(
            state, "Code Generation"
        )
        return {
            "code_generation_workflow_run_id": workflow_run_id,
            "code_generation_workflow_status": status,
            "code_generation_workflow_conclusion": conclusion,
        }

    @record_execution_time
    async def _fetch_run_ids(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Fetch Run IDs ===")
        try:
            result = (
                await FetchRunIdsSubgraph(github_client=self.github_client)
                .build_graph()
                .ainvoke({"github_config": state["github_config"]})
            )

            if not (run_ids := result["run_ids"]):
                error_msg = "No run IDs were fetched from the subgraph. Cannot proceed with experiments."
                logger.error(error_msg)
                raise WorkflowValidationError(error_msg)

            logger.info(f"Successfully fetched {len(run_ids)} run IDs: {run_ids}")

            return {
                "run_ids": run_ids,
                "current_run_id_index": 0,
                "retry_counts": {},
                "visualization_retry_count": 0,
            }
        except WorkflowValidationError:
            raise
        except Exception as e:
            logger.exception(f"Failed to fetch run IDs: {e}")
            raise WorkflowValidationError("Failed to fetch run IDs") from e

    @record_execution_time
    async def _dispatch_sanity_check(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        current_index = state.get("current_run_id_index", 0)

        if not (run_ids := state.get("run_ids", [])):
            error_msg = "No run IDs available for sanity check dispatch"
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        if current_index >= len(run_ids):
            logger.warning(
                f"No more run IDs to process: index={current_index}, "
                f"total_run_ids={len(run_ids)}"
            )
            return {"sanity_check_dispatched": False}

        current_run_id = run_ids[current_index]
        logger.info(
            f"=== Dispatch Sanity Check for run_id={current_run_id} "
            f"(index {current_index + 1}/{len(run_ids)}) ==="
        )

        result = (
            await DispatchSanityCheckSubgraph(
                github_client=self.github_client,
                runner_label=self.runner_config.runner_label,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "run_id": current_run_id,
                }
            )
        )

        return {"sanity_check_dispatched": result["dispatched"]}

    @record_execution_time
    async def _poll_sanity_check(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        status, conclusion, workflow_run_id = await self._poll_workflow(
            state, "Sanity Check"
        )
        return {
            "sanity_check_workflow_run_id": workflow_run_id,
            "sanity_check_workflow_status": status,
            "sanity_check_workflow_conclusion": conclusion,
        }

    @record_execution_time
    async def _dispatch_experiment_validation(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        current_index = state.get("current_run_id_index", 0)

        if not (run_ids := state.get("run_ids", [])):
            error_msg = (
                f"No run IDs available for experiment validation dispatch. "
                f"Current state: current_run_id_index={current_index}"
            )
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        if current_index >= len(run_ids):
            error_msg = (
                f"Invalid run_id index: {current_index} >= {len(run_ids)}. "
                f"Available run_ids: {run_ids}"
            )
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        current_run_id = run_ids[current_index]
        workflow_run_id = state.get("sanity_check_workflow_run_id")

        logger.info(
            f"=== Dispatch Experiment Validation for run_id={current_run_id} "
            f"(index {current_index + 1}/{len(run_ids)}) ==="
        )

        result = (
            await DispatchExperimentValidationSubgraph(
                github_client=self.github_client,
                llm_mapping=self.llm_mapping.dispatch_experiment_validation,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "research_topic": state["research_topic"],
                    "run_id": current_run_id,
                    "workflow_run_id": workflow_run_id,
                    "run_stage": "sanity",
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                    "wandb_config": self.wandb_config,
                    "github_actions_agent": self.github_actions_agent,
                }
            )
        )

        return {"experiment_validation_dispatched": result["dispatched"]}

    @record_execution_time
    async def _poll_experiment_validation(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        status, conclusion, workflow_run_id = await self._poll_workflow(
            state, "Experiment Validation"
        )
        return {
            "experiment_validation_workflow_run_id": workflow_run_id,
            "experiment_validation_workflow_status": status,
            "experiment_validation_workflow_conclusion": conclusion,
        }

    @record_execution_time
    async def _download_artifact(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, dict]:
        if (
            workflow_run_id := state.get("experiment_validation_workflow_run_id")
        ) is None:
            error_msg = "experiment_validation_workflow_run_id is missing from state"
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        logger.info(f"=== Download Artifact from workflow_run_id={workflow_run_id} ===")

        try:
            result = (
                await DownloadGithubActionsArtifactsSubgraph(
                    github_client=self.github_client
                )
                .build_graph()
                .ainvoke(
                    {
                        "github_config": state["github_config"],
                        "workflow_run_id": workflow_run_id,
                    }
                )
            )

            artifact_data = result.get("artifact_data", {})
            logger.info(
                f"Successfully downloaded artifact data with keys: {list(artifact_data.keys())}"
            )
            logger.debug(f"Artifact data details: {artifact_data}")

            return {"artifact_data": artifact_data}
        except Exception as e:
            logger.exception(
                f"Failed to download artifact from workflow_run_id={workflow_run_id}: {e}"
            )
            raise

    def _route_after_artifact_download(
        self, state: TopicOpenEndedResearchStateV2
    ) -> str:
        if not (artifact_data := state.get("artifact_data", {})):
            error_msg = "No artifact data found. Cannot determine validation action."
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        if (action := artifact_data.get("validation_action")) is None:
            error_msg = (
                f"'validation_action' field not found in artifact data. "
                f"Available fields: {list(artifact_data.keys())}"
            )
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        VALID_ACTIONS = {"retry", "proceed"}
        if action not in VALID_ACTIONS:
            error_msg = f"Invalid validation_action: '{action}', valid options are {VALID_ACTIONS}"
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        current_index = state.get("current_run_id_index", 0)
        run_ids = state.get("run_ids", [])
        current_run_id = run_ids[current_index]

        if action == "retry":
            retry_count = state.get("retry_counts", {}).get(current_run_id, 0)
            if retry_count >= self.MAX_RETRY_PER_RUN_ID:
                error_msg = (
                    f"Maximum retry count ({self.MAX_RETRY_PER_RUN_ID}) exceeded "
                    f"for run_id={current_run_id} at index {current_index}"
                )
                logger.error(error_msg)
                raise WorkflowValidationError(error_msg)

            logger.warning(
                f"Experiment validation failed for run_id={current_run_id} at index {current_index} "
                f"(retry {retry_count + 1}/{self.MAX_RETRY_PER_RUN_ID}). Retrying sanity check."
            )
            return "increment_retry_count"

        if current_index + 1 < len(run_ids):
            logger.info(
                f"Experiment validation passed for run_id at index {current_index}. "
                f"Moving to next run_id (index {current_index + 1}/{len(run_ids) - 1})"
            )
            return "increment_run_id_index"
        else:
            logger.info(
                f"All {len(run_ids)} run IDs completed successfully. "
                f"Proceeding to main experiment phase."
            )
            return "dispatch_main_experiment"

    @record_execution_time
    def _increment_run_id_index(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, int]:
        current_index = state.get("current_run_id_index", 0)
        new_index = current_index + 1
        logger.info(f"Incrementing run_id index: {current_index} -> {new_index}")
        return {"current_run_id_index": new_index}

    @record_execution_time
    def _increment_retry_count(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, dict[str, int]]:
        current_index = state.get("current_run_id_index", 0)
        run_ids = state.get("run_ids", [])
        current_run_id = run_ids[current_index]
        retry_counts = state.get("retry_counts", {})
        current_retry = retry_counts.get(current_run_id, 0)
        new_retry = current_retry + 1
        logger.info(
            f"Incrementing retry count for run_id={current_run_id}: {current_retry} -> {new_retry}"
        )
        return {"retry_counts": {**retry_counts, current_run_id: new_retry}}

    @record_execution_time
    async def _fetch_experiment_code(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, ExperimentCode]:
        logger.info("=== Fetch Experiment Code ===")
        result = (
            await FetchExperimentCodeSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {"experiment_code": result["experiment_code"]}

    @record_execution_time
    async def _create_branches_for_main_experiment(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, list[str]]:
        logger.info("=== Create Branches for Main Experiment ===")

        results = await create_branches_for_run_ids(
            github_client=self.github_client,
            github_config=state["github_config"],
            run_ids=state.get("run_ids", []),
        )

        branches = [branch_name for _, branch_name, is_success in results if is_success]

        logger.info(f"Created {len(branches)} branches: {branches}")

        return {"main_experiment_branches": branches}

    @record_execution_time
    async def _dispatch_main_experiment(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Dispatch Main Experiment ===")
        branches = state.get("main_experiment_branches", [])
        base_branch = state["github_config"].branch_name

        failed_branches = []

        for branch_name in branches:
            run_id = branch_name.replace(f"{base_branch}-", "")
            logger.info(
                f"Dispatching main experiment for branch={branch_name}, run_id={run_id}"
            )

            branch_config = GitHubConfig(
                **state["github_config"].model_dump(exclude={"branch_name"}),
                branch_name=branch_name,
            )

            result = (
                await DispatchMainExperimentSubgraph(
                    github_client=self.github_client,
                    runner_label=self.runner_config.runner_label,
                )
                .build_graph()
                .ainvoke(
                    {
                        "github_config": branch_config,
                        "run_id": run_id,
                    }
                )
            )

            if not result.get("dispatched", False):
                failed_branches.append(branch_name)
                logger.error(
                    f"Failed to dispatch main experiment for branch={branch_name}"
                )

        if failed_branches:
            error_msg = (
                f"Failed to dispatch main experiment for {len(failed_branches)}/{len(branches)} branches: "
                f"{failed_branches}"
            )
            logger.error(error_msg)
            raise WorkflowExecutionError(error_msg)

        logger.info(
            f"Successfully dispatched main experiment for all {len(branches)} branches"
        )

        return {
            "main_experiment_dispatched": True,
            "current_step": StepType.EXECUTE_FULL_EXPERIMENT,
        }

    @record_execution_time
    async def _poll_main_experiment(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Poll Main Experiment Workflow ===")

        if not (branches := state.get("main_experiment_branches", [])):
            logger.warning("No main experiment branches found, skipping poll")
            return {
                "main_experiment_workflow_status": None,
                "main_experiment_workflow_conclusion": None,
            }

        logger.info(f"Polling {len(branches)} branches in parallel: {branches}")

        async def poll_branch(
            branch: str,
        ) -> tuple[str, GitHubActionsStatus | None, GitHubActionsConclusion | None]:
            logger.info(f"Polling workflow for branch: {branch}")
            branch_config = GitHubConfig(
                **state["github_config"].model_dump(exclude={"branch_name"}),
                branch_name=branch,
            )

            result = (
                await PollGithubActionsSubgraph(github_client=self.github_client)
                .build_graph()
                .ainvoke(
                    {"github_config": branch_config},
                    {"recursion_limit": WorkflowTimeouts.STANDARD_WORKFLOW},
                )
            )

            status: GitHubActionsStatus | None = result.get("status")
            conclusion: GitHubActionsConclusion | None = result.get("conclusion")

            logger.info(f"Branch {branch}: status={status}, conclusion={conclusion}")

            return branch, status, conclusion

        results = await asyncio.gather(*[poll_branch(branch) for branch in branches])

        failed_branches = []
        successful_branches = []

        for branch, status, conclusion in results:
            if conclusion == GitHubActionsConclusion.SUCCESS:
                successful_branches.append(branch)
            else:
                failed_branches.append((branch, status, conclusion))
                logger.error(
                    f"Branch {branch} workflow failed - status: {status}, conclusion: {conclusion}"
                )

        logger.info(
            f"Main experiment results: {len(successful_branches)}/{len(branches)} branches succeeded"
        )
        if failed_branches:
            logger.error(f"Failed branches: {[b for b, _, _ in failed_branches]}")

        success_rate = len(successful_branches) / len(branches) if branches else 0
        logger.info(
            f"Main experiment success rate: {success_rate:.1%} (minimum required: {self.min_success_rate_for_parallel_experiments:.1%})"
        )

        if success_rate < self.min_success_rate_for_parallel_experiments:
            error_msg = (
                f"Main experiment success rate ({success_rate:.1%}) is below the minimum required "
                f"({self.min_success_rate_for_parallel_experiments:.1%}). "
                f"Successful: {len(successful_branches)}/{len(branches)} branches"
            )
            logger.error(error_msg)
            final_status = GitHubActionsStatus.COMPLETED
            final_conclusion = GitHubActionsConclusion.FAILURE
            self._validate_github_actions_completion(
                "Main Experiment", final_status, final_conclusion
            )
        else:
            final_status = GitHubActionsStatus.COMPLETED
            final_conclusion = GitHubActionsConclusion.SUCCESS
            logger.info(
                f"Main experiment passed with {len(successful_branches)}/{len(branches)} branches successful"
            )

        return {
            "main_experiment_workflow_status": final_status,
            "main_experiment_workflow_conclusion": final_conclusion,
        }

    @record_execution_time
    async def _dispatch_experiment_validation_for_main_experiment(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Dispatch Experiment Validation for Main Experiment ===")

        if not (branches := state.get("main_experiment_branches", [])):
            logger.warning(
                "No main experiment branches found, skipping experiment validation dispatch"
            )
            return {"main_experiment_validation_dispatched": False}

        logger.info(
            f"Dispatching experiment validation for {len(branches)} branches: {branches}"
        )

        failed_branches = []

        for branch in branches:
            run_id = branch.replace(f"{state['github_config'].branch_name}-", "")
            logger.info(
                f"Dispatching experiment validation for branch={branch}, run_id={run_id}"
            )

            branch_config = GitHubConfig(
                **state["github_config"].model_dump(exclude={"branch_name"}),
                branch_name=branch,
            )

            # Get the workflow_run_id for this branch's main experiment
            poll_result = (
                await PollGithubActionsSubgraph(github_client=self.github_client)
                .build_graph()
                .ainvoke(
                    {"github_config": branch_config},
                    {"recursion_limit": 10},  # Quick poll just to get the run_id
                )
            )
            workflow_run_id = poll_result.get("workflow_run_id")

            dispatch_result = (
                await DispatchExperimentValidationSubgraph(
                    github_client=self.github_client,
                    llm_mapping=self.llm_mapping.dispatch_experiment_validation,
                )
                .build_graph()
                .ainvoke(
                    {
                        "github_config": branch_config,
                        "research_topic": state["research_topic"],
                        "run_id": run_id,
                        "workflow_run_id": workflow_run_id,
                        "run_stage": "main",
                        "research_hypothesis": state["research_hypothesis"],
                        "experimental_design": state["experimental_design"],
                        "wandb_config": self.wandb_config,
                        "github_actions_agent": self.github_actions_agent,
                    }
                )
            )

            if not dispatch_result.get("dispatched", False):
                failed_branches.append(branch)
                logger.error(
                    f"Failed to dispatch experiment validation for branch={branch}"
                )

        if failed_branches:
            error_msg = (
                f"Failed to dispatch experiment validation for {len(failed_branches)}/{len(branches)} branches: "
                f"{failed_branches}"
            )
            logger.error(error_msg)
            raise WorkflowExecutionError(error_msg)

        logger.info(
            f"Successfully dispatched experiment validation for all {len(branches)} branches"
        )

        return {"main_experiment_validation_dispatched": True}

    @record_execution_time
    async def _poll_experiment_validation_for_main_experiment(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Poll Experiment Validation for Main Experiment ===")

        if not (branches := state.get("main_experiment_branches", [])):
            logger.warning(
                "No main experiment branches found, skipping experiment validation poll"
            )
            return {
                "main_experiment_validation_workflow_status": None,
                "main_experiment_validation_workflow_conclusion": None,
            }

        logger.info(
            f"Polling experiment validation for {len(branches)} branches in parallel: {branches}"
        )

        async def poll_branch_experiment_validation(
            branch: str,
        ) -> tuple[str, GitHubActionsStatus | None, GitHubActionsConclusion | None]:
            logger.info(f"Polling experiment validation workflow for branch: {branch}")
            branch_config = GitHubConfig(
                **state["github_config"].model_dump(exclude={"branch_name"}),
                branch_name=branch,
            )

            result = (
                await PollGithubActionsSubgraph(github_client=self.github_client)
                .build_graph()
                .ainvoke(
                    {"github_config": branch_config},
                    {"recursion_limit": WorkflowTimeouts.STANDARD_WORKFLOW},
                )
            )

            status: GitHubActionsStatus | None = result.get("status")
            conclusion: GitHubActionsConclusion | None = result.get("conclusion")

            logger.info(
                f"Branch {branch} experiment validation: status={status}, conclusion={conclusion}"
            )

            return branch, status, conclusion

        results = await asyncio.gather(
            *[poll_branch_experiment_validation(branch) for branch in branches]
        )

        failed_branches = []
        successful_branches = []

        for branch, status, conclusion in results:
            if conclusion == GitHubActionsConclusion.SUCCESS:
                successful_branches.append(branch)
            else:
                failed_branches.append((branch, status, conclusion))
                logger.error(
                    f"Branch {branch} experiment validation failed - status: {status}, conclusion: {conclusion}"
                )

        logger.info(
            f"Experiment validation results: {len(successful_branches)}/{len(branches)} branches succeeded"
        )
        if failed_branches:
            logger.error(f"Failed branches: {[b for b, _, _ in failed_branches]}")

        success_rate = len(successful_branches) / len(branches) if branches else 0
        logger.info(
            f"Main experiment validation success rate: {success_rate:.1%} (minimum required: {self.min_success_rate_for_parallel_experiments:.1%})"
        )

        if success_rate < self.min_success_rate_for_parallel_experiments:
            error_msg = (
                f"Main experiment validation success rate ({success_rate:.1%}) is below the minimum required "
                f"({self.min_success_rate_for_parallel_experiments:.1%}). "
                f"Successful: {len(successful_branches)}/{len(branches)} branches"
            )
            logger.error(error_msg)
            final_status = GitHubActionsStatus.COMPLETED
            final_conclusion = GitHubActionsConclusion.FAILURE
            self._validate_github_actions_completion(
                "Main Experiment Validation", final_status, final_conclusion
            )
        else:
            final_status = GitHubActionsStatus.COMPLETED
            final_conclusion = GitHubActionsConclusion.SUCCESS
            logger.info(
                f"Main experiment validation passed with {len(successful_branches)}/{len(branches)} branches successful"
            )

        return {
            "main_experiment_validation_workflow_status": final_status,
            "main_experiment_validation_workflow_conclusion": final_conclusion,
        }

    @record_execution_time
    async def _dispatch_visualization(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Dispatch Visualization ===")

        result = (
            await DispatchVisualizationSubgraph(
                github_client=self.github_client,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "run_ids": state.get("run_ids", []),
                }
            )
        )

        return {
            "visualization_dispatched": result["dispatched"],
            "current_step": StepType.EXECUTE_EVALUATION_WORKFLOW,
        }

    @record_execution_time
    async def _poll_visualization(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        status, conclusion, workflow_run_id = await self._poll_workflow(
            state, "Visualization"
        )
        return {
            "visualization_workflow_run_id": workflow_run_id,
            "visualization_workflow_status": status,
            "visualization_workflow_conclusion": conclusion,
        }

    @record_execution_time
    async def _dispatch_experiment_validation_for_visualization(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Dispatch Experiment Validation for Visualization ===")

        workflow_run_id = state.get("visualization_workflow_run_id")

        logger.info(
            "Dispatching experiment validation for visualization (no specific run_id)"
        )

        result = (
            await DispatchExperimentValidationSubgraph(
                github_client=self.github_client,
                llm_mapping=self.llm_mapping.dispatch_experiment_validation,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "research_topic": state["research_topic"],
                    "workflow_run_id": workflow_run_id,
                    "run_stage": "visualization",
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                    "wandb_config": self.wandb_config,
                    "github_actions_agent": self.github_actions_agent,
                }
            )
        )

        return {"visualization_validation_dispatched": result["dispatched"]}

    @record_execution_time
    async def _poll_experiment_validation_for_visualization(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        status, conclusion, workflow_run_id = await self._poll_workflow(
            state, "Experiment Validation for Visualization"
        )
        return {
            "visualization_validation_workflow_run_id": workflow_run_id,
            "visualization_validation_workflow_status": status,
            "visualization_validation_workflow_conclusion": conclusion,
        }

    @record_execution_time
    async def _download_artifact_for_visualization(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, dict]:
        if (
            workflow_run_id := state.get("visualization_validation_workflow_run_id")
        ) is None:
            error_msg = "visualization_validation_workflow_run_id is missing from state"
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        logger.info(
            f"=== Download Artifact for Visualization from workflow_run_id={workflow_run_id} ==="
        )

        try:
            result = (
                await DownloadGithubActionsArtifactsSubgraph(
                    github_client=self.github_client
                )
                .build_graph()
                .ainvoke(
                    {
                        "github_config": state["github_config"],
                        "workflow_run_id": workflow_run_id,
                    }
                )
            )

            artifact_data = result.get("artifact_data", {})
            logger.info(
                f"Successfully downloaded artifact data with keys: {list(artifact_data.keys())}"
            )
            logger.debug(f"Artifact data details: {artifact_data}")

            return {"artifact_data": artifact_data}
        except Exception as e:
            logger.exception(
                f"Failed to download artifact from workflow_run_id={workflow_run_id}: {e}"
            )
            raise

    def _route_after_visualization_artifact_download(
        self, state: TopicOpenEndedResearchStateV2
    ) -> str:
        if not (artifact_data := state.get("artifact_data", {})):
            error_msg = "No artifact data found for visualization. Cannot determine validation action."
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        if (action := artifact_data.get("validation_action")) is None:
            error_msg = (
                f"'validation_action' field not found in visualization artifact data. "
                f"Available fields: {list(artifact_data.keys())}"
            )
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        VALID_ACTIONS = {"retry", "proceed"}
        if action not in VALID_ACTIONS:
            error_msg = f"Invalid validation_action: '{action}', valid options are {VALID_ACTIONS}"
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        if action == "retry":
            retry_count = state.get("visualization_retry_count", 0)
            if retry_count >= self.MAX_RETRY_FOR_VISUALIZATION:
                error_msg = (
                    f"Maximum retry count ({self.MAX_RETRY_FOR_VISUALIZATION}) exceeded "
                    f"for visualization validation"
                )
                logger.error(error_msg)
                raise WorkflowValidationError(error_msg)

            logger.warning(
                f"Visualization validation failed (retry {retry_count + 1}/{self.MAX_RETRY_FOR_VISUALIZATION}). "
                f"Retrying visualization."
            )
            return "increment_visualization_retry_count"

        logger.info(
            "Visualization validation passed. Proceeding to fetch experiment results."
        )
        return "fetch_experiment_results"

    @record_execution_time
    def _increment_visualization_retry_count(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, int]:
        retry_count = state.get("visualization_retry_count", 0)
        new_retry = retry_count + 1
        logger.info(
            f"Incrementing visualization retry count: {retry_count} -> {new_retry}"
        )
        return {"visualization_retry_count": new_retry}

    @record_execution_time
    async def _fetch_experiment_results(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Fetch Experiment Results ===")
        result = (
            await FetchExperimentResultsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {
            "experimental_results": result["experiment_results"],
            "current_step": StepType.ANALYZE_EXPERIMENT_RESULTS,
        }

    @record_execution_time
    async def _analyze_experiment(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Experiment Analysis ===")
        result = (
            await AnalyzeExperimentSubgraph(
                langchain_client=self.langchain_client,
                llm_mapping=self.llm_mapping.analyze_experiment,
            )
            .build_graph()
            .ainvoke(
                {
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                    "experiment_code": state["experiment_code"],
                    "experimental_results": state["experimental_results"],
                }
            )
        )

        return {
            "experimental_analysis": result["experimental_analysis"],
            "current_step": StepType.GENERATE_BIBFILE,
        }

    @record_execution_time
    async def _generate_bibfile(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Reference Generation ===")
        result = (
            await GenerateBibfileSubgraph()
            .build_graph()
            .ainvoke({"research_study_list": state["research_study_list"]})
        )

        return {
            "references_bib": result["references_bib"],
            "current_step": StepType.GENERATE_PAPER,
        }

    @record_execution_time
    async def _push_bibfile(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, bool]:
        logger.info("=== Push Bibfile to GitHub ===")
        bibfile_path = f".research/latex/{self.latex_template_name}/references.bib"

        result = (
            await PushGitHubSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "files": {bibfile_path: state["references_bib"]},
                    "commit_message": "Add references.bib",
                }
            )
        )

        return {"is_upload_successful": result["is_upload_successful"]}

    @record_execution_time
    async def _generate_paper(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Paper Writing ===")
        result = (
            await WriteSubgraph(
                langchain_client=self.langchain_client,
                paper_content_refinement_iterations=self.paper_content_refinement_iterations,
                llm_mapping=self.llm_mapping.write,
            )
            .build_graph()
            .ainvoke(
                {
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                    "experiment_code": state["experiment_code"],
                    "experimental_results": state["experimental_results"],
                    "experimental_analysis": state["experimental_analysis"],
                    "research_study_list": state["research_study_list"],
                    "references_bib": state["references_bib"],
                }
            )
        )

        return {
            "paper_content": result["paper_content"],
            "current_step": StepType.GENERATE_LATEX,
        }

    @record_execution_time
    async def _generate_latex(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== LaTeX Generation ===")
        result = (
            await GenerateLatexSubgraph(
                langchain_client=self.langchain_client,
                github_client=self.github_client,
                latex_template_name=self.latex_template_name,
                llm_mapping=self.llm_mapping.generate_latex,
            )
            .build_graph()
            .ainvoke(
                {
                    "references_bib": state["references_bib"],
                    "paper_content": state["paper_content"],
                }
            )
        )

        return {
            "latex_text": result["latex_text"],
            "current_step": StepType.COMPILE_LATEX,
        }

    @record_execution_time
    async def _push_latex(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, bool]:
        logger.info("=== Push LaTeX to GitHub ===")
        result = (
            await PushLatexSubgraph(
                github_client=self.github_client,
                latex_template_name=self.latex_template_name,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "latex_text": state["latex_text"],
                }
            )
        )

        return {"is_upload_successful": result["is_upload_successful"]}

    @record_execution_time
    async def _compile_latex(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, Any]:
        logger.info("=== Compile LaTeX ===")
        result = (
            await CompileLatexSubgraph(
                github_client=self.github_client,
                latex_template_name=self.latex_template_name,
                github_actions_agent=self.github_actions_agent,
                llm_mapping=self.llm_mapping.compile_latex,
            )
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {
            "compile_latex_dispatched": result["compile_latex_dispatched"],
            "paper_url": result.get("paper_url"),
            "current_step": StepType.DONE,
        }

    @record_execution_time
    async def _poll_compile_latex_workflow(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, GitHubActionsStatus | GitHubActionsConclusion | None]:
        status, conclusion, _ = await self._poll_workflow(
            state, "Compile LaTeX", recursion_limit=WorkflowTimeouts.LATEX_COMPILATION
        )
        return {
            "compile_latex_workflow_status": status,
            "compile_latex_workflow_conclusion": conclusion,
        }

    @record_execution_time
    async def _finalize(
        self, state: TopicOpenEndedResearchStateV2
    ) -> dict[str, str | ResearchHistory | None]:
        logger.info("=== Workflow Completed ===")
        logger.info(
            f"Repository: {state['github_config'].github_owner}/{state['github_config'].repository_name}"
        )
        logger.info(f"Branch: {state['github_config'].branch_name}")
        if paper_url := state.get("paper_url"):
            logger.info(f"Paper URL: {paper_url}")

        self.e2e_service.update(
            id=self.task_id,
            status=Status.COMPLETED,
            current_step=StepType.DONE,
            result=to_dict_deep(state),
        )
        return {
            "status": "completed",
            "research_history": state.get("research_history"),
        }

    def build_graph(self):
        graph_builder = StateGraph(
            TopicOpenEndedResearchStateV2,
            input_schema=TopicOpenEndedResearchInputStateV2,
            output_schema=TopicOpenEndedResearchOutputStateV2,
        )

        graph_builder.add_node("create_record", self._create_record)
        graph_builder.add_node("prepare_repository", self._prepare_repository)
        graph_builder.add_node(
            "set_github_actions_secrets", self._set_github_actions_secrets
        )
        graph_builder.add_node("generate_queries", self._generate_queries)
        graph_builder.add_node("search_paper_titles", self._search_paper_titles)
        graph_builder.add_node("retrieve_papers", self._retrieve_papers)
        graph_builder.add_node("generate_hypothesis", self._generate_hypothesis)
        graph_builder.add_node(
            "generate_experimental_design", self._generate_experimental_design
        )
        graph_builder.add_node(
            "dispatch_code_generation", self._dispatch_code_generation
        )
        graph_builder.add_node("poll_code_generation", self._poll_code_generation)
        graph_builder.add_node("fetch_run_ids", self._fetch_run_ids)
        graph_builder.add_node("dispatch_sanity_check", self._dispatch_sanity_check)
        graph_builder.add_node("poll_sanity_check", self._poll_sanity_check)
        graph_builder.add_node(
            "dispatch_experiment_validation", self._dispatch_experiment_validation
        )
        graph_builder.add_node(
            "poll_experiment_validation", self._poll_experiment_validation
        )
        graph_builder.add_node("download_artifact", self._download_artifact)
        graph_builder.add_node("increment_run_id_index", self._increment_run_id_index)
        graph_builder.add_node("increment_retry_count", self._increment_retry_count)
        graph_builder.add_node("fetch_experiment_code", self._fetch_experiment_code)
        graph_builder.add_node(
            "create_branches_for_main_experiment",
            self._create_branches_for_main_experiment,
        )
        graph_builder.add_node(
            "dispatch_main_experiment", self._dispatch_main_experiment
        )
        graph_builder.add_node("poll_main_experiment", self._poll_main_experiment)
        graph_builder.add_node(
            "dispatch_experiment_validation_for_main_experiment",
            self._dispatch_experiment_validation_for_main_experiment,
        )
        graph_builder.add_node(
            "poll_experiment_validation_for_main_experiment",
            self._poll_experiment_validation_for_main_experiment,
        )
        graph_builder.add_node("dispatch_visualization", self._dispatch_visualization)
        graph_builder.add_node("poll_visualization", self._poll_visualization)
        graph_builder.add_node(
            "dispatch_experiment_validation_for_visualization",
            self._dispatch_experiment_validation_for_visualization,
        )
        graph_builder.add_node(
            "poll_experiment_validation_for_visualization",
            self._poll_experiment_validation_for_visualization,
        )
        graph_builder.add_node(
            "download_artifact_for_visualization",
            self._download_artifact_for_visualization,
        )
        graph_builder.add_node(
            "increment_visualization_retry_count",
            self._increment_visualization_retry_count,
        )
        graph_builder.add_node(
            "fetch_experiment_results", self._fetch_experiment_results
        )
        graph_builder.add_node("analyze_experiment", self._analyze_experiment)
        graph_builder.add_node("generate_bibfile", self._generate_bibfile)
        graph_builder.add_node("push_bibfile", self._push_bibfile)
        graph_builder.add_node("generate_paper", self._generate_paper)
        graph_builder.add_node("generate_latex", self._generate_latex)
        graph_builder.add_node("push_latex", self._push_latex)
        graph_builder.add_node("compile_latex", self._compile_latex)
        graph_builder.add_node(
            "poll_compile_latex_workflow", self._poll_compile_latex_workflow
        )
        graph_builder.add_node("finalize", self._finalize)

        UPLOAD_AFTER = {
            "generate_queries",
            "search_paper_titles",
            "retrieve_papers",
            "generate_hypothesis",
            "generate_experimental_design",
            "poll_code_generation",
            "fetch_run_ids",
            "fetch_experiment_code",
            "poll_main_experiment",
            "poll_visualization",
            "fetch_experiment_results",
            "analyze_experiment",
            "generate_bibfile",
            "generate_paper",
            "generate_latex",
            "poll_compile_latex_workflow",
        }

        for node in UPLOAD_AFTER:
            github_upload_node = f"github_upload_after_{node}"
            graph_builder.add_node(github_upload_node, self._upload_research_history)
            db_update_node = f"db_update_after_{node}"
            graph_builder.add_node(db_update_node, self._update_record)

        graph_builder.add_edge(START, "create_record")
        graph_builder.add_edge("create_record", "prepare_repository")
        graph_builder.add_edge("prepare_repository", "set_github_actions_secrets")
        graph_builder.add_edge("set_github_actions_secrets", "generate_queries")

        self._add_edge_with_upload(
            graph_builder, "generate_queries", "search_paper_titles", UPLOAD_AFTER
        )
        self._add_edge_with_upload(
            graph_builder, "search_paper_titles", "retrieve_papers", UPLOAD_AFTER
        )
        self._add_edge_with_upload(
            graph_builder, "retrieve_papers", "generate_hypothesis", UPLOAD_AFTER
        )
        self._add_edge_with_upload(
            graph_builder,
            "generate_hypothesis",
            "generate_experimental_design",
            UPLOAD_AFTER,
        )
        self._add_edge_with_upload(
            graph_builder,
            "generate_experimental_design",
            "dispatch_code_generation",
            UPLOAD_AFTER,
        )

        graph_builder.add_edge("dispatch_code_generation", "poll_code_generation")
        self._add_edge_with_upload(
            graph_builder, "poll_code_generation", "fetch_run_ids", UPLOAD_AFTER
        )
        self._add_edge_with_upload(
            graph_builder, "fetch_run_ids", "dispatch_sanity_check", UPLOAD_AFTER
        )

        # Sanity check loop
        graph_builder.add_edge("dispatch_sanity_check", "poll_sanity_check")
        graph_builder.add_edge("poll_sanity_check", "dispatch_experiment_validation")
        graph_builder.add_edge(
            "dispatch_experiment_validation", "poll_experiment_validation"
        )
        graph_builder.add_edge("poll_experiment_validation", "download_artifact")

        # Conditional routing after artifact download
        graph_builder.add_conditional_edges(
            "download_artifact",
            self._route_after_artifact_download,
            {
                "increment_retry_count": "increment_retry_count",
                "increment_run_id_index": "increment_run_id_index",
                "dispatch_main_experiment": "fetch_experiment_code",
            },
        )

        # Loop back to sanity check for retry or next run_id
        graph_builder.add_edge("increment_retry_count", "dispatch_sanity_check")
        graph_builder.add_edge("increment_run_id_index", "dispatch_sanity_check")

        # Main experiment flow
        self._add_edge_with_upload(
            graph_builder,
            "fetch_experiment_code",
            "create_branches_for_main_experiment",
            UPLOAD_AFTER,
        )
        graph_builder.add_edge(
            "create_branches_for_main_experiment", "dispatch_main_experiment"
        )
        graph_builder.add_edge("dispatch_main_experiment", "poll_main_experiment")
        self._add_edge_with_upload(
            graph_builder,
            "poll_main_experiment",
            "dispatch_experiment_validation_for_main_experiment",
            UPLOAD_AFTER,
        )
        graph_builder.add_edge(
            "dispatch_experiment_validation_for_main_experiment",
            "poll_experiment_validation_for_main_experiment",
        )
        graph_builder.add_edge(
            "poll_experiment_validation_for_main_experiment", "dispatch_visualization"
        )

        # Visualization with validation loop
        graph_builder.add_edge("dispatch_visualization", "poll_visualization")
        self._add_edge_with_upload(
            graph_builder,
            "poll_visualization",
            "dispatch_experiment_validation_for_visualization",
            UPLOAD_AFTER,
        )
        graph_builder.add_edge(
            "dispatch_experiment_validation_for_visualization",
            "poll_experiment_validation_for_visualization",
        )
        graph_builder.add_edge(
            "poll_experiment_validation_for_visualization",
            "download_artifact_for_visualization",
        )

        # Conditional routing after visualization artifact download
        graph_builder.add_conditional_edges(
            "download_artifact_for_visualization",
            self._route_after_visualization_artifact_download,
            {
                "increment_visualization_retry_count": "increment_visualization_retry_count",
                "fetch_experiment_results": "fetch_experiment_results",
            },
        )

        # Loop back to visualization for retry
        graph_builder.add_edge(
            "increment_visualization_retry_count", "dispatch_visualization"
        )

        self._add_edge_with_upload(
            graph_builder,
            "fetch_experiment_results",
            "analyze_experiment",
            UPLOAD_AFTER,
        )
        self._add_edge_with_upload(
            graph_builder, "analyze_experiment", "generate_bibfile", UPLOAD_AFTER
        )
        self._add_edge_with_upload(
            graph_builder, "generate_bibfile", "push_bibfile", UPLOAD_AFTER
        )

        graph_builder.add_edge("push_bibfile", "generate_paper")
        self._add_edge_with_upload(
            graph_builder, "generate_paper", "generate_latex", UPLOAD_AFTER
        )
        self._add_edge_with_upload(
            graph_builder, "generate_latex", "push_latex", UPLOAD_AFTER
        )

        graph_builder.add_edge("push_latex", "compile_latex")
        graph_builder.add_edge("compile_latex", "poll_compile_latex_workflow")
        self._add_edge_with_upload(
            graph_builder, "poll_compile_latex_workflow", "finalize", UPLOAD_AFTER
        )

        graph_builder.add_edge("finalize", END)

        return graph_builder.compile()

    def _add_edge_with_upload(
        self,
        graph_builder: StateGraph,
        source: str,
        target: str,
        upload_after: set[str],
    ):
        if source in upload_after:
            github_upload_node = f"github_upload_after_{source}"
            db_update_node = f"db_update_after_{source}"
            graph_builder.add_edge(source, github_upload_node)
            graph_builder.add_edge(source, db_update_node)
            graph_builder.add_edge([github_upload_node, db_update_node], target)
        else:
            graph_builder.add_edge(source, target)
