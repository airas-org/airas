import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.features.retrieve.retrieve_paper_subgraph.nodes.extract_experimental_info import (
    extract_experimental_info,
)
from airas.features.retrieve.retrieve_paper_subgraph.nodes.extract_github_url_from_text import (
    extract_github_url_from_text,
)
from airas.features.retrieve.retrieve_paper_subgraph.nodes.extract_reference_titles import (
    extract_reference_titles,
)
from airas.features.retrieve.retrieve_paper_subgraph.nodes.filter_titles_by_queries import (
    filter_titles_by_queries,
)
from airas.features.retrieve.retrieve_paper_subgraph.nodes.get_paper_titles_from_airas_db import (
    get_paper_titles_from_airas_db,
)
from airas.features.retrieve.retrieve_paper_subgraph.nodes.retrieve_repository_contents import (
    retrieve_repository_contents_from_url_groups,
)
from airas.features.retrieve.retrieve_paper_subgraph.nodes.retrieve_text_from_url import (
    retrieve_text_from_url,
)
from airas.features.retrieve.retrieve_paper_subgraph.nodes.summarize_paper import (
    PaperSummary,
    summarize_paper,
)
from airas.features.retrieve.retrieve_paper_subgraph.prompt.extract_github_url_from_text_prompt import (
    extract_github_url_from_text_prompt,
)
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_study import LLMExtractedInfo, MetaData, ResearchStudy
from airas.utils.logging_utils import setup_logging
from src.airas.config.llm_config import DEFAULT_NODE_LLMS
from src.airas.features.retrieve.retrieve_paper_subgraph.nodes.search_arxiv_id_from_title import (
    search_arxiv_id_from_title,
)
from src.airas.features.retrieve.retrieve_paper_subgraph.nodes.search_arxiv_info_by_id import (
    search_arxiv_info_by_id,
)
from src.airas.features.retrieve.retrieve_paper_subgraph.prompt.openai_websearch_arxiv_ids_prompt import (
    openai_websearch_arxiv_ids_prompt,
)
from src.airas.features.retrieve.retrieve_paper_subgraph.prompt.summarize_paper_prompt import (
    summarize_paper_prompt,
)
from src.airas.services.api_client.arxiv_client import ArxivClient
from src.airas.types.arxiv import ArxivInfo
from src.airas.utils.execution_timers import ExecutionTimeState, time_node

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("retrieve_paper_subgraph")(f)  # noqa: E731


class RetrievePaperSubgraphLLMMapping(BaseModel):
    search_arxiv_id_from_title: LLM_MODEL = DEFAULT_NODE_LLMS[
        "search_arxiv_id_from_title"
    ]
    summarize_paper: LLM_MODEL = DEFAULT_NODE_LLMS["summarize_paper"]
    extract_github_url_from_text: LLM_MODEL = DEFAULT_NODE_LLMS[
        "extract_github_url_from_text"
    ]
    extract_experimental_info: LLM_MODEL = DEFAULT_NODE_LLMS[
        "extract_experimental_info"
    ]
    extract_reference_titles: LLM_MODEL = DEFAULT_NODE_LLMS["extract_reference_titles"]


class RetrievePaperSubgraphInputState(TypedDict, total=False):
    query_list: list[str]


class RetrievePaperSubgraphOutputState(ExecutionTimeState, total=False):
    research_study_list: list[list[ResearchStudy]]


class RetrievePaperSubgraphState(
    RetrievePaperSubgraphInputState,
    RetrievePaperSubgraphOutputState,
    total=False,
):
    all_papers: list[dict[str, Any]]
    retrieve_paper_title_list: list[list[str]]
    arxiv_id_list: list[list[str]]
    arxiv_info_list: list[list[ArxivInfo]]
    arxiv_full_text_list: list[list[str]]
    paper_summary_list: list[list[PaperSummary]]
    reference_title_list: list[list[list[str]]]
    github_url_list: list[list[str]]
    github_code_list: list[list[str]]
    experimental_info_list: list[list[str]]
    experimental_code_list: list[list[str]]


class RetrievePaperSubgraph:
    def __init__(
        self,
        llm_client: LLMFacadeClient,
        arxiv_client: ArxivClient,
        github_client: GithubClient,
        max_results_per_query: int = 3,
    ):
        self.llm_client = llm_client
        self.arxiv_client = arxiv_client
        self.github_client = github_client
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
            papers=state.get("all_papers", []),
            queries=state.get("query_list", []),
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
            retrieve_paper_title_list=state.get("retrieve_paper_title_list", []),
        )
        return {"arxiv_id_list": arxiv_id_list}

    @record_execution_time
    async def _search_arxiv_info_by_id(
        self, state: RetrievePaperSubgraphState
    ) -> RetrievePaperSubgraphState:
        arxiv_info_list = await search_arxiv_info_by_id(
            arxiv_id_list=state.get("arxiv_id_list", []),
            arxiv_client=self.arxiv_client,
        )
        return {"arxiv_info_list": arxiv_info_list}

    @record_execution_time
    async def _retrieve_text_from_url(
        self, state: RetrievePaperSubgraphState
    ) -> RetrievePaperSubgraphState:
        arxiv_full_text_list = await retrieve_text_from_url(
            arxiv_info_groups=state.get("arxiv_info_list", []),
        )
        return {"arxiv_full_text_list": arxiv_full_text_list}

    # @record_execution_time
    async def _summarize_paper(
        self, state: RetrievePaperSubgraphState
    ) -> RetrievePaperSubgraphState:
        paper_summary_list = await summarize_paper(
            llm_name=self.llm_mapping.summarize_paper,
            llm_client=self.llm_client,
            prompt_template=summarize_paper_prompt,
            arxiv_full_text_list=state.get("arxiv_full_text_list", []),
        )
        return {"paper_summary_list": paper_summary_list}

    @record_execution_time
    async def _extract_github_url_from_text(
        self, state: RetrievePaperSubgraphState
    ) -> RetrievePaperSubgraphState:
        github_url_list = await extract_github_url_from_text(
            llm_name=self.llm_mapping.extract_github_url_from_text,
            prompt_template=extract_github_url_from_text_prompt,
            arxiv_full_text_list=state.get("arxiv_full_text_list", []),
            paper_summary_list=state.get("paper_summary_list", []),
            llm_client=self.llm_client,
            github_client=self.github_client,
        )
        return {"github_url_list": github_url_list}

    @record_execution_time
    def _retrieve_repository_contents(
        self, state: RetrievePaperSubgraphState
    ) -> RetrievePaperSubgraphState:
        github_url_list = state.get("github_url_list")
        if github_url_list is None:
            raise ValueError(
                "github_url_list must exist in the state before retrieving repository contents."
            )
        github_code_list = retrieve_repository_contents_from_url_groups(
            github_url_list=github_url_list,
            github_client=self.github_client,
        )
        return {"github_code_list": github_code_list}

    @record_execution_time
    async def _extract_experimental_info(
        self, state: RetrievePaperSubgraphState
    ) -> RetrievePaperSubgraphState:
        paper_summary_list = state.get("paper_summary_list")
        github_code_list = state.get("github_code_list")
        if paper_summary_list is None or github_code_list is None:
            raise ValueError(
                "Both paper_summary_list and github_code_list must exist in the state before extracting experimental info."
            )

        (
            experimental_info_list,
            experimental_code_list,
        ) = await extract_experimental_info(
            llm_name=self.llm_mapping.extract_experimental_info,
            llm_client=self.llm_client,
            paper_summary_list=paper_summary_list,
            github_code_list=github_code_list,
        )
        return {
            "experimental_info_list": experimental_info_list,
            "experimental_code_list": experimental_code_list,
        }

    # @record_execution_time
    async def _extract_reference_titles(
        self, state: RetrievePaperSubgraphState
    ) -> RetrievePaperSubgraphState:
        reference_title_list = await extract_reference_titles(
            llm_name=self.llm_mapping.extract_reference_titles,
            llm_client=self.llm_client,
            arxiv_full_text_list=state.get("arxiv_full_text_list", []),
        )
        return {"reference_title_list": reference_title_list}

    @record_execution_time
    async def _formatted_output(
        self, state: RetrievePaperSubgraphState
    ) -> RetrievePaperSubgraphState:
        retrieve_paper_title_list = state.get("retrieve_paper_title_list", [])
        arxiv_info_list = state.get("arxiv_info_list", [])
        arxiv_full_text_list = state.get("arxiv_full_text_list", [])
        paper_summary_list = state.get("paper_summary_list", [])
        github_url_list = state.get("github_url_list", [])
        experimental_info_list = state.get("experimental_info_list", [])
        experimental_code_list = state.get("experimental_code_list", [])
        research_study_list: list[list[ResearchStudy]] = []
        for (
            title_group,
            full_text_group,
            arxiv_info_group,
            paper_summary_group,
            github_url_group,
            experimental_info_group,
            experimental_code_group,
        ) in zip(
            retrieve_paper_title_list,
            arxiv_full_text_list,
            arxiv_info_list,
            paper_summary_list,
            github_url_list,
            experimental_info_list,
            experimental_code_list,
            strict=True,
        ):
            research_study_group: list[ResearchStudy] = []
            for (
                title,
                full_text,
                arxiv_info,
                paper_summary,
                github_url,
                experimental_info,
                experimental_code,
            ) in zip(
                title_group,
                full_text_group,
                arxiv_info_group,
                paper_summary_group,
                github_url_group,
                experimental_info_group,
                experimental_code_group,
                strict=True,
            ):
                research_study_group.append(
                    ResearchStudy(
                        title=title,
                        full_text=full_text,
                        references={},
                        meta_data=MetaData(
                            arxiv_id=arxiv_info.id,
                            doi=arxiv_info.doi,
                            authors=arxiv_info.authors,
                            published_date=arxiv_info.published_date,
                            github_url=github_url,
                        ),
                        llm_extracted_info=LLMExtractedInfo(
                            main_contributions=paper_summary.main_contributions,
                            methodology=paper_summary.methodology,
                            experimental_setup=paper_summary.experimental_setup,
                            limitations=paper_summary.limitations,
                            future_research_directions=paper_summary.future_research_directions,
                            experimental_info=experimental_info,
                            experimental_code=experimental_code,
                        ),
                    )
                )
            research_study_list.append(research_study_group)
        return {"research_study_list": research_study_list}

    def build_graph(self):
        graph_builder = StateGraph(
            RetrievePaperSubgraphState,
            input_schema=RetrievePaperSubgraphInputState,
            output_schema=RetrievePaperSubgraphOutputState,
        )
        graph_builder.add_node(
            "get_paper_titles_from_airas_db", self._get_paper_titles_from_airas_db
        )
        graph_builder.add_node(
            "filter_titles_by_queries", self._filter_titles_by_queries
        )
        graph_builder.add_node(
            "search_arxiv_id_from_title", self._search_arxiv_id_from_title
        )
        graph_builder.add_node("search_arxiv_info_by_id", self._search_arxiv_info_by_id)
        graph_builder.add_node("retrieve_text_from_url", self._retrieve_text_from_url)
        graph_builder.add_node("summarize_paper", self._summarize_paper)
        graph_builder.add_node(
            "extract_reference_titles", self._extract_reference_titles
        )
        graph_builder.add_node(
            "extract_github_url_from_text", self._extract_github_url_from_text
        )
        graph_builder.add_node(
            "retrieve_repository_contents", self._retrieve_repository_contents
        )
        graph_builder.add_node(
            "extract_experimental_info", self._extract_experimental_info
        )
        graph_builder.add_node("formatted_output", self._formatted_output)
        graph_builder.add_edge(START, "get_paper_titles_from_airas_db")
        graph_builder.add_edge(
            "get_paper_titles_from_airas_db", "filter_titles_by_queries"
        )
        graph_builder.add_edge("filter_titles_by_queries", "search_arxiv_id_from_title")
        graph_builder.add_edge("search_arxiv_id_from_title", "search_arxiv_info_by_id")
        graph_builder.add_edge("search_arxiv_info_by_id", "retrieve_text_from_url")
        graph_builder.add_edge("retrieve_text_from_url", "summarize_paper")
        graph_builder.add_edge("retrieve_text_from_url", "extract_reference_titles")
        graph_builder.add_edge("retrieve_text_from_url", "extract_github_url_from_text")
        graph_builder.add_edge(
            "extract_github_url_from_text", "retrieve_repository_contents"
        )
        graph_builder.add_edge(
            [
                "summarize_paper",
                "extract_reference_titles",
                "retrieve_repository_contents",
            ],
            "extract_experimental_info",
        )
        graph_builder.add_edge("extract_experimental_info", "formatted_output")
        graph_builder.add_edge("formatted_output", END)
        return graph_builder.compile()
