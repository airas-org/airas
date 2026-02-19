import logging
from typing import Annotated, Any

from langgraph.graph import END, START, StateGraph
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
from airas.usecases.executors.dispatch_sanity_check_subgraph.dispatch_sanity_check_subgraph import (
    DispatchSanityCheckSubgraph,
)
from airas.usecases.github.download_github_actions_artifacts_subgraph.download_github_actions_artifacts_subgraph import (
    DownloadGithubActionsArtifactsSubgraph,
)
from airas.usecases.github.poll_github_actions_subgraph.poll_github_actions_subgraph import (
    PollGithubActionsSubgraph,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("sanity_check_graph")(f)  # noqa: E731

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


class SanityCheckInputState(TypedDict):
    github_config: GitHubConfig
    run_ids: list[str]
    research_topic: str
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign


class SanityCheckState(SanityCheckInputState, total=False):
    current_run_id_index: int
    sanity_check_retry_counts: dict[str, int]
    artifact_data: Annotated[dict, lambda x, y: y]
    sanity_workflow_run_id: str | None
    sanity_validation_workflow_run_id: str | None


class SanityCheckGraph:
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
    async def _dispatch_sanity_check(self, state: SanityCheckState) -> dict[str, Any]:
        current_index = state.get("current_run_id_index", 0)
        run_ids = state.get("run_ids", [])
        if current_index >= len(run_ids):
            error_msg = f"Invalid run_id index: {current_index} >= {len(run_ids)}"
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)
        current_run_id = run_ids[current_index]
        retry_count = state.get("sanity_check_retry_counts", {}).get(current_run_id, 0)
        logger.info(
            f"=== Dispatch Sanity Check for run_id={current_run_id} "
            f"(index {current_index + 1}/{len(run_ids)}, attempt {retry_count + 1}/{_MAX_RETRY_GITHUB_ACTIONS_VALIDATION}) ==="
        )

        dispatch_result = (
            await DispatchSanityCheckSubgraph(
                github_client=self.github_client,
                runner_label=self.runner_config.runner_label,
            )
            .build_graph()
            .ainvoke(
                {"github_config": state["github_config"], "run_id": current_run_id}
            )
        )

        if not dispatch_result.get("dispatched", False):
            error_msg = (
                f"Failed to dispatch sanity workflow for run_id={current_run_id}"
            )
            logger.error(error_msg)
            raise WorkflowExecutionError(error_msg)

        logger.info(
            f"Sanity workflow dispatched successfully for run_id={current_run_id}"
        )
        return {}

    @record_execution_time
    async def _poll_sanity(self, state: SanityCheckState) -> dict[str, Any]:
        current_index = state.get("current_run_id_index", 0)
        current_run_id = state.get("run_ids", [])[current_index]
        logger.info(f"Polling sanity workflow for run_id={current_run_id}...")

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
            f"Sanity workflow completed for run_id={current_run_id}: status={status}, conclusion={conclusion}"
        )
        self._validate_github_actions_completion("Sanity", status, conclusion)
        return {"sanity_workflow_run_id": workflow_run_id}

    @record_execution_time
    async def _dispatch_validation(self, state: SanityCheckState) -> dict[str, Any]:
        current_index = state.get("current_run_id_index", 0)
        current_run_id = state.get("run_ids", [])[current_index]
        logger.info(
            f"Dispatching validation for sanity workflow (run_id={current_run_id})..."
        )

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
                    "run_id": current_run_id,
                    "workflow_run_id": state.get("sanity_workflow_run_id"),
                    "run_stage": "sanity",
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                    "wandb_config": self.wandb_config,
                    "github_actions_agent": self.github_actions_agent,
                }
            )
        )

        if not validation_dispatch_result.get("dispatched", False):
            error_msg = f"Failed to dispatch validation for sanity workflow (run_id={current_run_id})"
            logger.error(error_msg)
            raise WorkflowExecutionError(error_msg)

        logger.info(
            f"Validation for sanity workflow dispatched successfully (run_id={current_run_id})"
        )
        return {}

    @record_execution_time
    async def _poll_validation(self, state: SanityCheckState) -> dict[str, Any]:
        current_index = state.get("current_run_id_index", 0)
        current_run_id = state.get("run_ids", [])[current_index]
        logger.info(
            f"Polling validation for sanity workflow (run_id={current_run_id})..."
        )

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
            f"Sanity validation completed for run_id={current_run_id}: "
            f"status={validation_status}, conclusion={validation_conclusion}"
        )
        self._validate_github_actions_completion(
            "Sanity Validation", validation_status, validation_conclusion
        )
        return {"sanity_validation_workflow_run_id": validation_workflow_run_id}

    @record_execution_time
    async def _download_artifact(self, state: SanityCheckState) -> dict[str, Any]:
        current_index = state.get("current_run_id_index", 0)
        current_run_id = state.get("run_ids", [])[current_index]
        logger.info(
            f"Downloading artifact from sanity validation workflow (run_id={current_run_id})..."
        )

        artifact_result = (
            await DownloadGithubActionsArtifactsSubgraph(
                github_client=self.github_client
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "workflow_run_id": state.get("sanity_validation_workflow_run_id"),
                }
            )
        )

        if not (artifact_data := artifact_result.get("artifact_data", {})):
            error_msg = (
                f"No artifact data found for sanity workflow (run_id={current_run_id})"
            )
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        if (validation_action := artifact_data.get("validation_action")) not in {
            "retry",
            "proceed",
        }:
            error_msg = (
                f"Invalid validation_action: '{validation_action}' for sanity workflow (run_id={current_run_id}). "
                f"Expected 'retry' or 'proceed'"
            )
            logger.error(error_msg)
            raise WorkflowValidationError(error_msg)

        logger.info(
            f"Sanity workflow validation result for run_id={current_run_id}: {validation_action}"
        )
        return {"artifact_data": artifact_data}

    def _route_after_sanity_check(self, state: SanityCheckState) -> str:
        current_index = state.get("current_run_id_index", 0)
        run_ids = state.get("run_ids", [])
        current_run_id = run_ids[current_index]
        retry_count = state.get("sanity_check_retry_counts", {}).get(current_run_id, 0)
        action = state.get("artifact_data", {}).get("validation_action")

        if action == "retry":
            if retry_count >= _MAX_RETRY_GITHUB_ACTIONS_VALIDATION:
                error_msg = (
                    f"Maximum retry count ({_MAX_RETRY_GITHUB_ACTIONS_VALIDATION}) exceeded "
                    f"for run_id={current_run_id} at index {current_index}"
                )
                logger.error(error_msg)
                raise WorkflowValidationError(error_msg)
            logger.warning(
                f"Validation failed for run_id={current_run_id} at index {current_index} "
                f"(retry {retry_count + 1}/{_MAX_RETRY_GITHUB_ACTIONS_VALIDATION}). Retrying."
            )
            return "retry"

        if current_index + 1 < len(run_ids):
            logger.info(
                f"Sanity check passed for run_id={current_run_id} at index {current_index}. "
                f"Moving to next run_id (index {current_index + 1}/{len(run_ids)})"
            )
            return "proceed"

        logger.info(f"All {len(run_ids)} run IDs completed sanity checks successfully.")
        return "end"

    @record_execution_time
    def _increment_run_id_index(self, state: SanityCheckState) -> dict[str, int]:
        current_index = state.get("current_run_id_index", 0)
        new_index = current_index + 1
        logger.info(f"Incrementing run_id index: {current_index} -> {new_index}")
        return {"current_run_id_index": new_index}

    @record_execution_time
    def _increment_retry_count(
        self, state: SanityCheckState
    ) -> dict[str, dict[str, int]]:
        current_index = state.get("current_run_id_index", 0)
        current_run_id = state.get("run_ids", [])[current_index]
        retry_counts: dict[str, int] = state.get("sanity_check_retry_counts", {})
        current_retry = retry_counts.get(current_run_id, 0)
        new_retry = current_retry + 1
        logger.info(
            f"Incrementing retry count for run_id={current_run_id}: {current_retry} -> {new_retry}"
        )
        return {
            "sanity_check_retry_counts": {**retry_counts, current_run_id: new_retry}
        }

    def build_graph(self):
        graph_builder = StateGraph(
            SanityCheckState,
            input_schema=SanityCheckInputState,
        )

        graph_builder.add_node("dispatch_sanity_check", self._dispatch_sanity_check)
        graph_builder.add_node("poll_sanity", self._poll_sanity)
        graph_builder.add_node("dispatch_validation", self._dispatch_validation)
        graph_builder.add_node("poll_validation", self._poll_validation)
        graph_builder.add_node("download_artifact", self._download_artifact)
        graph_builder.add_node("increment_retry_count", self._increment_retry_count)
        graph_builder.add_node("increment_run_id_index", self._increment_run_id_index)

        graph_builder.add_edge(START, "dispatch_sanity_check")
        graph_builder.add_edge("dispatch_sanity_check", "poll_sanity")
        graph_builder.add_edge("poll_sanity", "dispatch_validation")
        graph_builder.add_edge("dispatch_validation", "poll_validation")
        graph_builder.add_edge("poll_validation", "download_artifact")
        graph_builder.add_conditional_edges(
            "download_artifact",
            self._route_after_sanity_check,
            {
                "retry": "increment_retry_count",
                "proceed": "increment_run_id_index",
                "end": END,
            },
        )
        graph_builder.add_edge("increment_retry_count", "dispatch_sanity_check")
        graph_builder.add_edge("increment_run_id_index", "dispatch_sanity_check")

        return graph_builder.compile()
