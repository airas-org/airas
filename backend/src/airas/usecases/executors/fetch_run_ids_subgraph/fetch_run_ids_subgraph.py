import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.executors.nodes.read_run_ids import read_run_ids_from_repository

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("fetch_run_ids_subgraph")(f)  # noqa: E731


class FetchRunIdsSubgraphInputState(TypedDict):
    github_config: GitHubConfig


class FetchRunIdsSubgraphOutputState(ExecutionTimeState):
    run_ids: list[str]


class FetchRunIdsSubgraphState(
    FetchRunIdsSubgraphInputState,
    FetchRunIdsSubgraphOutputState,
    total=False,
):
    pass


class FetchRunIdsSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
    ):
        self.github_client = github_client

    @record_execution_time
    async def _read_run_ids(
        self, state: FetchRunIdsSubgraphState
    ) -> dict[str, list[str]]:
        run_ids = await read_run_ids_from_repository(
            self.github_client,
            state["github_config"],
        )
        return {"run_ids": run_ids}

    def build_graph(self):
        graph_builder = StateGraph(
            FetchRunIdsSubgraphState,
            input_schema=FetchRunIdsSubgraphInputState,
            output_schema=FetchRunIdsSubgraphOutputState,
        )

        graph_builder.add_node("read_run_ids", self._read_run_ids)

        graph_builder.add_edge(START, "read_run_ids")
        graph_builder.add_edge("read_run_ids", END)

        return graph_builder.compile()
