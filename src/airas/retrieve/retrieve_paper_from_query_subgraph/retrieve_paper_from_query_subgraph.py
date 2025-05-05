import os
import shutil
import operator
import argparse
import logging
from typing import Annotated, TypedDict, Any

from langgraph.graph import START, END, StateGraph
from langgraph.graph.graph import CompiledGraph

from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.web_scrape_node import (
    web_scrape_node,
)  # NOTE: `firecrawl_client.py`
from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.extract_paper_title_node import (
    extract_paper_title_node,
)
from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.arxiv_api_node import (
    ArxivNode,
)  # NOTE: `arxiv_client.py`
from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.extract_github_url_node import (
    ExtractGithubUrlNode,
)
from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.select_best_paper_node import (
    select_best_paper_node,
    select_base_paper_prompt,
)
from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.summarize_paper_node import (
    summarize_paper_node,
    summarize_paper_prompt_base,
)
from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.retrieve_arxiv_text_node import (
    RetrievearXivTextNode,
)

from airas.utils.check_api_key import check_api_key
from airas.utils.logging_utils import setup_logging
from airas.utils.execution_timers import time_node, ExecutionTimeState
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph

from airas.typing.paper import CandidatePaperInfo

setup_logging()
logger = logging.getLogger(__name__)


class RetrievePaperFromQueryInputState(TypedDict):
    base_queries: list[str]


class RetrievePaperFromQueryHiddenState(TypedDict):
    scraped_results: list[dict]
    extracted_paper_titles: list[str]
    search_paper_list: list[dict]
    search_paper_count: int
    paper_full_text: str
    github_url: str
    process_index: int
    candidate_base_papers_info_list: Annotated[list[CandidatePaperInfo], operator.add]
    selected_base_paper_arxiv_id: str
    selected_base_paper_info: CandidatePaperInfo


class RetrievePaperFromQueryOutputState(TypedDict):
    base_github_url: str
    base_method_text: CandidatePaperInfo


class RetrievePaperFromQueryState(
    RetrievePaperFromQueryInputState,
    RetrievePaperFromQueryHiddenState,
    RetrievePaperFromQueryOutputState,
    ExecutionTimeState,
):
    pass


class RetrievePaperFromQuerySubgraph:
    def __init__(
        self,
        llm_name: str,
        save_dir: str,
        scrape_urls: list,
        arxiv_query_batch_size: int = 10,
        arxiv_num_retrieve_paper: int = 1,
        arxiv_period_days: int | None = None,
    ):
        self.llm_name = llm_name
        self.save_dir = save_dir
        self.scrape_urls = scrape_urls
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
        self, state: RetrievePaperFromQueryState
    ) -> dict[str, list[str] | list[CandidatePaperInfo] | int]:
        return {
            "base_queries": state["base_queries"],
            "process_index": 0,
            "candidate_base_papers_info_list": [],
        }

    @time_node("retrieve_base_paper_subgraph", "_web_scrape_node")
    def _web_scrape_node(
        self, state: RetrievePaperFromQueryState
    ) -> dict[str, list[str]]:
        scraped_results = web_scrape_node(
            queries=state["base_queries"],  # TODO: abstractもスクレイピングする
            scrape_urls=self.scrape_urls,
        )
        return {"scraped_results": scraped_results}

    @time_node("retrieve_base_paper_subgraph", "_extract_paper_title_node")
    def _extract_paper_title_node(
        self, state: RetrievePaperFromQueryState
    ) -> dict[str, list[str]]:
        extracted_paper_titles = extract_paper_title_node(
            llm_name="o3-mini-2025-01-31",
            queries=state["base_queries"],
            scraped_results=state["scraped_results"],
        )
        return {"extracted_paper_titles": extracted_paper_titles}

    def _check_extracted_titles(self, state: RetrievePaperFromQueryState) -> str:
        logger.info("check_extracted_titles")
        if not state.get("extracted_paper_titles"):
            return "Stop"
        return "Continue"

    @time_node("retrieve_base_paper_subgraph", "_search_arxiv_node")
    def _search_arxiv_node(
        self, state: RetrievePaperFromQueryState
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
        search_paper_list = ArxivNode(
            num_retrieve_paper=self.arxiv_num_retrieve_paper,
        ).execute(queries=batch_paper_titles)
        return {
            "search_paper_list": search_paper_list,
            "search_paper_count": len(search_paper_list),
        }

    @time_node("retrieve_base_paper_subgraph", "_retrieve_arxiv_full_text_node")
    def _retrieve_arxiv_full_text_node(
        self, state: RetrievePaperFromQueryState
    ) -> dict[str, str]:
        process_index = state["process_index"]
        logger.info(f"process_index: {process_index}")
        paper_info = state["search_paper_list"][process_index]
        paper_full_text = RetrievearXivTextNode(papers_dir=self.papers_dir).execute(
            arxiv_url=paper_info["arxiv_url"]
        )
        return {"paper_full_text": paper_full_text}

    @time_node("retrieve_base_paper_subgraph", "_extract_github_url_node")
    def _extract_github_url_node(
        self, state: RetrievePaperFromQueryState
    ) -> dict[str, str | int]:
        paper_full_text = state["paper_full_text"]
        process_index = state["process_index"]
        paper_summary = state["search_paper_list"][process_index]["summary"]
        github_url = ExtractGithubUrlNode(
            llm_name="gemini-2.0-flash-001",
        ).execute(
            paper_full_text=paper_full_text,
            paper_summary=paper_summary,
        )
        # GitHub URLが取得できなかった場合は次の論文を処理するためにProcess Indexを進める
        process_index = process_index + 1 if github_url == "" else process_index
        return {"github_url": github_url, "process_index": process_index}

    def _check_github_urls(self, state: RetrievePaperFromQueryState) -> str:
        if state["github_url"] == "":
            if state["process_index"] < state["search_paper_count"]:
                return "Next paper"
            return "All complete"
        else:
            return "Generate paper summary"

    @time_node("retrieve_base_paper_subgraph", "_summarize_base_paper_node")
    def _summarize_paper_node(
        self, state: RetrievePaperFromQueryState
    ) -> dict[str, list[CandidatePaperInfo] | int]:
        process_index = state["process_index"]
        (
            main_contributions,
            methodology,
            experimental_setup,
            limitations,
            future_research_directions,
        ) = summarize_paper_node(
            llm_name="gemini-2.0-flash-001",
            prompt_template=summarize_paper_prompt_base,
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

    def _check_paper_count(self, state: RetrievePaperFromQueryState) -> str:
        if state["process_index"] < state["search_paper_count"]:
            return "Next paper"
        return "All complete"

    @time_node("retrieve_base_paper_subgraph", "_base_select_best_paper_node")
    def _select_best_paper_node(
        self, state: RetrievePaperFromQueryState
    ) -> dict[str, str | CandidatePaperInfo | None]:
        candidate_papers_info_list = state["candidate_base_papers_info_list"]
        # TODO:論文の検索数の制御がうまくいっていない気がする
        selected_arxiv_ids = select_best_paper_node(
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
        self, state: RetrievePaperFromQueryState
    ) -> dict[str, str | CandidatePaperInfo]:
        select_base_paper_info = state["selected_base_paper_info"]
        return {
            "base_github_url": select_base_paper_info["github_url"],
            "base_method_text": select_base_paper_info,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(RetrievePaperFromQueryState)

        graph_builder.add_node("initialize_state", self._initialize_state)
        graph_builder.add_node("web_scrape_node", self._web_scrape_node)
        graph_builder.add_node(
            "extract_paper_title_node", self._extract_paper_title_node
        )
        graph_builder.add_node(
            "search_arxiv_node", self._search_arxiv_node
        )  # TODO: 検索結果が空ならEND
        graph_builder.add_node(
            "retrieve_arxiv_full_text_node", self._retrieve_arxiv_full_text_node
        )
        graph_builder.add_node(
            "extract_github_urls_node", self._extract_github_url_node
        )
        graph_builder.add_node("summarize_paper_node", self._summarize_paper_node)
        graph_builder.add_node("select_best_paper_node", self._select_best_paper_node)
        graph_builder.add_node("prepare_state", self._prepare_state)

        graph_builder.add_edge(START, "initialize_state")
        graph_builder.add_edge("initialize_state", "web_scrape_node")
        graph_builder.add_edge("web_scrape_node", "extract_paper_title_node")
        graph_builder.add_conditional_edges(
            source="extract_paper_title_node",
            path=self._check_extracted_titles,
            path_map={
                "Stop": END,
                "Continue": "search_arxiv_node",
            },
        )
        graph_builder.add_edge("search_arxiv_node", "retrieve_arxiv_full_text_node")
        graph_builder.add_edge(
            "retrieve_arxiv_full_text_node", "extract_github_urls_node"
        )
        graph_builder.add_conditional_edges(
            source="extract_github_urls_node",
            path=self._check_github_urls,
            path_map={
                "Next paper": "retrieve_arxiv_full_text_node",
                "Generate paper summary": "summarize_paper_node",
                "All complete": "select_best_paper_node",
            },
        )
        graph_builder.add_conditional_edges(
            source="summarize_paper_node",
            path=self._check_paper_count,
            path_map={
                "Next paper": "retrieve_arxiv_full_text_node",
                "All complete": "select_best_paper_node",
            },
        )
        graph_builder.add_edge("select_best_paper_node", "prepare_state")
        graph_builder.add_edge("prepare_state", END)
        return graph_builder.compile()


RetrievePaperFromQuery = create_wrapped_subgraph(
    RetrievePaperFromQuerySubgraph,
    RetrievePaperFromQueryInputState,
    RetrievePaperFromQueryOutputState,
)


def main():
    scrape_urls = [
        "https://icml.cc/virtual/2024/papers.html?filter=title",
        # "https://iclr.cc/virtual/2024/papers.html?filter=title",
        # "https://nips.cc/virtual/2024/papers.html?filter=title",
        # "https://cvpr.thecvf.com/virtual/2024/papers.html?filter=title",
    ]
    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/researchgraph/data"
    input = {
        "base_queries": ["transformer"],
    }

    parser = argparse.ArgumentParser(
        description="execute retrieve_paper_from_query_subgraph"
    )
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    base_paper_retriever = RetrievePaperFromQuery(
        github_repository=args.github_repository,
        branch_name=args.branch_name,
        perform_download=False,
        llm_name=llm_name,
        save_dir=save_dir,
        scrape_urls=scrape_urls,
    )

    result = base_paper_retriever.run(input)
    print(f"result: {result}")
    return


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
