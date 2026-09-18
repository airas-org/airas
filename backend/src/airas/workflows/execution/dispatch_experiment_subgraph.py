from typing import Any

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.types.github import GitHubConfig
from airas.core.types.run_stage import RunStage
from airas.infra.github_client import GithubClient
from airas.infra.seyval_client import SeyvalClient
from airas.usecases.execution.dispatch_experiment import Backend, dispatch_experiment


class DispatchExperimentSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    run_id: str


class DispatchExperimentSubgraphOutputState(ExecutionTimeState):
    dispatched: bool
    execution_id: str | None
    execution_url: str | None


class DispatchExperimentSubgraphState(
    DispatchExperimentSubgraphInputState,
    DispatchExperimentSubgraphOutputState,
    total=False,
):
    pass


class DispatchExperimentSubgraph:
    """`dispatch_experiment` as one graph node, for the fixed workflows."""

    def __init__(
        self,
        backend: Backend,
        github_client: GithubClient,
        seyval_client: SeyvalClient | None = None,
        run_stage: RunStage | None = None,
        **options: Any,
    ):
        if backend == "seyval" and seyval_client is None:
            raise ValueError('backend="seyval" needs a seyval_client')
        self.backend = backend
        self.github_client = github_client
        self.seyval_client = seyval_client
        self.run_stage = run_stage or RunStage.SANITY
        self.options = options

    @time_node("dispatch_experiment_subgraph")
    async def _dispatch(self, state: DispatchExperimentSubgraphState) -> dict[str, Any]:
        return await dispatch_experiment(
            state["github_config"],
            state["run_id"],
            backend=self.backend,
            github_client=self.github_client,
            seyval_client=self.seyval_client,
            run_stage=self.run_stage,
            **self.options,
        )

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchExperimentSubgraphState,
            input_schema=DispatchExperimentSubgraphInputState,
            output_schema=DispatchExperimentSubgraphOutputState,
        )
        graph_builder.add_node("dispatch_experiment", self._dispatch)
        graph_builder.add_edge(START, "dispatch_experiment")
        graph_builder.add_edge("dispatch_experiment", END)
        return graph_builder.compile()
