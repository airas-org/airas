import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.core.types.arxiv import ArxivInfo
from airas.core.types.research_study import LLMExtractedInfo, MetaData, ResearchStudy
from airas.infra.arxiv_client import ArxivClient
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.extract_code_structure import (
    RepositoryCodeStructure,
    extract_repository_code_structure,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.extract_github_url_from_text import (
    extract_github_url_from_text,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.extract_reference_titles import (
    extract_reference_titles,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.retrieve_repository_contents import (
    RepositoryContents,
    retrieve_repository_contents_from_urls,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.retrieve_text_from_url import (
    retrieve_text_from_url,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.search_arxiv_id_from_title import (
    search_arxiv_id_from_title,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.search_arxiv_info_by_id import (
    search_arxiv_info_by_id,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.select_experimental_contents import (
    select_experimental_contents,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.summarize_paper import (
    PaperSummary,
    summarize_paper,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.prompt.extract_github_url_from_text_prompt import (
    extract_github_url_from_text_prompt,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.prompt.openai_websearch_arxiv_ids_prompt import (
    openai_websearch_arxiv_ids_prompt,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.prompt.select_experimental_files_prompt import (
    select_experimental_files_prompt,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.prompt.summarize_paper_prompt import (
    summarize_paper_prompt,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("retrieve_paper_subgraph")(f)  # noqa: E731


class RetrievePaperSubgraphLLMMapping(BaseModel):
    search_arxiv_id_from_title: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "search_arxiv_id_from_title"
    ]
    summarize_paper: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG["summarize_paper"]
    extract_github_url_from_text: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "extract_github_url_from_text"
    ]
    select_experimental_files: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "select_experimental_files"
    ]
    extract_reference_titles: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "extract_reference_titles"
    ]


class RetrievePaperSubgraphInputState(TypedDict):
    paper_titles: list[str]


class RetrievePaperSubgraphOutputState(ExecutionTimeState):
    research_study_list: list[ResearchStudy]


class RetrievePaperSubgraphState(
    RetrievePaperSubgraphInputState, RetrievePaperSubgraphOutputState
):
    arxiv_id_list: list[str]
    arxiv_info_list: list[ArxivInfo]
    arxiv_full_text_list: list[str]
    paper_summary_list: list[PaperSummary]
    reference_title_list: list[list[str]]
    github_url_list: list[str]
    repository_contents_list: list[RepositoryContents]
    repository_code_structure_list: list[RepositoryCodeStructure]
    experimental_info_list: list[str]
    experimental_code_list: list[str]


class RetrievePaperSubgraph:
    def __init__(
        self,
        langchain_client: LangChainClient,
        arxiv_client: ArxivClient,
        github_client: GithubClient,
        llm_mapping: RetrievePaperSubgraphLLMMapping | None = None,
    ):
        self.langchain_client = langchain_client
        self.arxiv_client = arxiv_client
        self.github_client = github_client
        self.llm_mapping = llm_mapping or RetrievePaperSubgraphLLMMapping()

    @record_execution_time
    async def _search_arxiv_id_from_title(
        self, state: RetrievePaperSubgraphState
    ) -> dict[str, list[str]]:
        arxiv_id_list = await search_arxiv_id_from_title(
            llm_config=self.llm_mapping.search_arxiv_id_from_title,
            llm_client=self.langchain_client,
            prompt_template=openai_websearch_arxiv_ids_prompt,
            paper_titles=state["paper_titles"],
        )
        return {"arxiv_id_list": arxiv_id_list}

    @record_execution_time
    async def _search_arxiv_info_by_id(
        self, state: RetrievePaperSubgraphState
    ) -> dict[str, list[ArxivInfo]]:
        arxiv_info_list = await search_arxiv_info_by_id(
            arxiv_id_list=state.get("arxiv_id_list", []),
            arxiv_client=self.arxiv_client,
        )
        return {"arxiv_info_list": arxiv_info_list}

    @record_execution_time
    async def _retrieve_text_from_url(
        self, state: RetrievePaperSubgraphState
    ) -> dict[str, list[str]]:
        arxiv_full_text_list = await retrieve_text_from_url(
            arxiv_info_list=state.get("arxiv_info_list", []),
        )
        return {"arxiv_full_text_list": arxiv_full_text_list}

    @record_execution_time
    async def _summarize_paper(
        self, state: RetrievePaperSubgraphState
    ) -> dict[str, list[PaperSummary]]:
        paper_summary_list = await summarize_paper(
            llm_config=self.llm_mapping.summarize_paper,
            llm_client=self.langchain_client,
            prompt_template=summarize_paper_prompt,
            arxiv_full_text_list=state.get("arxiv_full_text_list", []),
        )
        return {"paper_summary_list": paper_summary_list}

    @record_execution_time
    async def _extract_github_url_from_text(
        self, state: RetrievePaperSubgraphState
    ) -> dict[str, list[str]]:
        github_url_list = await extract_github_url_from_text(
            llm_config=self.llm_mapping.extract_github_url_from_text,
            prompt_template=extract_github_url_from_text_prompt,
            arxiv_full_text_list=state.get("arxiv_full_text_list", []),
            paper_summary_list=state.get("paper_summary_list", []),
            llm_client=self.langchain_client,
            github_client=self.github_client,
        )
        return {"github_url_list": github_url_list}

    @record_execution_time
    def _retrieve_repository_contents(
        self, state: RetrievePaperSubgraphState
    ) -> dict[str, list[RepositoryContents]]:
        github_url_list = state.get("github_url_list")
        if github_url_list is None:
            raise ValueError(
                "github_url_list must exist in the state before retrieving repository contents."
            )
        repository_contents_list = retrieve_repository_contents_from_urls(
            github_url_list=github_url_list,
            github_client=self.github_client,
        )
        return {"repository_contents_list": repository_contents_list}

    @record_execution_time
    def _extract_code_structure(
        self, state: RetrievePaperSubgraphState
    ) -> dict[str, list[RepositoryCodeStructure]]:
        repository_contents_list = state.get("repository_contents_list")
        if repository_contents_list is None:
            raise ValueError(
                "repository_contents_list must exist in the state before extracting code structure."
            )
        repository_code_structure_list = [
            extract_repository_code_structure(contents)
            for contents in repository_contents_list
        ]
        return {"repository_code_structure_list": repository_code_structure_list}

    @record_execution_time
    async def _select_experimental_contents(
        self, state: RetrievePaperSubgraphState
    ) -> dict[str, list[str]]:
        paper_summary_list = state.get("paper_summary_list")
        repository_contents_list = state.get("repository_contents_list")
        repository_code_structure_list = state.get("repository_code_structure_list")
        if (
            paper_summary_list is None
            or repository_contents_list is None
            or repository_code_structure_list is None
        ):
            raise ValueError(
                "paper_summary_list, repository_contents_list, and repository_code_structure_list must exist in the state before selecting experimental files."
            )

        (
            experimental_info_list,
            experimental_code_list,
        ) = await select_experimental_contents(
            llm_config=self.llm_mapping.select_experimental_files,
            llm_client=self.langchain_client,
            prompt_template=select_experimental_files_prompt,
            paper_summary_list=paper_summary_list,
            repository_contents_list=repository_contents_list,
            repository_code_structure_list=repository_code_structure_list,
        )
        return {
            "experimental_info_list": experimental_info_list,
            "experimental_code_list": experimental_code_list,
        }

    async def _extract_reference_titles(
        self, state: RetrievePaperSubgraphState
    ) -> dict[str, list[list[str]]]:
        reference_title_list = await extract_reference_titles(
            llm_config=self.llm_mapping.extract_reference_titles,
            llm_client=self.langchain_client,
            arxiv_full_text_list=state.get("arxiv_full_text_list", []),
        )
        return {"reference_title_list": reference_title_list}

    @record_execution_time
    async def _formatted_output(
        self, state: RetrievePaperSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        paper_titles = state.get("paper_titles", [])
        arxiv_full_text_list = state.get("arxiv_full_text_list", [])
        arxiv_info_list = state.get("arxiv_info_list", [])
        paper_summary_list = state.get("paper_summary_list", [])
        github_url_list = state.get("github_url_list", [])
        experimental_info_list = state.get("experimental_info_list", [])
        experimental_code_list = state.get("experimental_code_list", [])
        reference_title_list = state.get("reference_title_list", [])

        research_study_list: list[ResearchStudy] = []
        for (
            title,
            full_text,
            arxiv_info,
            paper_summary,
            github_url,
            experimental_info,
            experimental_code,
            reference_titles,
        ) in zip(
            paper_titles,
            arxiv_full_text_list,
            arxiv_info_list,
            paper_summary_list,
            github_url_list,
            experimental_info_list,
            experimental_code_list,
            reference_title_list,
            strict=True,
        ):
            research_study_list.append(
                ResearchStudy(
                    title=title,
                    full_text=full_text,
                    references=reference_titles,
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
        return {"research_study_list": research_study_list}

    def build_graph(self):
        graph_builder = StateGraph(
            RetrievePaperSubgraphState,
            input_schema=RetrievePaperSubgraphInputState,
            output_schema=RetrievePaperSubgraphOutputState,
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
        graph_builder.add_node("extract_code_structure", self._extract_code_structure)
        graph_builder.add_node(
            "select_experimental_contents", self._select_experimental_contents
        )
        graph_builder.add_node("formatted_output", self._formatted_output)
        graph_builder.add_edge(START, "search_arxiv_id_from_title")
        graph_builder.add_edge("search_arxiv_id_from_title", "search_arxiv_info_by_id")
        graph_builder.add_edge("search_arxiv_info_by_id", "retrieve_text_from_url")
        graph_builder.add_edge("retrieve_text_from_url", "summarize_paper")
        graph_builder.add_edge("retrieve_text_from_url", "extract_reference_titles")
        graph_builder.add_edge("retrieve_text_from_url", "extract_github_url_from_text")
        graph_builder.add_edge(
            "extract_github_url_from_text", "retrieve_repository_contents"
        )
        graph_builder.add_edge("retrieve_repository_contents", "extract_code_structure")
        graph_builder.add_edge(
            [
                "summarize_paper",
                "extract_reference_titles",
                "extract_code_structure",
            ],
            "select_experimental_contents",
        )
        graph_builder.add_edge("select_experimental_contents", "formatted_output")
        graph_builder.add_edge("formatted_output", END)
        return graph_builder.compile()
