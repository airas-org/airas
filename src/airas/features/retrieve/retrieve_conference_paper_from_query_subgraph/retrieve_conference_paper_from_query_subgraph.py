import json
import logging
import operator
import os
import shutil
from typing import Annotated, Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.retrieve.nodes.extract_github_url_from_text import (
    extract_github_url_from_text,
)
from airas.features.retrieve.nodes.get_paper_title_from_airas_db import (
    get_paper_title_from_airas_db,
)
from airas.features.retrieve.nodes.retrieve_arxiv_text_from_url import (
    retrieve_arxiv_text_from_url,
)
from airas.features.retrieve.nodes.search_arxiv import (
    search_arxiv,
)
from airas.features.retrieve.nodes.select_best_paper import (
    select_best_paper,
)
from airas.features.retrieve.nodes.summarize_paper import (
    summarize_paper,
)
from airas.features.retrieve.prompt.extract_github_url_prompt import (
    extract_github_url_from_text_prompt,
)
from airas.features.retrieve.prompt.select_best_paper_prompt import (
    select_base_paper_prompt,
)
from airas.features.retrieve.prompt.summarize_paper_prompt import (
    summarize_paper_prompt,
)
from airas.features.retrieve.retrieve_conference_paper_from_query_subgraph.input_data import (
    retrieve_paper_from_query_subgraph_input_data,
)
from airas.types.paper import CandidatePaperInfo
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

retrieve_str = "retrieve_paper_from_query_subgraph"
retrieve_paper_from_query_timed = lambda f: time_node(retrieve_str)(f)  # noqa: E731


class RetrieveConferencePaperFromQueryInputState(TypedDict):
    base_queries: list[str]


class RetrieveConferencePaperFromQueryHiddenState(TypedDict):
    extracted_paper_titles: list[str]
    search_paper_list: list[dict]
    search_paper_count: int
    paper_full_text: str
    github_url: str
    process_index: int
    candidate_base_papers_info_list: Annotated[list[CandidatePaperInfo], operator.add]
    selected_base_paper_arxiv_id: str
    selected_base_paper_info: CandidatePaperInfo


class RetrieveConferencePaperFromQueryOutputState(TypedDict):
    base_github_url: str
    base_method_text: CandidatePaperInfo


class RetrieveConferencePaperFromQueryState(
    RetrieveConferencePaperFromQueryInputState,
    RetrieveConferencePaperFromQueryHiddenState,
    RetrieveConferencePaperFromQueryOutputState,
    ExecutionTimeState,
):
    pass


class RetrieveConferencePaperFromQuerySubgraph(BaseSubgraph):
    InputState = RetrieveConferencePaperFromQueryInputState
    OutputState = RetrieveConferencePaperFromQueryOutputState

    def __init__(
        self,
        llm_name: str,
        save_dir: str,
        arxiv_query_batch_size: int = 10,
        arxiv_num_retrieve_paper: int = 1,
        arxiv_period_days: int | None = None,
    ):
        self.llm_name = llm_name
        self.save_dir = save_dir
        self.arxiv_query_batch_size = arxiv_query_batch_size
        self.arxiv_num_retrieve_paper = arxiv_num_retrieve_paper
        self.arxiv_period_days = arxiv_period_days

        self.papers_dir = os.path.join(self.save_dir, "papers")
        self.selected_papers_dir = os.path.join(self.save_dir, "selected_papers")
        os.makedirs(self.papers_dir, exist_ok=True)
        os.makedirs(self.selected_papers_dir, exist_ok=True)
        check_api_key(
            llm_api_key_check=True,
            fire_crawl_api_key_check=True,
        )

    def _initialize_state(
        self, state: RetrieveConferencePaperFromQueryState
    ) -> dict[str, list[str] | list[CandidatePaperInfo] | int]:
        return {
            "base_queries": state["base_queries"],
            "process_index": 0,
            "candidate_base_papers_info_list": [],
        }

    @retrieve_paper_from_query_timed
    def _get_paper_title_from_airas_db(
        self, state: RetrieveConferencePaperFromQueryState
    ) -> dict[str, list[str]]:
        extracted_paper_titles = get_paper_title_from_airas_db(
            queries=state["base_queries"],
        )
        return {"extracted_paper_titles": extracted_paper_titles}

    def _check_extracted_titles(
        self, state: RetrieveConferencePaperFromQueryState
    ) -> str:
        logger.info("check_extracted_titles")
        if not state.get("extracted_paper_titles"):
            return "Stop"
        return "Continue"

    @retrieve_paper_from_query_timed
    def _search_arxiv_node(
        self, state: RetrieveConferencePaperFromQueryState
    ) -> dict[str, list[dict[Any, Any]] | int]:
        extract_paper_titles = state["extracted_paper_titles"]
        if not extract_paper_titles:
            return {
                "search_paper_list": [],
                "search_paper_count": 0,
            }
        batch_paper_titles = extract_paper_titles[
            : min(len(extract_paper_titles), self.arxiv_query_batch_size)
        ]
        search_paper_list = search_arxiv(
            queries=batch_paper_titles,
            num_retrieve_paper=self.arxiv_num_retrieve_paper,
        )
        return {
            "search_paper_list": search_paper_list,
            "search_paper_count": len(search_paper_list),
        }

    @retrieve_paper_from_query_timed
    def _retrieve_arxiv_text_from_url_node(
        self, state: RetrieveConferencePaperFromQueryState
    ) -> dict[str, str]:
        process_index = state["process_index"]
        logger.info(f"process_index: {process_index}")
        paper_info = state["search_paper_list"][process_index]
        paper_full_text = retrieve_arxiv_text_from_url(
            papers_dir=self.papers_dir, arxiv_url=paper_info["arxiv_url"]
        )
        return {"paper_full_text": paper_full_text}

    @retrieve_paper_from_query_timed
    def _extract_github_url_from_text_node(
        self, state: RetrieveConferencePaperFromQueryState
    ) -> dict[str, str | int]:
        paper_full_text = state["paper_full_text"]
        process_index = state["process_index"]
        paper_summary = state["search_paper_list"][process_index]["summary"]
        github_url = extract_github_url_from_text(
            text=paper_full_text,
            paper_summary=paper_summary,
            llm_name="gemini-2.0-flash-001",
            prompt_template=extract_github_url_from_text_prompt,
        )
        # GitHub URLが取得できなかった場合は次の論文を処理するためにProcess Indexを進める
        process_index = process_index + 1 if github_url == "" else process_index
        return {"github_url": github_url, "process_index": process_index}

    def _check_github_urls(self, state: RetrieveConferencePaperFromQueryState) -> str:
        if state["github_url"] == "":
            if state["process_index"] < state["search_paper_count"]:
                return "Next paper"
            return "All complete"
        else:
            return "Generate paper summary"

    @retrieve_paper_from_query_timed
    def _summarize_paper_node(
        self, state: RetrieveConferencePaperFromQueryState
    ) -> dict[str, list[CandidatePaperInfo] | int]:
        process_index = state["process_index"]
        (
            main_contributions,
            methodology,
            experimental_setup,
            limitations,
            future_research_directions,
        ) = summarize_paper(
            llm_name="gemini-2.0-flash-001",
            prompt_template=summarize_paper_prompt,
            paper_text=state["paper_full_text"],
        )

        paper_info = state["search_paper_list"][process_index]
        candidate_papers_info = {
            "arxiv_id": paper_info["arxiv_id"],
            "arxiv_url": paper_info["arxiv_url"],
            "title": paper_info.get("title", ""),
            "authors": paper_info.get("authors", ""),
            "published_date": paper_info.get("published_date", ""),
            "journal": paper_info.get("journal", ""),
            "doi": paper_info.get("doi", ""),
            "summary": paper_info.get("summary", ""),
            "github_url": state["github_url"],
            "main_contributions": main_contributions,
            "methodology": methodology,
            "experimental_setup": experimental_setup,
            "limitations": limitations,
            "future_research_directions": future_research_directions,
        }
        return {
            "process_index": process_index + 1,
            "candidate_base_papers_info_list": [
                CandidatePaperInfo(**candidate_papers_info)
            ],
        }

    def _check_paper_count(self, state: RetrieveConferencePaperFromQueryState) -> str:
        if state["process_index"] < state["search_paper_count"]:
            return "Next paper"
        return "All complete"

    @retrieve_paper_from_query_timed
    def _select_best_paper_node(
        self, state: RetrieveConferencePaperFromQueryState
    ) -> dict[str, str | CandidatePaperInfo | None]:
        candidate_papers_info_list = state["candidate_base_papers_info_list"]
        # TODO:論文の検索数の制御がうまくいっていない気がする
        selected_arxiv_ids = select_best_paper(
            llm_name="gemini-2.0-flash-001",
            prompt_template=select_base_paper_prompt,
            candidate_papers=candidate_papers_info_list,
        )

        # 選択された論文の情報を取得
        selected_arxiv_id = selected_arxiv_ids[0]
        selected_paper_info = next(
            (
                paper_info
                for paper_info in candidate_papers_info_list
                if paper_info["arxiv_id"] == selected_arxiv_id
            ),
            None,
        )
        # 選択された論文を別のディレクトリにコピーする
        for ext in ["txt", "pdf"]:
            source_path = os.path.join(self.papers_dir, f"{selected_arxiv_id}.{ext}")
            if os.path.exists(source_path):
                shutil.copy(
                    source_path,
                    os.path.join(
                        self.selected_papers_dir, f"{selected_arxiv_id}.{ext}"
                    ),
                )
        return {
            "selected_base_paper_arxiv_id": selected_arxiv_id,
            "selected_base_paper_info": selected_paper_info,
        }

    def _prepare_state(
        self, state: RetrieveConferencePaperFromQueryState
    ) -> dict[str, str | CandidatePaperInfo]:
        select_base_paper_info = state["selected_base_paper_info"]
        return {
            "base_github_url": select_base_paper_info["github_url"],
            "base_method_text": select_base_paper_info,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(RetrieveConferencePaperFromQueryState)

        graph_builder.add_node("initialize_state", self._initialize_state)
        graph_builder.add_node(
            "get_paper_title_from_airas_db",
            self._get_paper_title_from_airas_db,
        )
        graph_builder.add_node(
            "search_arxiv_node", self._search_arxiv_node
        )  # TODO: 検索結果が空ならEND
        graph_builder.add_node(
            "retrieve_arxiv_text_from_url_node", self._retrieve_arxiv_text_from_url_node
        )
        graph_builder.add_node(
            "extract_github_url_from_text_node", self._extract_github_url_from_text_node
        )
        graph_builder.add_node("summarize_paper_node", self._summarize_paper_node)
        graph_builder.add_node("select_best_paper_node", self._select_best_paper_node)
        graph_builder.add_node("prepare_state", self._prepare_state)

        graph_builder.add_edge(START, "initialize_state")
        graph_builder.add_edge("initialize_state", "get_paper_title_from_airas_db")
        graph_builder.add_conditional_edges(
            source="get_paper_title_from_airas_db",
            path=self._check_extracted_titles,
            path_map={
                "Stop": END,
                "Continue": "search_arxiv_node",
            },
        )
        graph_builder.add_edge("search_arxiv_node", "retrieve_arxiv_text_from_url_node")
        graph_builder.add_edge(
            "retrieve_arxiv_text_from_url_node", "extract_github_url_from_text_node"
        )
        graph_builder.add_conditional_edges(
            source="extract_github_url_from_text_node",
            path=self._check_github_urls,
            path_map={
                "Next paper": "retrieve_arxiv_text_from_url_node",
                "Generate paper summary": "summarize_paper_node",
                "All complete": "select_best_paper_node",
            },
        )
        graph_builder.add_conditional_edges(
            source="summarize_paper_node",
            path=self._check_paper_count,
            path_map={
                "Next paper": "retrieve_arxiv_text_from_url_node",
                "All complete": "select_best_paper_node",
            },
        )
        graph_builder.add_edge("select_best_paper_node", "prepare_state")
        graph_builder.add_edge("prepare_state", END)
        return graph_builder.compile()


def main():
    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/airas/data"
    input = retrieve_paper_from_query_subgraph_input_data

    import time

    start_time = time.perf_counter()
    result = RetrieveConferencePaperFromQuerySubgraph(
        llm_name=llm_name,
        save_dir=save_dir,
    ).run(input)
    print(f"result: {json.dumps(result, indent=2)}")

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    print(f"Execution time: {elapsed_time:.4f} seconds")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
