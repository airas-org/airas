import logging
from typing import Annotated, Any

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send
from typing_extensions import TypedDict

from airas.core.execution_timers import time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experimental_design import ExperimentalDesign, RunnerConfig
from airas.core.types.github import (
    GitHubActionsAgent,
    GitHubActionsConclusion,
    GitHubActionsStatus,
    GitHubConfig,
)
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.wandb import WandbConfig
from airas.infra.github_client import GithubClient
from airas.usecases.executors.dispatch_experiment_validation_subgraph.dispatch_experiment_validation_subgraph import (
    DispatchExperimentValidationLLMMapping,
    DispatchExperimentValidationSubgraph,
)
from airas.usecases.executors.dispatch_main_experiment_subgraph.dispatch_main_experiment_subgraph import (
    DispatchMainExperimentSubgraph,
)
from airas.usecases.github.download_github_actions_artifacts_subgraph.download_github_actions_artifacts_subgraph import (
    DownloadGithubActionsArtifactsSubgraph,
)
from airas.usecases.github.nodes.create_branch import create_branches_for_run_ids
from airas.usecases.github.poll_github_actions_subgraph.poll_github_actions_subgraph import (
    PollGithubActionsSubgraph,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("main_experiment_graph")(f)  # noqa: E731

_STANDARD_WORKFLOW_RECURSION_LIMIT = 50000
_MAX_RETRY_GITHUB_ACTIONS_VALIDATION = 10


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


class MainExperimentInputState(TypedDict):
    github_config: GitHubConfig
    run_ids: list[str]
    research_topic: str
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign


class MainExperimentState(MainExperimentInputState, total=False):
    main_experiment_branches: list[str]
    main_experiment_branch_results: Annotated[dict[str, dict], lambda x, y: {**x, **y}]


class MainExperimentGraph:
    def __init__(
        self,
        github_client: GithubClient,
        runner_config: RunnerConfig,
        wandb_config: WandbConfig,
        github_actions_agent: GitHubActionsAgent,
        llm_mapping: DispatchExperimentValidationLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.runner_config = runner_config
        self.wandb_config = wandb_config
        self.github_actions_agent = github_actions_agent
        self.llm_mapping = llm_mapping or DispatchExperimentValidationLLMMapping()

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

        if status in {GitHubActionsStatus.FAILURE, GitHubActionsStatus.STARTUP_FAILURE}:
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
    async def _create_branches(
        self, state: MainExperimentState
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

    def _dispatch_branches(self, state: MainExperimentState) -> list[Send]:
        branches = state.get("main_experiment_branches", [])
        logger.info(
            f"=== Dispatching {len(branches)} branches for independent processing ==="
        )

        return [
            Send(
                "run_branch_pipeline",
                {
                    "main_experiment_branch_name": branch,
                    "github_config": state["github_config"],
                    "research_topic": state["research_topic"],
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                },
            )
            for branch in branches
        ]

    @record_execution_time
    async def _run_branch_pipeline(self, state: dict[str, Any]) -> dict[str, Any]:
        """Executes the entire pipeline for a single branch (dispatch → poll → validate → download), including retries.

        Since this is invoked via Send as an independent node per branch, LangGraph’s
        superstep synchronization does not occur, and validation begins immediately
        after the experiment completes.
        """
        main_experiment_branch_name: str = state["main_experiment_branch_name"]
        github_config: GitHubConfig = state["github_config"]
        run_id: str = main_experiment_branch_name.replace(
            f"{github_config.branch_name}-", ""
        )
        branch_config = GitHubConfig(
            **github_config.model_dump(exclude={"branch_name"}),
            branch_name=main_experiment_branch_name,
        )

        retry_count = 0
        artifact_data: dict = {}

        while True:
            # Step 1: Dispatch main experiment
            logger.info(
                f"=== Dispatch Main Experiment for branch={main_experiment_branch_name}, run_id={run_id} "
                f"(attempt {retry_count + 1}/{_MAX_RETRY_GITHUB_ACTIONS_VALIDATION}) ==="
            )
            dispatch_result = (
                await DispatchMainExperimentSubgraph(
                    github_client=self.github_client,
                    runner_label=self.runner_config.runner_label,
                )
                .build_graph()
                .ainvoke({"github_config": branch_config, "run_id": run_id})
            )
            if not dispatch_result.get("dispatched", False):
                error_msg = f"Failed to dispatch main experiment workflow for branch={main_experiment_branch_name}"
                logger.error(error_msg)
                raise WorkflowExecutionError(error_msg)

            logger.info(
                f"Main experiment workflow dispatched successfully for branch={main_experiment_branch_name}"
            )

            # Step 2: Poll main experiment
            logger.info(
                f"Polling main experiment workflow for branch={main_experiment_branch_name}..."
            )
            poll_result = (
                await PollGithubActionsSubgraph(github_client=self.github_client)
                .build_graph()
                .ainvoke(
                    {"github_config": branch_config},
                    {"recursion_limit": _STANDARD_WORKFLOW_RECURSION_LIMIT},
                )
            )
            workflow_run_id = poll_result.get("workflow_run_id")
            logger.info(
                f"Main experiment workflow completed for branch={main_experiment_branch_name}: "
                f"status={poll_result.get('status')}, conclusion={poll_result.get('conclusion')}"
            )
            self._validate_github_actions_completion(
                "Main", poll_result.get("status"), poll_result.get("conclusion")
            )

            # Step 3: Dispatch validation
            logger.info(
                f"Dispatching validation for main experiment (branch={main_experiment_branch_name})..."
            )
            validation_dispatch_result = (
                await DispatchExperimentValidationSubgraph(
                    github_client=self.github_client,
                    llm_mapping=self.llm_mapping,
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
            if not validation_dispatch_result.get("dispatched", False):
                error_msg = f"Failed to dispatch validation for main experiment (branch={main_experiment_branch_name})"
                logger.error(error_msg)
                raise WorkflowExecutionError(error_msg)

            logger.info(
                f"Validation for main experiment dispatched successfully (branch={main_experiment_branch_name})"
            )

            # Step 4: Poll validation
            logger.info(
                f"Polling validation for main experiment (branch={main_experiment_branch_name})..."
            )
            validation_poll_result = (
                await PollGithubActionsSubgraph(github_client=self.github_client)
                .build_graph()
                .ainvoke(
                    {"github_config": branch_config},
                    {"recursion_limit": _STANDARD_WORKFLOW_RECURSION_LIMIT},
                )
            )
            validation_workflow_run_id = validation_poll_result.get("workflow_run_id")
            logger.info(
                f"Main experiment validation completed for branch={main_experiment_branch_name}: "
                f"status={validation_poll_result.get('status')}, conclusion={validation_poll_result.get('conclusion')}"
            )
            self._validate_github_actions_completion(
                "Main Validation",
                validation_poll_result.get("status"),
                validation_poll_result.get("conclusion"),
            )

            # Step 5: Download artifact
            logger.info(
                f"Downloading artifact from main experiment validation (branch={main_experiment_branch_name})..."
            )
            artifact_result = (
                await DownloadGithubActionsArtifactsSubgraph(
                    github_client=self.github_client
                )
                .build_graph()
                .ainvoke(
                    {
                        "github_config": branch_config,
                        "workflow_run_id": validation_workflow_run_id,
                    }
                )
            )
            artifact_data = artifact_result.get("artifact_data", {})
            if not artifact_data:
                error_msg = f"No artifact data found for main experiment (branch={main_experiment_branch_name})"
                logger.error(error_msg)
                raise WorkflowValidationError(error_msg)

            validation_action = artifact_data.get("validation_action")
            if validation_action not in {"retry", "proceed"}:
                error_msg = (
                    f"Invalid validation_action: '{validation_action}' for main experiment (branch={main_experiment_branch_name}). "
                    f"Expected 'retry' or 'proceed'"
                )
                logger.error(error_msg)
                raise WorkflowValidationError(error_msg)

            logger.info(
                f"Main experiment validation result for branch={main_experiment_branch_name}: {validation_action}"
            )

            # Step 6: Route — proceed or retry
            if validation_action == "proceed":
                logger.info(
                    f"branch={main_experiment_branch_name} passed after {retry_count + 1} attempt(s)"
                )
                break

            if retry_count >= _MAX_RETRY_GITHUB_ACTIONS_VALIDATION - 1:
                error_msg = (
                    f"Maximum retry count ({_MAX_RETRY_GITHUB_ACTIONS_VALIDATION}) exceeded "
                    f"for branch={main_experiment_branch_name}"
                )
                logger.error(error_msg)
                raise WorkflowValidationError(error_msg)

            retry_count += 1
            logger.warning(
                f"Validation failed for branch={main_experiment_branch_name} "
                f"(retry {retry_count}/{_MAX_RETRY_GITHUB_ACTIONS_VALIDATION}). Retrying."
            )

        return {
            "main_experiment_branch_results": {
                main_experiment_branch_name: {
                    "status": "success",
                    "artifact_data": artifact_data,
                }
            }
        }

    @record_execution_time
    def _collect_main_experiment_results(
        self, state: MainExperimentState
    ) -> dict[str, Any]:
        branch_results = state.get("main_experiment_branch_results", {})
        branches = state.get("main_experiment_branches", [])

        logger.info(f"=== Collecting results from {len(branches)} branches ===")
        logger.info(f"Branch results: {branch_results}")

        if not branch_results:
            error_msg = "No branch results found"
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        if len(branch_results) != len(branches):
            error_msg = (
                f"Branch results count mismatch: expected {len(branches)}, "
                f"got {len(branch_results)}"
            )
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        all_successful = all(
            result.get("status") == "success" for result in branch_results.values()
        )

        if not all_successful:
            error_msg = "Not all branches completed successfully"
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        logger.info(f"All {len(branches)} branches completed successfully")
        return {}

    def build_graph(self):
        graph_builder = StateGraph(
            MainExperimentState,
            input_schema=MainExperimentInputState,
        )

        graph_builder.add_node("create_branches", self._create_branches)
        graph_builder.add_node("run_branch_pipeline", self._run_branch_pipeline)
        graph_builder.add_node(
            "collect_main_experiment_results", self._collect_main_experiment_results
        )

        graph_builder.add_edge(START, "create_branches")
        graph_builder.add_conditional_edges(
            "create_branches",
            self._dispatch_branches,
        )
        graph_builder.add_edge("run_branch_pipeline", "collect_main_experiment_results")
        graph_builder.add_edge("collect_main_experiment_results", END)

        return graph_builder.compile()
