import logging
from typing import Annotated, Any

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experimental_design import ExperimentalDesign
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
from airas.usecases.executors.dispatch_visualization_subgraph.dispatch_visualization_subgraph import (
    DispatchVisualizationSubgraph,
)
from airas.usecases.github.download_github_actions_artifacts_subgraph.download_github_actions_artifacts_subgraph import (
    DownloadGithubActionsArtifactsSubgraph,
)
from airas.usecases.github.poll_github_actions_subgraph.poll_github_actions_subgraph import (
    PollGithubActionsSubgraph,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("visualization_graph")(f)  # noqa: E731

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


class VisualizationInputState(TypedDict):
    github_config: GitHubConfig
    run_ids: list[str]
    research_topic: str
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign


class VisualizationState(VisualizationInputState, total=False):
    visualization_retry_count: int
    artifact_data: Annotated[dict, lambda x, y: y]
    visualization_workflow_run_id: str | None
    visualization_validation_workflow_run_id: str | None


class VisualizationGraph:
    def __init__(
        self,
        github_client: GithubClient,
        wandb_config: WandbConfig,
        github_actions_agent: GitHubActionsAgent,
        llm_mapping: DispatchExperimentValidationLLMMapping | None = None,
    ):
        self.github_client = github_client
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
    async def _dispatch_visualization(
        self, state: VisualizationState
    ) -> dict[str, Any]:
        retry_count = state.get("visualization_retry_count", 0)
        logger.info(
            f"=== Dispatch Visualization "
            f"(attempt {retry_count + 1}/{_MAX_RETRY_GITHUB_ACTIONS_VALIDATION}) ==="
        )

        dispatch_result = (
            await DispatchVisualizationSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "run_ids": state.get("run_ids", []),
                }
            )
        )

        if not dispatch_result.get("dispatched", False):
            error_msg = "Failed to dispatch visualization workflow"
            logger.error(error_msg)
            raise WorkflowExecutionError(error_msg)

        logger.info("Visualization workflow dispatched successfully")
        return {}

    @record_execution_time
    async def _poll_visualization(self, state: VisualizationState) -> dict[str, Any]:
        logger.info("Polling visualization workflow...")

        poll_result = (
            await PollGithubActionsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {"github_config": state["github_config"]},
                {"recursion_limit": _STANDARD_WORKFLOW_RECURSION_LIMIT},
            )
        )

        workflow_run_id = poll_result.get("workflow_run_id")
        status = poll_result.get("status")
        conclusion = poll_result.get("conclusion")
        logger.info(
            f"Visualization workflow completed: status={status}, conclusion={conclusion}"
        )
        self._validate_github_actions_completion("Visualization", status, conclusion)
        return {"visualization_workflow_run_id": workflow_run_id}

    @record_execution_time
    async def _dispatch_visualization_validation(
        self, state: VisualizationState
    ) -> dict[str, Any]:
        logger.info("Dispatching validation for visualization workflow...")

        validation_dispatch_result = (
            await DispatchExperimentValidationSubgraph(
                github_client=self.github_client,
                llm_mapping=self.llm_mapping,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "research_topic": state["research_topic"],
                    "run_id": None,
                    "workflow_run_id": state.get("visualization_workflow_run_id"),
                    "run_stage": "visualization",
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                    "wandb_config": self.wandb_config,
                    "github_actions_agent": self.github_actions_agent,
                }
            )
        )

        if not validation_dispatch_result.get("dispatched", False):
            error_msg = "Failed to dispatch validation for visualization workflow"
            logger.error(error_msg)
            raise WorkflowExecutionError(error_msg)

        logger.info("Validation for visualization workflow dispatched successfully")
        return {}

    @record_execution_time
    async def _poll_visualization_validation(
        self, state: VisualizationState
    ) -> dict[str, Any]:
        logger.info("Polling validation for visualization workflow...")

        validation_poll_result = (
            await PollGithubActionsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {"github_config": state["github_config"]},
                {"recursion_limit": _STANDARD_WORKFLOW_RECURSION_LIMIT},
            )
        )

        validation_workflow_run_id = validation_poll_result.get("workflow_run_id")
        validation_status = validation_poll_result.get("status")
        validation_conclusion = validation_poll_result.get("conclusion")
        logger.info(
            f"Visualization validation completed: status={validation_status}, conclusion={validation_conclusion}"
        )
        self._validate_github_actions_completion(
            "Visualization Validation", validation_status, validation_conclusion
        )
        return {"visualization_validation_workflow_run_id": validation_workflow_run_id}

    @record_execution_time
    async def _download_visualization_artifact(
        self, state: VisualizationState
    ) -> dict[str, Any]:
        logger.info("Downloading artifact from visualization validation workflow...")

        artifact_result = (
            await DownloadGithubActionsArtifactsSubgraph(
                github_client=self.github_client
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "workflow_run_id": state.get(
                        "visualization_validation_workflow_run_id"
                    ),
                }
            )
        )

        if not (artifact_data := artifact_result.get("artifact_data", {})):
            error_msg = "No artifact data found for visualization workflow"
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        if (validation_action := artifact_data.get("validation_action")) not in {
            "retry",
            "proceed",
        }:
            error_msg = (
                f"Invalid validation_action: '{validation_action}' for visualization workflow. "
                f"Expected 'retry' or 'proceed'"
            )
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        logger.info(f"Visualization workflow validation result: {validation_action}")
        return {"artifact_data": artifact_data}

    def _route_after_visualization(self, state: VisualizationState) -> str:
        retry_count = state.get("visualization_retry_count", 0)
        action = state.get("artifact_data", {}).get("validation_action")

        if action == "retry":
            if retry_count >= _MAX_RETRY_GITHUB_ACTIONS_VALIDATION - 1:
                error_msg = (
                    f"Maximum retry count ({_MAX_RETRY_GITHUB_ACTIONS_VALIDATION}) exceeded "
                    f"for visualization"
                )
                logger.error(error_msg)
                raise WorkflowValidationError(error_msg)
            logger.warning(
                f"Validation failed for visualization "
                f"(retry {retry_count + 1}/{_MAX_RETRY_GITHUB_ACTIONS_VALIDATION}). Retrying."
            )
            return "retry"

        logger.info(f"Visualization passed after {retry_count + 1} attempt(s)")
        return "end"

    @record_execution_time
    def _increment_visualization_retry_count(
        self, state: VisualizationState
    ) -> dict[str, int]:
        current_count = state.get("visualization_retry_count", 0)
        new_count = current_count + 1
        logger.info(
            f"Incrementing visualization retry count: {current_count} -> {new_count}"
        )
        return {"visualization_retry_count": new_count}

    def build_graph(self):
        graph_builder = StateGraph(
            VisualizationState,
            input_schema=VisualizationInputState,
        )

        graph_builder.add_node("dispatch_visualization", self._dispatch_visualization)
        graph_builder.add_node("poll_visualization", self._poll_visualization)
        graph_builder.add_node(
            "dispatch_visualization_validation", self._dispatch_visualization_validation
        )
        graph_builder.add_node(
            "poll_visualization_validation", self._poll_visualization_validation
        )
        graph_builder.add_node(
            "download_visualization_artifact", self._download_visualization_artifact
        )
        graph_builder.add_node(
            "increment_visualization_retry_count",
            self._increment_visualization_retry_count,
        )

        graph_builder.add_edge(START, "dispatch_visualization")
        graph_builder.add_edge("dispatch_visualization", "poll_visualization")
        graph_builder.add_edge(
            "poll_visualization", "dispatch_visualization_validation"
        )
        graph_builder.add_edge(
            "dispatch_visualization_validation", "poll_visualization_validation"
        )
        graph_builder.add_edge(
            "poll_visualization_validation", "download_visualization_artifact"
        )
        graph_builder.add_conditional_edges(
            "download_visualization_artifact",
            self._route_after_visualization,
            {
                "retry": "increment_visualization_retry_count",
                "end": END,
            },
        )
        graph_builder.add_edge(
            "increment_visualization_retry_count", "dispatch_visualization"
        )

        return graph_builder.compile()
