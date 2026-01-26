import asyncio
import logging
from typing import Any
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel, ValidationError
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experimental_analysis import ExperimentalAnalysis
from airas.core.types.experimental_design import ExperimentalDesign, RunnerConfig
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.github import (
    GitHubActionsConclusion,
    GitHubActionsStatus,
    GitHubConfig,
)
from airas.core.types.paper import PaperContent
from airas.core.types.research_history import ResearchHistory
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.core.types.wandb import WandbConfig
from airas.core.utils import to_dict_deep
from airas.infra.arxiv_client import ArxivClient
from airas.infra.db.models.e2e import Status, StepType
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.usecases.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentLLMMapping,
    AnalyzeExperimentSubgraph,
)
from airas.usecases.autonomous_research.topic_open_ended_research.topic_open_ended_research_service import (
    TopicOpenEndedResearchService,
)
from airas.usecases.executors.execute_evaluation_subgraph.execute_evaluation_subgraph import (
    ExecuteEvaluationLLMMapping,
    ExecuteEvaluationSubgraph,
)
from airas.usecases.executors.execute_full_experiment_subgraph.execute_full_experiment_subgraph import (
    ExecuteFullExperimentLLMMapping,
    ExecuteFullExperimentSubgraph,
)
from airas.usecases.executors.execute_trial_experiment_subgraph.execute_trial_experiment_subgraph import (
    ExecuteTrialExperimentLLMMapping,
    ExecuteTrialExperimentSubgraph,
)
from airas.usecases.executors.fetch_experiment_results_subgraph.fetch_experiment_results_subgraph import (
    FetchExperimentResultsSubgraph,
)
from airas.usecases.generators.generate_code_subgraph.generate_code_subgraph import (
    GenerateCodeLLMMapping,
    GenerateCodeSubgraph,
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
from airas.usecases.github.github_upload_subgraph import GithubUploadSubgraph
from airas.usecases.github.poll_github_actions_subgraph.poll_github_actions_subgraph import (
    PollGithubActionsSubgraph,
)
from airas.usecases.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)
from airas.usecases.github.push_code_subgraph.push_code_subgraph import (
    PushCodeSubgraph,
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
from airas.usecases.writers.generate_bibfile_subgraph.generate_bibfile_subgraph import (
    GenerateBibfileSubgraph,
)
from airas.usecases.writers.write_subgraph.write_subgraph import (
    WriteLLMMapping,
    WriteSubgraph,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("execute_e2e")(f)  # noqa: E731


class TopicOpenEndedResearchSubgraphLLMMapping(BaseModel):
    generate_queries: GenerateQueriesLLMMapping | None = None
    retrieve_paper: RetrievePaperSubgraphLLMMapping | None = None
    generate_hypothesis: GenerateHypothesisSubgraphV0LLMMapping | None = None
    generate_experimental_design: GenerateExperimentalDesignLLMMapping | None = None
    generate_code: GenerateCodeLLMMapping | None = None
    execute_trial_experiment: ExecuteTrialExperimentLLMMapping | None = None
    execute_full_experiment: ExecuteFullExperimentLLMMapping | None = None
    execute_evaluation: ExecuteEvaluationLLMMapping | None = None
    analyze_experiment: AnalyzeExperimentLLMMapping | None = None
    write: WriteLLMMapping | None = None
    generate_latex: GenerateLatexLLMMapping | None = None
    compile_latex: CompileLatexLLMMapping | None = None


class TopicOpenEndedResearchInputState(TypedDict):
    task_id: str | UUID
    github_config: GitHubConfig
    research_topic: str


class TopicOpenEndedResearchOutputState(ExecutionTimeState):
    status: str
    research_history: ResearchHistory | None


class TopicOpenEndedResearchState(
    TopicOpenEndedResearchInputState,
    TopicOpenEndedResearchOutputState,
    total=False,
):
    current_step: StepType  # NOTE: the database status is updated to reflect progress
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
    code_pushed: bool
    is_upload_successful: bool
    # Experiment execution states
    trial_dispatched: bool
    trial_run_ids: list[str]
    trial_workflow_status: GitHubActionsStatus | None
    trial_workflow_conclusion: GitHubActionsConclusion | None
    full_dispatched: bool
    full_experiment_branches: list[str]
    full_workflow_status: GitHubActionsStatus | None
    full_workflow_conclusion: GitHubActionsConclusion | None
    evaluation_dispatched: bool
    evaluation_workflow_status: GitHubActionsStatus | None
    evaluation_workflow_conclusion: GitHubActionsConclusion | None
    compile_latex_dispatched: bool
    compile_latex_workflow_status: GitHubActionsStatus | None
    compile_latex_workflow_conclusion: GitHubActionsConclusion | None


class TopicOpenEndedResearchSubgraph:
    def __init__(
        self,
        search_index: AirasDbPaperSearchIndex,
        github_client: GithubClient,
        arxiv_client: ArxivClient,
        langchain_client: LangChainClient,
        e2e_service: TopicOpenEndedResearchService,
        runner_config: RunnerConfig,
        wandb_config: WandbConfig,
        task_id: UUID,
        is_github_repo_private: bool = False,
        num_paper_search_queries: int = 2,
        papers_per_query: int = 5,
        hypothesis_refinement_iterations: int = 1,
        num_experiment_models: int = 1,
        num_experiment_datasets: int = 1,
        num_comparison_methods: int = 0,
        experiment_code_validation_iterations: int = 3,
        paper_content_refinement_iterations: int = 2,
        latex_template_name: str = "iclr2024",
        llm_mapping: TopicOpenEndedResearchSubgraphLLMMapping | None = None,
    ):
        self.search_index = search_index
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
        self.experiment_code_validation_iterations = (
            experiment_code_validation_iterations
        )
        self.paper_content_refinement_iterations = paper_content_refinement_iterations
        self.latex_template_name = latex_template_name
        self.llm_mapping = llm_mapping or TopicOpenEndedResearchSubgraphLLMMapping()

    @record_execution_time
    def _create_record(self, state: TopicOpenEndedResearchState) -> dict[str, Any]:
        github_config = state["github_config"]
        github_url = (
            f"https://github.com/{github_config.github_owner}/"
            f"{github_config.repository_name}/tree/{github_config.branch_name}"
        )
        self.e2e_service.create(
            id=self.task_id,
            title="Untitled E2E Research Task",
            created_by=UUID("00000000-0000-0000-0000-000000000001"),
            status=Status.RUNNING,
            current_step=StepType.GENERATE_QUERIES,
            github_url=github_url,
        )
        return {}

    @record_execution_time
    def _update_record(self, state: TopicOpenEndedResearchState) -> dict[str, Any]:
        self.e2e_service.update(
            id=self.task_id,
            current_step=state.get("current_step"),
            result=to_dict_deep(state),
        )
        return {}

    @record_execution_time
    async def _upload_research_history(
        self, state: TopicOpenEndedResearchState
    ) -> dict[str, ResearchHistory]:
        logger.info("=== Upload Research History ===")
        try:
            research_history = ResearchHistory(
                **{
                    k: v
                    for k, v in state.items()
                    if k in ResearchHistory.model_fields.keys()
                }
            )
        except ValidationError as e:
            logger.error(f"Failed to construct ResearchHistory: {e}")
            raise

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
            raise ValueError(
                f"{workflow_name} workflow polling timed out or no status available"
            )

        if status == GitHubActionsStatus.COMPLETED:
            if conclusion not in {
                GitHubActionsConclusion.SUCCESS,
                GitHubActionsConclusion.NEUTRAL,
                GitHubActionsConclusion.SKIPPED,
            }:
                raise ValueError(
                    f"{workflow_name} workflow failed with conclusion: {conclusion}"
                )
            return

        if status in {
            GitHubActionsStatus.FAILURE,
            GitHubActionsStatus.STARTUP_FAILURE,
        }:
            raise ValueError(
                f"{workflow_name} workflow did not complete successfully. "
                f"Status: {status}, conclusion: {conclusion}"
            )

        raise ValueError(
            f"{workflow_name} workflow ended in unexpected state. "
            f"Status: {status}, conclusion: {conclusion}"
        )

    @record_execution_time
    async def _prepare_repository(
        self, state: TopicOpenEndedResearchState
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
    async def _generate_queries(
        self, state: TopicOpenEndedResearchState
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
        self, state: TopicOpenEndedResearchState
    ) -> dict[str, Any]:
        logger.info("=== Search Paper Titles ===")
        result = (
            await SearchPaperTitlesFromAirasDbSubgraph(
                search_index=self.search_index,
                papers_per_query=self.papers_per_query,
            )
            .build_graph()
            .ainvoke({"queries": state["queries"]})
        )
        return {
            "paper_titles": result["paper_titles"],
            "current_step": StepType.RETRIEVE_PAPERS,
        }

    @record_execution_time
    async def _retrieve_papers(
        self, state: TopicOpenEndedResearchState
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
        self, state: TopicOpenEndedResearchState
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
        self, state: TopicOpenEndedResearchState
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
    async def _generate_code(
        self, state: TopicOpenEndedResearchState
    ) -> dict[str, Any]:
        logger.info("=== Code Generation ===")
        result = (
            await GenerateCodeSubgraph(
                langchain_client=self.langchain_client,
                wandb_config=self.wandb_config,
                max_code_validations=self.experiment_code_validation_iterations,
                llm_mapping=self.llm_mapping.generate_code,
            )
            .build_graph()
            .ainvoke(
                {
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                }
            )
        )

        return {
            "experiment_code": result["experiment_code"],
            "current_step": StepType.PUSH_CODE,
        }

    @record_execution_time
    async def _push_code(self, state: TopicOpenEndedResearchState) -> dict[str, Any]:
        logger.info("=== Push Code to GitHub ===")
        result = (
            await PushCodeSubgraph(
                github_client=self.github_client,
                secret_names=None,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "experiment_code": state["experiment_code"],
                }
            )
        )

        return {
            "code_pushed": result["code_pushed"],
            "current_step": StepType.EXECUTE_TRIAL_EXPERIMENT,
        }

    @record_execution_time
    async def _execute_trial_experiment(
        self, state: TopicOpenEndedResearchState
    ) -> dict[str, Any]:
        logger.info("=== Execute Trial Experiment ===")
        result = (
            await ExecuteTrialExperimentSubgraph(
                github_client=self.github_client,
                runner_label=self.runner_config.runner_label,
                llm_mapping=self.llm_mapping.execute_trial_experiment,
            )
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {
            "trial_dispatched": result["dispatched"],
            "trial_run_ids": result.get("run_ids", []),
            "current_step": StepType.EXECUTE_FULL_EXPERIMENT,
        }

    @record_execution_time
    async def _poll_trial_workflow(
        self, state: TopicOpenEndedResearchState
    ) -> dict[str, GitHubActionsStatus | GitHubActionsConclusion | None]:
        logger.info("=== Poll Trial Workflow ===")
        result = (
            await PollGithubActionsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {"github_config": state["github_config"]}, {"recursion_limit": 300}
            )
        )

        status = result.get("status")
        conclusion = result.get("conclusion")
        self._validate_github_actions_completion("Trial", status, conclusion)

        return {
            "trial_workflow_status": status,
            "trial_workflow_conclusion": conclusion,
        }

    @record_execution_time
    async def _execute_full_experiment(
        self, state: TopicOpenEndedResearchState
    ) -> dict[str, Any]:
        logger.info("=== Execute Full Experiment ===")
        result = (
            await ExecuteFullExperimentSubgraph(
                github_client=self.github_client,
                runner_label=self.runner_config.runner_label,
                llm_mapping=self.llm_mapping.execute_full_experiment,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "run_ids": state.get("trial_run_ids", []),
                }
            )
        )

        branches = [
            branch_name
            for _, branch_name, success in result.get("branch_creation_results", [])
            if success
        ]

        return {
            "full_dispatched": result["all_dispatched"],
            "full_experiment_branches": branches,
            "current_step": StepType.EXECUTE_EVALUATION_WORKFLOW,
        }

    @record_execution_time
    async def _poll_full_workflow(
        self, state: TopicOpenEndedResearchState
    ) -> dict[str, GitHubActionsStatus | GitHubActionsConclusion | None]:
        logger.info("=== Poll Full Workflow ===")

        if not (branches := state.get("full_experiment_branches", [])):
            logger.warning("No full experiment branches found, skipping poll")
            return {
                "full_workflow_status": None,
                "full_workflow_conclusion": None,
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
                .ainvoke({"github_config": branch_config}, {"recursion_limit": 3600})
            )

            status: GitHubActionsStatus | None = result.get("status")
            conclusion: GitHubActionsConclusion | None = result.get("conclusion")

            logger.info(f"Branch {branch}: status={status}, conclusion={conclusion}")

            return branch, status, conclusion

        results = await asyncio.gather(*[poll_branch(branch) for branch in branches])

        all_success = all(
            conclusion == GitHubActionsConclusion.SUCCESS
            for _, _, conclusion in results
        )
        for branch, _, conclusion in results:
            if conclusion != GitHubActionsConclusion.SUCCESS:
                logger.warning(
                    f"Branch {branch} workflow failed with conclusion: {conclusion}"
                )

        final_status = GitHubActionsStatus.COMPLETED
        final_conclusion = (
            GitHubActionsConclusion.SUCCESS
            if all_success
            else GitHubActionsConclusion.FAILURE
        )

        self._validate_github_actions_completion("Full", final_status, final_conclusion)

        return {
            "full_workflow_status": final_status,
            "full_workflow_conclusion": final_conclusion,
        }

    @record_execution_time
    async def _execute_evaluation_workflow(
        self, state: TopicOpenEndedResearchState
    ) -> dict[str, Any]:
        logger.info("=== Execute Evaluation ===")
        result = (
            await ExecuteEvaluationSubgraph(
                github_client=self.github_client,
                llm_mapping=self.llm_mapping.execute_evaluation,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "wandb_config": self.wandb_config,
                }
            )
        )

        return {
            "evaluation_dispatched": result.get("dispatched", False),
            "current_step": StepType.FETCH_EXPERIMENT_RESULTS,
        }

    @record_execution_time
    async def _poll_evaluation(
        self, state: TopicOpenEndedResearchState
    ) -> dict[str, GitHubActionsStatus | GitHubActionsConclusion | None]:
        logger.info("=== Poll Evaluation Workflow ===")
        result = (
            await PollGithubActionsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {"github_config": state["github_config"]}, {"recursion_limit": 300}
            )
        )

        status = result.get("status")
        conclusion = result.get("conclusion")
        self._validate_github_actions_completion("Evaluation", status, conclusion)

        return {
            "evaluation_workflow_status": status,
            "evaluation_workflow_conclusion": conclusion,
        }

    @record_execution_time
    async def _fetch_experiment_results(
        self, state: TopicOpenEndedResearchState
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
        self, state: TopicOpenEndedResearchState
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
        self, state: TopicOpenEndedResearchState
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
    async def _generate_paper(
        self, state: TopicOpenEndedResearchState
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
        self, state: TopicOpenEndedResearchState
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
    async def _push_latex(self, state: TopicOpenEndedResearchState) -> dict[str, bool]:
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
        self, state: TopicOpenEndedResearchState
    ) -> dict[str, Any]:
        logger.info("=== Compile LaTeX ===")
        result = (
            await CompileLatexSubgraph(
                github_client=self.github_client,
                latex_template_name=state.get("latex_template_name", "iclr2024"),
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
        self, state: TopicOpenEndedResearchState
    ) -> dict[str, GitHubActionsStatus | GitHubActionsConclusion | None]:
        logger.info("=== Poll Compile LaTeX Workflow ===")
        result = (
            await PollGithubActionsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {"github_config": state["github_config"]}, {"recursion_limit": 300}
            )
        )

        status = result.get("status")
        conclusion = result.get("conclusion")
        self._validate_github_actions_completion("Compile LaTeX", status, conclusion)

        return {
            "compile_latex_workflow_status": status,
            "compile_latex_workflow_conclusion": conclusion,
        }

    @record_execution_time
    async def _finalize(
        self, state: TopicOpenEndedResearchState
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
        PIPELINE = [
            ("create_record", self._create_record),
            ("prepare_repository", self._prepare_repository),
            ("generate_queries", self._generate_queries),
            ("search_paper_titles", self._search_paper_titles),
            ("retrieve_papers", self._retrieve_papers),
            ("generate_hypothesis", self._generate_hypothesis),
            ("generate_experimental_design", self._generate_experimental_design),
            ("generate_code", self._generate_code),
            ("push_code", self._push_code),
            ("execute_trial_experiment", self._execute_trial_experiment),
            ("poll_trial_workflow", self._poll_trial_workflow),
            ("execute_full_experiment", self._execute_full_experiment),
            ("poll_full_workflow", self._poll_full_workflow),
            ("execute_evaluation_workflow", self._execute_evaluation_workflow),
            ("poll_evaluation", self._poll_evaluation),
            ("fetch_experiment_results", self._fetch_experiment_results),
            ("analyze_experiment", self._analyze_experiment),
            ("generate_bibfile", self._generate_bibfile),
            ("generate_paper", self._generate_paper),
            ("generate_latex", self._generate_latex),
            ("push_latex", self._push_latex),
            ("compile_latex", self._compile_latex),
            ("poll_compile_latex_workflow", self._poll_compile_latex_workflow),
            ("finalize", self._finalize),
        ]

        UPLOAD_AFTER = {
            "generate_queries",
            "search_paper_titles",
            "retrieve_papers",
            "generate_hypothesis",
            "generate_experimental_design",
            "generate_code",
            "poll_trial_workflow",
            "poll_full_workflow",
            "poll_evaluation",
            "fetch_experiment_results",
            "analyze_experiment",
            "generate_bibfile",
            "generate_paper",
            "generate_latex",
            "poll_compile_latex_workflow",
        }

        graph_builder = StateGraph(
            TopicOpenEndedResearchState,
            input_schema=TopicOpenEndedResearchInputState,
            output_schema=TopicOpenEndedResearchOutputState,
        )

        for node_name, method in PIPELINE:
            graph_builder.add_node(node_name, method)

        for node in UPLOAD_AFTER:
            github_upload_node = f"github_upload_after_{node}"
            graph_builder.add_node(github_upload_node, self._upload_research_history)
            db_update_node = f"db_update_after_{node}"
            graph_builder.add_node(db_update_node, self._update_record)

        graph_builder.add_edge(START, PIPELINE[0][0])

        for (prev, _), (nxt, _) in zip(PIPELINE, PIPELINE[1:], strict=False):
            if prev in UPLOAD_AFTER:
                github_upload_node = f"github_upload_after_{prev}"
                graph_builder.add_edge(prev, github_upload_node)
                db_update_node = f"db_update_after_{prev}"
                graph_builder.add_edge(prev, db_update_node)
                graph_builder.add_edge([github_upload_node, db_update_node], nxt)
            else:
                graph_builder.add_edge(prev, nxt)

        graph_builder.add_edge(PIPELINE[-1][0], END)

        return graph_builder.compile()


if __name__ == "__main__":
    import asyncio

    from airas.container import Container
    from airas.core.types.experimental_design import RunnerConfig
    from airas.core.types.wandb import WandbConfig

    async def main() -> None:
        container = Container()
        await container.init_resources()

        try:
            graph = TopicOpenEndedResearchSubgraph(
                search_index=container.airas_db_search_index(),
                github_client=container.github_client(),
                arxiv_client=container.arxiv_client(),
                langchain_client=container.langchain_client(),
                e2e_service=container.e2e_service,
                runner_config=RunnerConfig(
                    runner_label=["ubuntu-latest"],
                    description="Sample runner config for graph preview",
                ),
                wandb_config=WandbConfig(entity="demo", project="demo"),
                task_id=UUID("00000000-0000-0000-0000-000000000001"),
            ).build_graph()

            print(graph.get_graph().draw_mermaid())
        finally:
            await container.shutdown_resources()

    asyncio.run(main())
