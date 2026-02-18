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

record_execution_time = lambda f: time_node("dispatch_visualization_subgraph")(f)  # noqa: E731


class DispatchVisualizationSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    run_ids: list[str]


class DispatchVisualizationSubgraphOutputState(ExecutionTimeState):
    dispatched: bool


class DispatchVisualizationSubgraphState(
    DispatchVisualizationSubgraphInputState,
    DispatchVisualizationSubgraphOutputState,
    total=False,
):
    pass


class DispatchVisualizationSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        runner_label: list[str] | None = None,
        workflow_file: str = "run_visualization.yml",
    ):
        self.github_client = github_client
        self.runner_label = runner_label or ["ubuntu-latest"]
        self.workflow_file = workflow_file

    @record_execution_time
    async def _dispatch_visualization(
        self, state: DispatchVisualizationSubgraphState
    ) -> dict[str, bool]:
        github_config = state["github_config"]
        run_ids = state["run_ids"]

        logger.info(
            f"Dispatching visualization for {len(run_ids)} run_ids on branch '{github_config.branch_name}'"
        )
        logger.info(f"Run IDs: {', '.join(run_ids)}")

        inputs = {
            "branch_name": github_config.branch_name,
            "run_ids": json.dumps(run_ids),
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
            logger.info("Visualization dispatch successful")
        else:
            logger.error("Visualization dispatch failed")

        return {"dispatched": success}

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchVisualizationSubgraphState,
            input_schema=DispatchVisualizationSubgraphInputState,
            output_schema=DispatchVisualizationSubgraphOutputState,
        )

        graph_builder.add_node("dispatch_visualization", self._dispatch_visualization)

        graph_builder.add_edge(START, "dispatch_visualization")
        graph_builder.add_edge("dispatch_visualization", END)

        return graph_builder.compile()
