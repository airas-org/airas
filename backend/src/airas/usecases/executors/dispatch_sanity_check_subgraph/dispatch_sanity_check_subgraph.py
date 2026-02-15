import json
import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.dispatch_workflow import dispatch_workflow

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("dispatch_sanity_check_subgraph")(f)  # noqa: E731


class DispatchSanityCheckSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    run_id: str


class DispatchSanityCheckSubgraphOutputState(ExecutionTimeState):
    dispatched: bool


class DispatchSanityCheckSubgraphState(
    DispatchSanityCheckSubgraphInputState,
    DispatchSanityCheckSubgraphOutputState,
    total=False,
):
    pass


class DispatchSanityCheckSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        runner_label: list[str] | None = None,
        workflow_file: str = "run_sanity_check.yml",
    ):
        self.github_client = github_client
        self.runner_label = runner_label or ["ubuntu-latest"]
        self.workflow_file = workflow_file

    @record_execution_time
    async def _dispatch_sanity_check(
        self, state: DispatchSanityCheckSubgraphState
    ) -> dict[str, bool]:
        github_config = state["github_config"]
        run_id = state["run_id"]

        logger.info(
            f"Dispatching sanity check for run_id={run_id} on branch '{github_config.branch_name}'"
        )

        inputs = {
            "branch_name": github_config.branch_name,
            "run_id": run_id,
            "runner_label": json.dumps(self.runner_label),
        }

        success = await dispatch_workflow(
            self.github_client,
            github_config.github_owner,
            github_config.repository_name,
            github_config.branch_name,
            self.workflow_file,
            inputs,
        )

        if success:
            logger.info(f"Sanity check dispatch successful for run_id={run_id}")
        else:
            logger.error(f"Sanity check dispatch failed for run_id={run_id}")

        return {"dispatched": success}

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchSanityCheckSubgraphState,
            input_schema=DispatchSanityCheckSubgraphInputState,
            output_schema=DispatchSanityCheckSubgraphOutputState,
        )

        graph_builder.add_node("dispatch_sanity_check", self._dispatch_sanity_check)

        graph_builder.add_edge(START, "dispatch_sanity_check")
        graph_builder.add_edge("dispatch_sanity_check", END)

        return graph_builder.compile()
