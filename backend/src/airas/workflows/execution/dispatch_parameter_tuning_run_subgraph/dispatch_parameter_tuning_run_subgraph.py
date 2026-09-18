from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.reproduction.dispatch_parameter_tuning_run import (
    WORKFLOW_FILE,
    dispatch_parameter_tuning_run,
)


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
    """`dispatch_parameter_tuning_run` as one graph node."""

    def __init__(
        self,
        github_client: GithubClient,
        runner_label: list[str] | None = None,
        workflow_file: str = WORKFLOW_FILE,
    ):
        self.github_client = github_client
        self.runner_label = runner_label
        self.workflow_file = workflow_file

    @time_node("dispatch_parameter_tuning_run_subgraph")
    async def _dispatch(self, state: DispatchParameterTuningRunSubgraphState) -> dict:
        return await dispatch_parameter_tuning_run(
            self.github_client,
            state["github_config"],
            state["repro_id"],
            repo_url=state["repo_url"],
            runner_label=self.runner_label,
            workflow_file=self.workflow_file,
        )

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchParameterTuningRunSubgraphState,
            input_schema=DispatchParameterTuningRunSubgraphInputState,
            output_schema=DispatchParameterTuningRunSubgraphOutputState,
        )
        graph_builder.add_node("dispatch_parameter_tuning_run", self._dispatch)
        graph_builder.add_edge(START, "dispatch_parameter_tuning_run")
        graph_builder.add_edge("dispatch_parameter_tuning_run", END)
        return graph_builder.compile()
