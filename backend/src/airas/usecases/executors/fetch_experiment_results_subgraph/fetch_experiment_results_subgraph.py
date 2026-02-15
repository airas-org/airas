import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.executors.fetch_experiment_results_subgraph.nodes.fetch_results import (
    fetch_results,
)
from airas.usecases.executors.nodes.read_run_ids import read_run_ids_from_repository

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("fetch_experiment_results_subgraph")(f)  # noqa: E731


class FetchExperimentResultsSubgraphInputState(TypedDict):
    github_config: GitHubConfig


class FetchExperimentResultsSubgraphOutputState(ExecutionTimeState, total=False):
    experimental_results: ExperimentalResults


class FetchExperimentResultsSubgraphState(
    FetchExperimentResultsSubgraphInputState,
    FetchExperimentResultsSubgraphOutputState,
    total=False,
):
    run_ids: list[str]


class FetchExperimentResultsSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
    ):
        self.github_client = github_client

    @record_execution_time
    async def _read_run_ids(
        self, state: FetchExperimentResultsSubgraphState
    ) -> dict[str, list[str]]:
        run_ids = await read_run_ids_from_repository(
            self.github_client,
            state["github_config"],
        )
        return {"run_ids": run_ids}

    @record_execution_time
    async def _fetch_results(
        self, state: FetchExperimentResultsSubgraphState
    ) -> dict[str, ExperimentalResults]:
        if not (run_ids := state.get("run_ids")):
            logger.error("No run_ids found in state")
            return {"experimental_results": ExperimentalResults()}

        github_config = state["github_config"]

        logger.info(f"Retrieving results for {len(run_ids)} run_ids")

        experimental_results = await fetch_results(
            self.github_client,
            github_config,
            run_ids,
        )

        return {"experimental_results": experimental_results}

    def build_graph(self):
        graph_builder = StateGraph(
            FetchExperimentResultsSubgraphState,
            input_schema=FetchExperimentResultsSubgraphInputState,
            output_schema=FetchExperimentResultsSubgraphOutputState,
        )

        graph_builder.add_node("read_run_ids", self._read_run_ids)
        graph_builder.add_node("fetch_results", self._fetch_results)

        graph_builder.add_edge(START, "read_run_ids")
        graph_builder.add_edge("read_run_ids", "fetch_results")
        graph_builder.add_edge("fetch_results", END)

        return graph_builder.compile()
