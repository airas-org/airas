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

record_execution_time = lambda f: time_node("dispatch_main_experiment_subgraph")(f)  # noqa: E731


class DispatchMainExperimentSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    run_id: str


class DispatchMainExperimentSubgraphOutputState(ExecutionTimeState):
    dispatched: bool


class DispatchMainExperimentSubgraphState(
    DispatchMainExperimentSubgraphInputState,
    DispatchMainExperimentSubgraphOutputState,
    total=False,
):
    pass


class DispatchMainExperimentSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        runner_label: list[str] | None = None,
        workflow_file: str = "run_main_experiment.yml",
    ):
        self.github_client = github_client
        self.runner_label = runner_label or ["ubuntu-latest"]
        self.workflow_file = workflow_file

    @record_execution_time
    async def _dispatch_main_experiment(
        self, state: DispatchMainExperimentSubgraphState
    ) -> dict[str, bool]:
        github_config = state["github_config"]
        run_id = state["run_id"]

        logger.info(
            f"Dispatching main experiment for run_id={run_id} on branch '{github_config.branch_name}'"
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
            logger.info(f"Main experiment dispatch successful for run_id={run_id}")
        else:
            logger.error(f"Main experiment dispatch failed for run_id={run_id}")

        return {"dispatched": success}

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchMainExperimentSubgraphState,
            input_schema=DispatchMainExperimentSubgraphInputState,
            output_schema=DispatchMainExperimentSubgraphOutputState,
        )

        graph_builder.add_node(
            "dispatch_main_experiment", self._dispatch_main_experiment
        )

        graph_builder.add_edge(START, "dispatch_main_experiment")
        graph_builder.add_edge("dispatch_main_experiment", END)

        return graph_builder.compile()
