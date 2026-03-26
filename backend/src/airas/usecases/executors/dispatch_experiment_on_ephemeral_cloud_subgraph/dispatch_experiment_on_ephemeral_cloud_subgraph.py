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
    return time_node("dispatch_experiment_on_ephemeral_cloud_subgraph")(f)


_CLOUD_RUNNER_WORKFLOW_FILE = "run_on_cloud_runner.yml"


class DispatchExperimentOnEphemeralCloudSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    run_id: str


class DispatchExperimentOnEphemeralCloudSubgraphOutputState(ExecutionTimeState):
    dispatched: bool


class DispatchExperimentOnEphemeralCloudSubgraphState(
    DispatchExperimentOnEphemeralCloudSubgraphInputState,
    DispatchExperimentOnEphemeralCloudSubgraphOutputState,
    total=False,
):
    pass


class DispatchExperimentOnEphemeralCloudSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        cloud_provider: str = "aws",
        gpu_instance_type: str = "g4dn.xlarge",
        max_instance_hours: int = 120,
        run_stage: RunStage | None = None,
    ):
        self.github_client = github_client
        self.cloud_provider = cloud_provider
        self.gpu_instance_type = gpu_instance_type
        self.max_instance_hours = max_instance_hours
        self.run_stage = run_stage

    @record_execution_time
    async def _dispatch_experiment_on_ephemeral_cloud(
        self, state: DispatchExperimentOnEphemeralCloudSubgraphState
    ) -> dict[str, bool]:
        github_config = state["github_config"]
        run_id = state["run_id"]

        logger.info(
            f"Dispatching {_CLOUD_RUNNER_WORKFLOW_FILE} via ephemeral cloud runner for run_id={run_id} "
            f"on branch '{github_config.branch_name}' "
            f"(provider={self.cloud_provider}, instance={self.gpu_instance_type})"
        )

        inputs = {
            "run_id": run_id,
            "branch_name": github_config.branch_name,
            "cloud_provider": self.cloud_provider,
            "gpu_instance_type": self.gpu_instance_type,
            "max_instance_hours": str(self.max_instance_hours),
        }

        if self.run_stage is not None:
            inputs["mode"] = self.run_stage.value

        success = await dispatch_workflow(
            self.github_client,
            github_config.github_owner,
            github_config.repository_name,
            github_config.branch_name,
            _CLOUD_RUNNER_WORKFLOW_FILE,
            inputs,
        )

        if success:
            logger.info(
                f"Ephemeral cloud dispatch successful: {_CLOUD_RUNNER_WORKFLOW_FILE} for run_id={run_id}"
            )
        else:
            logger.error(
                f"Ephemeral cloud dispatch failed: {_CLOUD_RUNNER_WORKFLOW_FILE} for run_id={run_id}"
            )

        return {"dispatched": success}

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchExperimentOnEphemeralCloudSubgraphState,
            input_schema=DispatchExperimentOnEphemeralCloudSubgraphInputState,
            output_schema=DispatchExperimentOnEphemeralCloudSubgraphOutputState,
        )

        graph_builder.add_node(
            "dispatch_experiment_on_ephemeral_cloud",
            self._dispatch_experiment_on_ephemeral_cloud,
        )

        graph_builder.add_edge(START, "dispatch_experiment_on_ephemeral_cloud")
        graph_builder.add_edge("dispatch_experiment_on_ephemeral_cloud", END)

        return graph_builder.compile()
