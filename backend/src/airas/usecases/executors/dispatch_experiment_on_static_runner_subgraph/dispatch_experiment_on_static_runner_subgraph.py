import json
import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experiment_history import RunStage
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.dispatch_workflow import dispatch_workflow

setup_logging()
logger = logging.getLogger(__name__)


def record_execution_time(f):
    return time_node("dispatch_experiment_on_static_runner_subgraph")(f)  # noqa: E731


class DispatchExperimentOnStaticRunnerSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    run_id: str


class DispatchExperimentOnStaticRunnerSubgraphOutputState(ExecutionTimeState):
    dispatched: bool


class DispatchExperimentOnStaticRunnerSubgraphState(
    DispatchExperimentOnStaticRunnerSubgraphInputState,
    DispatchExperimentOnStaticRunnerSubgraphOutputState,
    total=False,
):
    pass


class DispatchExperimentOnStaticRunnerSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        workflow_file: str = "run_experiment.yml",
        runner_label: list[str] | None = None,
        run_stage: RunStage | None = None,
    ):
        self.github_client = github_client
        self.workflow_file = workflow_file
        self.runner_label = runner_label or ["ubuntu-latest"]
        self.run_stage = run_stage

    @record_execution_time
    async def _dispatch_experiment_on_static_runner(
        self, state: DispatchExperimentOnStaticRunnerSubgraphState
    ) -> dict[str, bool]:
        github_config = state["github_config"]
        run_id = state["run_id"]

        logger.info(
            f"Dispatching {self.workflow_file} for run_id={run_id} on branch '{github_config.branch_name}' "
            f"with runner_label={self.runner_label}"
        )

        inputs = {
            "branch_name": github_config.branch_name,
            "run_id": run_id,
            "runner_label": json.dumps(self.runner_label),
        }

        if self.run_stage is not None:
            inputs["mode"] = self.run_stage.value

        success = await dispatch_workflow(
            self.github_client,
            github_config.github_owner,
            github_config.repository_name,
            github_config.branch_name,
            self.workflow_file,
            inputs,
        )

        if success:
            logger.info(
                f"Dispatch successful: {self.workflow_file} for run_id={run_id}"
            )
        else:
            logger.error(f"Dispatch failed: {self.workflow_file} for run_id={run_id}")

        return {"dispatched": success}

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchExperimentOnStaticRunnerSubgraphState,
            input_schema=DispatchExperimentOnStaticRunnerSubgraphInputState,
            output_schema=DispatchExperimentOnStaticRunnerSubgraphOutputState,
        )

        graph_builder.add_node(
            "dispatch_experiment_on_static_runner",
            self._dispatch_experiment_on_static_runner,
        )

        graph_builder.add_edge(START, "dispatch_experiment_on_static_runner")
        graph_builder.add_edge("dispatch_experiment_on_static_runner", END)

        return graph_builder.compile()
