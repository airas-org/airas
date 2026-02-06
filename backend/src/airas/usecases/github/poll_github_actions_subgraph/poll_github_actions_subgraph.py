import asyncio
import logging
import time
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import (
    GitHubActionsConclusion,
    GitHubActionsStatus,
    GitHubConfig,
)
from airas.infra.github_client import GithubClient
from airas.usecases.github.poll_github_actions_subgraph.nodes.get_latest_workflow_status import (
    get_latest_workflow_status,
)
from airas.usecases.github.poll_github_actions_subgraph.nodes.get_workflow_runs import (
    get_workflow_runs,
)
from airas.usecases.github.poll_github_actions_subgraph.nodes.log_workflow_failure_details import (
    log_workflow_failure_details,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("poll_github_actions")(f)  # noqa: E731

_POLL_INTERVAL_SEC = 60
_TIMEOUT_SEC = 360000  # NOTE: 6000 minutes (matching YAML timeout-minutes setting)


class PollGithubActionsInputState(TypedDict):
    github_config: GitHubConfig


class PollGithubActionsOutputState(ExecutionTimeState):
    workflow_run_id: int | None
    status: GitHubActionsStatus | None
    conclusion: GitHubActionsConclusion | None


class PollGithubActionsState(
    PollGithubActionsInputState,
    PollGithubActionsOutputState,
    total=False,
):
    current_workflow_id: int | None
    start_time: float
    poll_count: int


class PollGithubActionsSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        poll_interval_sec: int = _POLL_INTERVAL_SEC,
        timeout_sec: int = _TIMEOUT_SEC,
    ):
        self.github_client = github_client
        self.poll_interval_sec = poll_interval_sec
        self.timeout_sec = timeout_sec

    @record_execution_time
    async def _initialize(self, state: PollGithubActionsState) -> Command:
        cfg = state["github_config"]
        logger.info(
            f"Starting workflow polling for {cfg.repository_name} on branch {cfg.branch_name}"
        )

        return Command(
            update={
                "current_workflow_id": None,
                "start_time": time.time(),
                "poll_count": 0,
            },
            goto="poll_workflow_status",
        )

    @record_execution_time
    async def _poll_workflow_status(self, state: PollGithubActionsState) -> Command:
        elapsed_time = time.time() - state["start_time"]
        if elapsed_time > self.timeout_sec:
            logger.error(f"Workflow polling timed out after {elapsed_time:.2f} seconds")
            return Command(
                update={
                    "workflow_run_id": None,
                    "status": None,
                    "conclusion": None,
                },
                goto=END,
            )

        poll_count = state.get("poll_count", 0) + 1
        logger.info(f"Polling attempt #{poll_count} (elapsed: {elapsed_time:.2f}s)")

        workflow_runs_response = await get_workflow_runs(
            github_config=state["github_config"],
            github_client=self.github_client,
        )

        workflow_run_id, status, conclusion = get_latest_workflow_status(
            workflow_runs_response
        )

        return Command(
            update={
                "workflow_run_id": workflow_run_id,
                "status": status,
                "conclusion": conclusion,
                "poll_count": poll_count,
            },
            goto="check_completion",
        )

    @record_execution_time
    async def _check_completion(self, state: PollGithubActionsState) -> Command:
        workflow_run_id = state.get("workflow_run_id")
        status = state.get("status")
        conclusion = state.get("conclusion")
        current_workflow_id = state.get("current_workflow_id")

        if workflow_run_id is None:
            logger.info("No workflow found, waiting...")
            return Command(goto="sleep_and_retry")

        running_statuses = [
            GitHubActionsStatus.QUEUED,
            GitHubActionsStatus.IN_PROGRESS,
            GitHubActionsStatus.WAITING,
            GitHubActionsStatus.PENDING,
        ]
        if status in running_statuses:
            logger.info(f"Workflow {workflow_run_id} is {status}, waiting...")
            return Command(
                update={"current_workflow_id": workflow_run_id},
                goto="sleep_and_retry",
            )

        if status == GitHubActionsStatus.COMPLETED:
            if (
                current_workflow_id is not None
                and workflow_run_id != current_workflow_id
            ):
                logger.info(
                    f"New workflow {workflow_run_id} detected (was tracking {current_workflow_id}), "
                    "waiting to see if it triggers another..."
                )
                return Command(
                    update={"current_workflow_id": workflow_run_id},
                    goto="sleep_and_retry",
                )

            if current_workflow_id is None:
                logger.info(
                    f"Workflow {workflow_run_id} completed, waiting to check for recursive triggers..."
                )
                return Command(
                    update={"current_workflow_id": workflow_run_id},
                    goto="sleep_and_retry",
                )

            logger.info(
                f"Workflow chain completed. Final workflow {workflow_run_id} "
                f"with conclusion: {conclusion}"
            )

            # Only log failure details if workflow failed
            if conclusion not in {
                GitHubActionsConclusion.SUCCESS,
                GitHubActionsConclusion.NEUTRAL,
                GitHubActionsConclusion.SKIPPED,
            }:
                return Command(goto="log_workflow_failure_details")

            return Command(goto=END)

        logger.warning(f"Unknown workflow status: {status}, waiting...")
        return Command(goto="sleep_and_retry")

    @record_execution_time
    async def _log_workflow_failure_details(
        self, state: PollGithubActionsState
    ) -> Command:
        workflow_run_id = state["workflow_run_id"]

        await log_workflow_failure_details(
            workflow_run_id=workflow_run_id,
            github_config=state["github_config"],
            github_client=self.github_client,
        )

        return Command(goto=END)

    @record_execution_time
    async def _sleep_and_retry(
        self, _state: PollGithubActionsState
    ) -> Command[Literal["poll_workflow_status"]]:
        await asyncio.sleep(self.poll_interval_sec)
        return Command(goto="poll_workflow_status")

    def build_graph(self):
        graph_builder = StateGraph(PollGithubActionsState)

        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node("poll_workflow_status", self._poll_workflow_status)
        graph_builder.add_node("check_completion", self._check_completion)
        graph_builder.add_node(
            "log_workflow_failure_details", self._log_workflow_failure_details
        )
        graph_builder.add_node("sleep_and_retry", self._sleep_and_retry)

        graph_builder.add_edge(START, "initialize")

        return graph_builder.compile()
