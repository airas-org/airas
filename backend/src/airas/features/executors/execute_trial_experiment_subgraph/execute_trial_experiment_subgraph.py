import json
import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.features.executors.nodes.read_run_ids import (
    read_run_ids_from_repository,
)
from airas.features.github.nodes.dispatch_workflow import (
    dispatch_workflow,
)
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("execute_trial_experiment_subgraph")(f)  # noqa: E731


class ExecuteTrialExperimentSubgraphInputState(TypedDict):
    github_config: GitHubConfig


class ExecuteTrialExperimentSubgraphOutputState(ExecutionTimeState):
    dispatched: bool
    run_ids: list[str]


class ExecuteTrialExperimentSubgraphState(
    ExecuteTrialExperimentSubgraphInputState,
    ExecuteTrialExperimentSubgraphOutputState,
    total=False,
):
    pass


class ExecuteTrialExperimentSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        runner_label: str = "ubuntu-latest",
        workflow_file: str = "dev_run_trial_experiment_with_claude_code.yml",
    ):
        self.github_client = github_client
        self.runner_label = runner_label
        self.workflow_file = workflow_file

    @record_execution_time
    async def _read_run_ids(
        self, state: ExecuteTrialExperimentSubgraphState
    ) -> dict[str, list[str]]:
        run_ids = await read_run_ids_from_repository(
            self.github_client,
            state["github_config"],
        )
        return {"run_ids": run_ids}

    @record_execution_time
    async def _dispatch_trial_experiment(
        self, state: ExecuteTrialExperimentSubgraphState
    ) -> dict[str, bool]:
        run_ids = state.get("run_ids", [])
        if not run_ids:
            logger.error("No run_ids found in state")
            return {"dispatched": False}

        github_config = state["github_config"]

        logger.info(
            f"Dispatching trial experiment: {len(run_ids)} run_ids on branch '{github_config.branch_name}'"
        )
        logger.info(f"Run IDs: {', '.join(run_ids)}")

        inputs = {
            "runner_label": json.dumps([self.runner_label]),
            "run_ids": json.dumps(run_ids),
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
            logger.info("Trial experiment dispatch successful")
        else:
            logger.error("Trial experiment dispatch failed")

        return {"dispatched": success}

    def build_graph(self):
        graph_builder = StateGraph(
            ExecuteTrialExperimentSubgraphState,
            input_schema=ExecuteTrialExperimentSubgraphInputState,
            output_schema=ExecuteTrialExperimentSubgraphOutputState,
        )

        graph_builder.add_node("read_run_ids", self._read_run_ids)
        graph_builder.add_node(
            "dispatch_trial_experiment", self._dispatch_trial_experiment
        )

        graph_builder.add_edge(START, "read_run_ids")
        graph_builder.add_edge("read_run_ids", "dispatch_trial_experiment")
        graph_builder.add_edge("dispatch_trial_experiment", END)

        return graph_builder.compile()
