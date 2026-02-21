import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.executors.fetch_experiment_code_subgraph.nodes.fetch_code import (
    fetch_experiment_code,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("fetch_experiment_code_subgraph")(f)  # noqa: E731


class FetchExperimentCodeSubgraphInputState(TypedDict):
    github_config: GitHubConfig


class FetchExperimentCodeSubgraphOutputState(ExecutionTimeState, total=False):
    experiment_code: ExperimentCode


class FetchExperimentCodeSubgraphState(
    FetchExperimentCodeSubgraphInputState,
    FetchExperimentCodeSubgraphOutputState,
    total=False,
):
    pass


class FetchExperimentCodeSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
    ):
        self.github_client = github_client

    @record_execution_time
    async def _fetch_code(
        self, state: FetchExperimentCodeSubgraphState
    ) -> dict[str, ExperimentCode]:
        github_config = state["github_config"]

        logger.info("Retrieving experiment code from repository")

        experiment_code = await fetch_experiment_code(
            self.github_client,
            github_config,
        )

        return {"experiment_code": experiment_code}

    def build_graph(self):
        graph_builder = StateGraph(
            FetchExperimentCodeSubgraphState,
            input_schema=FetchExperimentCodeSubgraphInputState,
            output_schema=FetchExperimentCodeSubgraphOutputState,
        )

        graph_builder.add_node("fetch_code", self._fetch_code)

        graph_builder.add_edge(START, "fetch_code")
        graph_builder.add_edge("fetch_code", END)

        return graph_builder.compile()
