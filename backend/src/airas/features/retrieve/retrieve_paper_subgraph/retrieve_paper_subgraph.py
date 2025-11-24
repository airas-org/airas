import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.features.retrieve.get_paper_titles_subgraph.nodes.filter_titles_by_queries import (
    filter_titles_by_queries,
)
from airas.features.retrieve.get_paper_titles_subgraph.nodes.get_paper_titles_from_airas_db import (
    get_paper_titles_from_airas_db,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.prompt.openai_websearch_arxiv_ids_prompt import (
    openai_websearch_arxiv_ids_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.utils.logging_utils import setup_logging
from src.airas.config.llm_config import DEFAULT_NODE_LLMS
from src.airas.features.retrieve.retrieve_paper_content_subgraph.nodes.search_arxiv_by_id import (
    search_arxiv_by_id,
)
from src.airas.features.retrieve.retrieve_paper_content_subgraph.nodes.search_arxiv_id_from_title import (
    search_arxiv_id_from_title,
)
from src.airas.services.api_client.arxiv_client import ArxivClient
from src.airas.utils.execution_timers import ExecutionTimeState, time_node

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("retrieve_paper_subgraph")(f)  # noqa: E731


class RetrievePaperSubgraphLLMMapping(BaseModel):
    search_arxiv_id_from_title: LLM_MODEL = DEFAULT_NODE_LLMS[
        "search_arxiv_id_from_title"
    ]


class RetrievePaperSubgraphInputState(TypedDict, total=False):
    query_list: list[str]


class RetrievePaperSubgraphState(
    RetrievePaperSubgraphInputState,
    ExecutionTimeState,
    total=False,
):
    all_papers: list[dict[str, Any]]
    retrieve_paper_title_list: list[list[str]]
    arxiv_id_list: list[list[str]]
    arxiv_info_list: list[list[Any]]


class RetrievePaperSubgraph:
    def __init__(
        self,
        llm_client: LLMFacadeClient,
        arxiv_client: ArxivClient,
        max_results_per_query: int = 3,
    ):
        self.llm_client = llm_client
        self.arxiv_client = arxiv_client
        self.max_results_per_query = max_results_per_query
        self.llm_mapping = RetrievePaperSubgraphLLMMapping()

    @record_execution_time
    def _get_paper_titles_from_airas_db(
        self, state: RetrievePaperSubgraphState
    ) -> RetrievePaperSubgraphState:
        all_papers = get_paper_titles_from_airas_db()
        return {"all_papers": all_papers or []}

    @record_execution_time
    def _filter_titles_by_queries(
        self, state: RetrievePaperSubgraphState
    ) -> RetrievePaperSubgraphState:
        retrieve_paper_title_list = filter_titles_by_queries(
            papers=state["all_papers"],
            queries=state["query_list"],
            max_results_per_query=self.max_results_per_query,
        )
        return {"retrieve_paper_title_list": retrieve_paper_title_list}

    @record_execution_time
    async def _search_arxiv_id_from_title(
        self, state: RetrievePaperSubgraphState
    ) -> RetrievePaperSubgraphState:
        arxiv_id_list = await search_arxiv_id_from_title(
            llm_name=self.llm_mapping.search_arxiv_id_from_title,
            llm_client=self.llm_client,
            prompt_template=openai_websearch_arxiv_ids_prompt,
            retrieve_paper_title_list=state["retrieve_paper_title_list"],
        )
        return {"arxiv_id_list": arxiv_id_list}

    @record_execution_time
    def _search_arxiv_by_id(
        self, state: RetrievePaperSubgraphState
    ) -> RetrievePaperSubgraphState:
        arxiv_info_list = search_arxiv_by_id(
            arxiv_id_list=state["arxiv_id_list"], arxiv_client=self.arxiv_client
        )
        return {"arxiv_info_list": arxiv_info_list}

    def build_graph(self):
        graph_builder = StateGraph(RetrievePaperSubgraphState)
        graph_builder.add_node(
            "get_paper_titles_from_airas_db", self._get_paper_titles_from_airas_db
        )
        graph_builder.add_node(
            "filter_titles_by_queries", self._filter_titles_by_queries
        )
        graph_builder.add_node(
            "search_arxiv_id_from_title", self._search_arxiv_id_from_title
        )
        graph_builder.add_node("search_arxiv_by_id", self._search_arxiv_by_id)
        graph_builder.add_edge(START, "get_paper_titles_from_airas_db")
        graph_builder.add_edge(
            "get_paper_titles_from_airas_db", "filter_titles_by_queries"
        )
        graph_builder.add_edge("filter_titles_by_queries", "search_arxiv_id_from_title")
        graph_builder.add_edge("search_arxiv_id_from_title", "search_arxiv_by_id")
        graph_builder.add_edge("search_arxiv_by_id", END)
        return graph_builder.compile()
