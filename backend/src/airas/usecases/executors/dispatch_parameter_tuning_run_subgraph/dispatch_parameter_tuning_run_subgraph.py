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


def record_execution_time(f):
    return time_node("dispatch_parameter_tuning_run_subgraph")(f)


class DispatchParameterTuningRunSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    repro_id: str
    repo_url: str


class DispatchParameterTuningRunSubgraphOutputState(ExecutionTimeState):
    dispatched: bool


class DispatchParameterTuningRunSubgraphState(
    DispatchParameterTuningRunSubgraphInputState,
    DispatchParameterTuningRunSubgraphOutputState,
    total=False,
):
    pass


class DispatchParameterTuningRunSubgraph:
    # Tuning has no code-generation step: the tune_driver.py reuses the reproduction's src/main.py.
    def __init__(
        self,
        github_client: GithubClient,
        runner_label: list[str] | None = None,
        workflow_file: str = "run_parameter_tuning_run.yml",
    ):
        self.github_client = github_client
        self.runner_label = runner_label or ["ubuntu-latest"]
        self.workflow_file = workflow_file

    @record_execution_time
    async def _dispatch_parameter_tuning_run(
        self, state: DispatchParameterTuningRunSubgraphState
    ) -> dict[str, bool]:
        github_config = state["github_config"]

        logger.info(
            f"Dispatching {self.workflow_file} on branch "
            f"'{github_config.branch_name}' with runner_label={self.runner_label}"
        )

        inputs: dict[str, str] = {
            "branch_name": github_config.branch_name,
            "repro_id": state["repro_id"],
            "repo_url": state["repo_url"],
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
            logger.info(f"Dispatch successful: {self.workflow_file}")
        else:
            logger.error(f"Dispatch failed: {self.workflow_file}")

        return {"dispatched": success}

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchParameterTuningRunSubgraphState,
            input_schema=DispatchParameterTuningRunSubgraphInputState,
            output_schema=DispatchParameterTuningRunSubgraphOutputState,
        )
        graph_builder.add_node(
            "dispatch_parameter_tuning_run", self._dispatch_parameter_tuning_run
        )
        graph_builder.add_edge(START, "dispatch_parameter_tuning_run")
        graph_builder.add_edge("dispatch_parameter_tuning_run", END)
        return graph_builder.compile()
