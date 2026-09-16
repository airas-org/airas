import logging
from operator import or_
from typing import Annotated, Callable, Coroutine

from langgraph.graph import END, START, StateGraph
from typing_extensions import Any, TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.paper_search import PaperSearchResult
from airas.infra.arxiv_client import ArxivClient
from airas.infra.openalex_client import OpenAlexClient
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.usecases.literature.search_airas_records import (
    AirasRecordsIndex,
    search_airas_records,
)
from airas.usecases.literature.search_papers import merge_results
from airas.usecases.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
)
from airas.usecases.retrieve.search_papers_subgraph.nodes.search_airas_db import (
    search_airas_db,
)
from airas.usecases.retrieve.search_papers_subgraph.nodes.search_arxiv import (
    search_arxiv,
)
from airas.usecases.retrieve.search_papers_subgraph.nodes.search_openalex import (
    search_openalex,
)
from airas.usecases.retrieve.search_papers_subgraph.nodes.search_semantic_scholar import (
    search_semantic_scholar,
)

setup_logging()
logger = logging.getLogger(__name__)

subgraph_name = "search_papers_subgraph"
record_execution_time = lambda f: time_node(subgraph_name)(f)  # noqa: E731


class SourceSearchOutput(TypedDict):
    papers: list[PaperSearchResult]
    error: str | None


class SearchPapersSubgraphInputState(TypedDict):
    query: str
    sources: list[str]
    max_results_per_source: int
    year: str | None
    # "keyword" (default) or "semantic". Semantic search is only supported by
    # OpenAlex (native AI-embedding search, requires OPENALEX_API_KEY).
    search_mode: str


class SearchPapersSubgraphOutputState(ExecutionTimeState):
    papers: list[PaperSearchResult]
    source_results: dict[str, int]
    search_errors: dict[str, str]


class SearchPapersSubgraphState(
    SearchPapersSubgraphInputState, SearchPapersSubgraphOutputState
):
    # Source nodes run in parallel; each merges its own entry into this dict.
    source_outputs: Annotated[dict[str, SourceSearchOutput], or_]


class SearchPapersSubgraph:
    """Search multiple paper sources in parallel and merge the results.

    Sources that raise are reported in `search_errors` without failing the
    whole search. Duplicates across sources are merged (DOI, then arXiv ID,
    then normalized title).
    """

    def __init__(
        self,
        openalex_client: OpenAlexClient,
        semantic_scholar_client: SemanticScholarClient,
        arxiv_client: ArxivClient,
        airas_db_search_index: AirasDbPaperSearchIndex,
        airas_records_index: AirasRecordsIndex | None = None,
    ):
        self.openalex_client = openalex_client
        self.semantic_scholar_client = semantic_scholar_client
        self.arxiv_client = arxiv_client
        self.airas_db_search_index = airas_db_search_index
        self.airas_records_index = airas_records_index

    async def _run_source(
        self,
        source: str,
        state: SearchPapersSubgraphState,
        search: Callable[..., Coroutine[Any, Any, list[PaperSearchResult]]],
    ) -> dict[str, dict[str, SourceSearchOutput]]:
        if source not in state["sources"]:
            return {}
        try:
            papers = await search(
                query=state["query"],
                max_results=state["max_results_per_source"],
                year=state.get("year"),
            )
            output = SourceSearchOutput(papers=papers, error=None)
        except Exception as e:
            logger.warning(f"Paper search failed for source '{source}': {e}")
            output = SourceSearchOutput(papers=[], error=str(e))
        return {"source_outputs": {source: output}}

    @record_execution_time
    async def _search_openalex(self, state: SearchPapersSubgraphState) -> dict:
        semantic = state.get("search_mode") == "semantic"
        return await self._run_source(
            "openalex",
            state,
            lambda **kwargs: search_openalex(
                self.openalex_client, semantic=semantic, **kwargs
            ),
        )

    @record_execution_time
    async def _search_semantic_scholar(self, state: SearchPapersSubgraphState) -> dict:
        return await self._run_source(
            "semantic_scholar",
            state,
            lambda **kwargs: search_semantic_scholar(
                self.semantic_scholar_client, **kwargs
            ),
        )

    @record_execution_time
    async def _search_arxiv(self, state: SearchPapersSubgraphState) -> dict:
        return await self._run_source(
            "arxiv",
            state,
            lambda **kwargs: search_arxiv(self.arxiv_client, **kwargs),
        )

    @record_execution_time
    async def _search_airas_db(self, state: SearchPapersSubgraphState) -> dict:
        return await self._run_source(
            "airas_db",
            state,
            lambda **kwargs: search_airas_db(self.airas_db_search_index, **kwargs),
        )

    @record_execution_time
    async def _search_airas_records(self, state: SearchPapersSubgraphState) -> dict:
        index = self.airas_records_index
        if index is None:
            if "airas_records" not in state["sources"]:
                return {}
            output = SourceSearchOutput(
                papers=[], error="airas_records index not configured for this path"
            )
            return {"source_outputs": {"airas_records": output}}
        return await self._run_source(
            "airas_records",
            state,
            lambda query, max_results, year: search_airas_records(
                index, query, max_results
            ),
        )

    @record_execution_time
    def _merge_results(self, state: SearchPapersSubgraphState) -> dict:
        return merge_results(dict(state.get("source_outputs", {})))

    def build_graph(self):
        graph_builder = StateGraph(
            SearchPapersSubgraphState,
            input_schema=SearchPapersSubgraphInputState,
            output_schema=SearchPapersSubgraphOutputState,
        )
        graph_builder.add_node("search_openalex", self._search_openalex)
        graph_builder.add_node("search_semantic_scholar", self._search_semantic_scholar)
        graph_builder.add_node("search_arxiv", self._search_arxiv)
        graph_builder.add_node("search_airas_db", self._search_airas_db)
        graph_builder.add_node("search_airas_records", self._search_airas_records)
        graph_builder.add_node("merge_results", self._merge_results)

        for node in (
            "search_openalex",
            "search_semantic_scholar",
            "search_arxiv",
            "search_airas_db",
            "search_airas_records",
        ):
            graph_builder.add_edge(START, node)
        graph_builder.add_edge(
            [
                "search_openalex",
                "search_semantic_scholar",
                "search_arxiv",
                "search_airas_db",
                "search_airas_records",
            ],
            "merge_results",
        )
        graph_builder.add_edge("merge_results", END)
        return graph_builder.compile()
