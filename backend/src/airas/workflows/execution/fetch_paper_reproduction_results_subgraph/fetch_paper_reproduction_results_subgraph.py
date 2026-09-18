from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import NodeLLMConfig, require_llm_mapping
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.infra.litellm_client import LiteLLMClient
from airas.usecases.reproduction.fetch_paper_reproduction_results import (
    fetch_paper_reproduction_results,
)


class FetchPaperReproductionResultsLLMMapping(BaseModel):
    judge_reproduction: NodeLLMConfig


class FetchPaperReproductionResultsSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    repro_id: str


class FetchPaperReproductionResultsSubgraphOutputState(ExecutionTimeState):
    result: dict | None
    validation: dict | None
    parameter_check: dict | None
    final_status: dict | None
    repro_md: str | None
    repro_png_base64: str | None


class FetchPaperReproductionResultsSubgraphState(
    FetchPaperReproductionResultsSubgraphInputState,
    FetchPaperReproductionResultsSubgraphOutputState,
    total=False,
):
    pass


class FetchPaperReproductionResultsSubgraph:
    """`fetch_paper_reproduction_results` as one graph node."""

    def __init__(
        self,
        github_client: GithubClient,
        litellm_client: LiteLLMClient,
        llm_mapping: FetchPaperReproductionResultsLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.litellm_client = litellm_client
        self.llm_mapping = require_llm_mapping(llm_mapping)

    @time_node("fetch_paper_reproduction_results_subgraph")
    async def _fetch(self, state: FetchPaperReproductionResultsSubgraphState) -> dict:
        return await fetch_paper_reproduction_results(
            self.github_client,
            self.litellm_client,
            state["github_config"],
            state["repro_id"],
            self.llm_mapping.judge_reproduction,
        )

    def build_graph(self):
        graph_builder = StateGraph(
            FetchPaperReproductionResultsSubgraphState,
            input_schema=FetchPaperReproductionResultsSubgraphInputState,
            output_schema=FetchPaperReproductionResultsSubgraphOutputState,
        )
        graph_builder.add_node("fetch_paper_reproduction_results", self._fetch)
        graph_builder.add_edge(START, "fetch_paper_reproduction_results")
        graph_builder.add_edge("fetch_paper_reproduction_results", END)
        return graph_builder.compile()
