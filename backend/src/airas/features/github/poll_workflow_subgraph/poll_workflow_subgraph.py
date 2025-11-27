import argparse
import asyncio
import logging
import time
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.github.poll_workflow_subgraph.nodes.check_workflow_completion import (
    check_workflow_completion,
)
from airas.features.github.poll_workflow_subgraph.nodes.get_baseline_workflow_count import (
    get_baseline_workflow_count,
)
from airas.features.github.poll_workflow_subgraph.nodes.get_workflow_runs import (
    get_workflow_runs,
)
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

recode_execution_time = lambda f: time_node("poll_workflow")(f)  # noqa: E731

_POLL_INTERVAL_SEC = 60
_TIMEOUT_SEC = 360000  # NOTE: 6000 minutes (matching YAML timeout-minutes setting)


class PollWorkflowInputState(TypedDict):
    github_config: GitHubConfig


class PollWorkflowHiddenState(TypedDict):
    baseline_count: int | None
    workflow_runs_response: dict | None
    start_time: float
    poll_count: int


class PollWorkflowOutputState(TypedDict):
    run_id: int | None
    is_completed: bool


class PollWorkflowState(
    PollWorkflowInputState,
    PollWorkflowHiddenState,
    PollWorkflowOutputState,
    ExecutionTimeState,
):
    pass


class PollWorkflowSubgraph(BaseSubgraph):
    InputState = PollWorkflowInputState
    OutputState = PollWorkflowOutputState

    def __init__(
        self,
        github_client: GithubClient,
        poll_interval_sec: int = _POLL_INTERVAL_SEC,
        timeout_sec: int = _TIMEOUT_SEC,
    ):
        check_api_key(
            github_personal_access_token_check=True,
        )
        self.github_client = github_client
        self.poll_interval_sec = poll_interval_sec
        self.timeout_sec = timeout_sec

    @recode_execution_time
    async def _get_baseline_count(self, state: PollWorkflowState) -> Command:
        cfg = state["github_config"]
        logger.info(
            f"Starting workflow polling for {cfg.repository_name} on branch {cfg.branch_name}"
        )

        baseline_count = await get_baseline_workflow_count(
            github_config=cfg,
            github_client=self.github_client,
        )

        if baseline_count is None:
            logger.error("Failed to get baseline workflow count")
            return Command(
                update={
                    "is_completed": False,
                    "run_id": None,
                },
                goto=END,
            )

        return Command(
            update={
                "baseline_count": baseline_count,
                "start_time": time.time(),
                "poll_count": 0,
            },
            goto="poll_workflow_status",
        )

    @recode_execution_time
    async def _poll_workflow_status(self, state: PollWorkflowState) -> Command:
        elapsed_time = time.time() - state["start_time"]
        if elapsed_time > self.timeout_sec:
            logger.error(f"Workflow polling timed out after {elapsed_time:.2f} seconds")
            return Command(
                update={
                    "is_completed": False,
                    "run_id": None,
                },
                goto=END,
            )

        poll_count = state.get("poll_count", 0) + 1
        logger.info(f"Polling attempt #{poll_count} (elapsed: {elapsed_time:.2f}s)")

        workflow_runs_response = await get_workflow_runs(
            github_config=state["github_config"],
            github_client=self.github_client,
        )

        return Command(
            update={
                "workflow_runs_response": workflow_runs_response,
                "poll_count": poll_count,
            },
            goto="check_completion",
        )

    @recode_execution_time
    async def _check_completion(self, state: PollWorkflowState) -> Command:
        baseline_count = state.get("baseline_count")
        if baseline_count is None:
            logger.error("Baseline count is not set")
            return Command(
                update={
                    "is_completed": False,
                    "run_id": None,
                },
                goto=END,
            )

        run_id, is_completed = check_workflow_completion(
            workflow_runs_response=state.get("workflow_runs_response"),
            baseline_count=baseline_count,
        )

        if is_completed:
            logger.info(f"Workflow {run_id} completed successfully")
            return Command(
                update={
                    "run_id": run_id,
                    "is_completed": True,
                },
                goto=END,
            )

        logger.info(
            f"Workflow not yet completed, will retry after {self.poll_interval_sec}s"
        )
        return Command(
            update={
                "is_completed": False,
            },
            goto="sleep_and_retry",
        )

    @recode_execution_time
    async def _sleep_and_retry(
        self, _state: PollWorkflowState
    ) -> Command[Literal["poll_workflow_status"]]:
        await asyncio.sleep(self.poll_interval_sec)
        return Command(goto="poll_workflow_status")

    def build_graph(self):
        graph_builder = StateGraph(PollWorkflowState)

        graph_builder.add_node("get_baseline_count", self._get_baseline_count)
        graph_builder.add_node("poll_workflow_status", self._poll_workflow_status)
        graph_builder.add_node("check_completion", self._check_completion)
        graph_builder.add_node("sleep_and_retry", self._sleep_and_retry)

        graph_builder.add_edge(START, "get_baseline_count")

        return graph_builder.compile()


async def main():
    from airas.core.container import container

    parser = argparse.ArgumentParser(description="PollWorkflowSubgraph")
    parser.add_argument(
        "--github-owner",
        default="auto-res2",
        help="Your GitHub owner (default: auto-res2)",
    )
    parser.add_argument("repository_name", help="Your repository name")
    parser.add_argument("branch_name", help="Your branch name")
    args = parser.parse_args()

    github_config = GitHubConfig(
        github_owner=args.github_owner,
        repository_name=args.repository_name,
        branch_name=args.branch_name,
    )

    container.wire(modules=[__name__])

    try:
        result = await PollWorkflowSubgraph(
            github_client=container.github_client,
        ).arun({"github_config": github_config})
        print(f"Result: {result}")
    finally:
        await container.shutdown_resources()


if __name__ == "__main__":
    import sys

    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running PollWorkflow: {e}")
        sys.exit(1)
