from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.reproduction.fetch_parameter_tuning_results import (
    fetch_parameter_tuning_results,
)


class FetchParameterTuningResultsSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    repro_id: str


class FetchParameterTuningResultsSubgraphOutputState(ExecutionTimeState):
    result: dict | None
    tuning_figure_png_base64: str | None
    final_status: dict | None


class FetchParameterTuningResultsSubgraphState(
    FetchParameterTuningResultsSubgraphInputState,
    FetchParameterTuningResultsSubgraphOutputState,
    total=False,
):
    pass


class FetchParameterTuningResultsSubgraph:
    """`fetch_parameter_tuning_results` as one graph node."""

    def __init__(self, github_client: GithubClient):
        self.github_client = github_client

    @time_node("fetch_parameter_tuning_results_subgraph")
    async def _fetch(self, state: FetchParameterTuningResultsSubgraphState) -> dict:
        return await fetch_parameter_tuning_results(
            self.github_client, state["github_config"], state["repro_id"]
        )

    def build_graph(self):
        graph_builder = StateGraph(
            FetchParameterTuningResultsSubgraphState,
            input_schema=FetchParameterTuningResultsSubgraphInputState,
            output_schema=FetchParameterTuningResultsSubgraphOutputState,
        )
        graph_builder.add_node("fetch_tuning_outputs", self._fetch)
        graph_builder.add_edge(START, "fetch_tuning_outputs")
        graph_builder.add_edge("fetch_tuning_outputs", END)
        return graph_builder.compile()
