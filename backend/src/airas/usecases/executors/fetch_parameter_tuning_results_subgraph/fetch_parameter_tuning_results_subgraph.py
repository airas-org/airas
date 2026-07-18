import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.executors.fetch_parameter_tuning_results_subgraph.nodes.fetch_tuning_outputs import (
    fetch_tuning_outputs,
)

setup_logging()
logger = logging.getLogger(__name__)


def record_execution_time(f):
    return time_node("fetch_parameter_tuning_results_subgraph")(f)


class FetchParameterTuningResultsSubgraphInputState(TypedDict):
    github_config: GitHubConfig


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
    def __init__(self, github_client: GithubClient):
        self.github_client = github_client

    @record_execution_time
    async def _fetch_tuning_outputs(
        self, state: FetchParameterTuningResultsSubgraphState
    ) -> dict:
        try:
            outputs = await fetch_tuning_outputs(
                github_client=self.github_client,
                github_config=state["github_config"],
            )
        except Exception as exc:
            logger.warning("Failed to fetch tuning outputs: %s", exc)
            return {
                "result": None,
                "tuning_figure_png_base64": None,
                "final_status": {"status": "failed", "fetch_error": str(exc)},
            }

        result = outputs.get("result")
        if not isinstance(result, dict):
            return {
                "result": None,
                "tuning_figure_png_base64": outputs.get("tuning_figure_png_base64"),
                "final_status": {"status": "failed", "run_error": "result_missing"},
            }

        run_error = result.get("error")
        if run_error:
            return {
                "result": result,
                "tuning_figure_png_base64": outputs.get("tuning_figure_png_base64"),
                "final_status": {"status": "failed", "run_error": run_error},
            }

        return {
            "result": result,
            "tuning_figure_png_base64": outputs.get("tuning_figure_png_base64"),
            "final_status": {"status": "passed"},
        }

    def build_graph(self):
        graph_builder = StateGraph(
            FetchParameterTuningResultsSubgraphState,
            input_schema=FetchParameterTuningResultsSubgraphInputState,
            output_schema=FetchParameterTuningResultsSubgraphOutputState,
        )
        graph_builder.add_node("fetch_tuning_outputs", self._fetch_tuning_outputs)
        graph_builder.add_edge(START, "fetch_tuning_outputs")
        graph_builder.add_edge("fetch_tuning_outputs", END)
        return graph_builder.compile()
