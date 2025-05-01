import os
import shutil
import operator
import logging
from typing import Annotated, TypedDict, Optional

from langgraph.graph import START, END, StateGraph
from langgraph.graph.graph import CompiledGraph

from airas.utils.logging_utils import setup_logging

from airas.retrieve.retrieve_paper_subgraph.nodes.web_scrape_node import web_scrape_node
from airas.retrieve.retrieve_paper_subgraph.nodes.extract_paper_title_node import (
    extract_paper_title_node,
)
from airas.retrieve.retrieve_paper_subgraph.nodes.arxiv_api_node import ArxivNode
from airas.retrieve.retrieve_paper_subgraph.nodes.extract_github_url_node import (
    ExtractGithubUrlNode,
)
from airas.retrieve.retrieve_paper_subgraph.nodes.generate_queries_node import (
    generate_queries_node,
    generate_queries_prompt_add,
)
from airas.retrieve.retrieve_paper_subgraph.nodes.select_best_paper_node import (
    select_best_paper_node,
    select_base_paper_prompt,
    select_add_paper_prompt,
)
from airas.retrieve.retrieve_paper_subgraph.nodes.summarize_paper_node import (
    summarize_paper_node,
    summarize_paper_prompt_base,
)
from airas.retrieve.retrieve_paper_subgraph.nodes.retrieve_arxiv_text_node import (
    RetrievearXivTextNode,
)
from airas.utils.execution_timers import time_node, ExecutionTimeState
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph

setup_logging()
logger = logging.getLogger(__name__)


class CandidatePaperInfo(TypedDict):
    arxiv_id: str
    arxiv_url: str
    title: str
    authors: list[str]
    published_date: str
    journal: str
    doi: str
    summary: str
    # 途中で取得
    github_url: str
    # 最後のサマリーで取得
    main_contributions: str
    methodology: str
    experimental_setup: str
    limitations: str
    future_research_directions: str


class RetrievePaperInputState(TypedDict):
    queries: list


class RetrievePaperHiddenState(TypedDict):
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
    generated_queries: list[str]
    candidate_add_papers_info_list: Annotated[list[CandidatePaperInfo], operator.add]
    selected_add_paper_arxiv_ids: list[str]
    selected_add_paper_info_list: list[CandidatePaperInfo]


class RetrievePaperOutputState(TypedDict):
    base_github_url: str
    base_method_text: str
    add_github_urls: list[str]
    add_method_texts: list[str]


class RetrievePaperState(
    RetrievePaperInputState,
    RetrievePaperHiddenState,
    RetrievePaperOutputState,
    ExecutionTimeState,
):
    pass


class RetrievePaperSubgraph:
    def __init__(
        self,
        llm_name: str,
        save_dir: str,
        scrape_urls: list,
        arxiv_query_batch_size: int = 10,
        arxiv_num_retrieve_paper: int = 1,
        arxiv_period_days: Optional[int] = None,
        add_paper_num: int = 5,
    ):
        self.llm_name = llm_name
        self.save_dir = save_dir
        self.scrape_urls = scrape_urls
        self.arxiv_query_batch_size = arxiv_query_batch_size
        self.arxiv_num_retrieve_paper = arxiv_num_retrieve_paper
        self.arxiv_period_days = arxiv_period_days
        self.add_paper_num = add_paper_num
        self.papers_dir = os.path.join(self.save_dir, "papers")
        self.selected_papers_dir = os.path.join(self.save_dir, "selected_papers")
        os.makedirs(self.papers_dir, exist_ok=True)
        os.makedirs(self.selected_papers_dir, exist_ok=True)

    def _initialize_state(self, state: RetrievePaperState) -> dict:
        return {
            "queries": state["queries"],
            "process_index": 0,
            "candidate_base_papers_info_list": [],
            "candidate_add_papers_info_list": [],
        }

    @time_node("retrieve_paper_subgraph", "_base_web_scrape_node")
    def _base_web_scrape_node(self, state: RetrievePaperState) -> dict:
        scraped_results = web_scrape_node(
            queries=state["queries"],  # TODO: abstractもスクレイピングする
            scrape_urls=self.scrape_urls,
        )
        return {"scraped_results": scraped_results}

    @time_node("retrieve_paper_subgraph", "_extract_paper_title_node")
    def _extract_paper_title_node(self, state: RetrievePaperState) -> dict:
        extracted_paper_titles = extract_paper_title_node(
            llm_name="o3-mini-2025-01-31",
            queries=state["queries"],
            scraped_results=state["scraped_results"],
        )
        return {"extracted_paper_titles": extracted_paper_titles}

    def _check_extracted_titles(self, state: RetrievePaperState) -> str:
        logger.info("check_extracted_titles")
        if not state.get("extracted_paper_titles"):
            if "generated_queries" in state:
                return "Regenerate queries"
            else:
                return "Stop"
        else:
            return "Continue"

    @time_node("retrieve_paper_subgraph", "_search_arxiv_node")
    def _search_arxiv_node(self, state: RetrievePaperState) -> dict:
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

    @time_node("retrieve_paper_subgraph", "_retrieve_arxiv_full_text_node")
    def _retrieve_arxiv_full_text_node(self, state: RetrievePaperState) -> dict:
        process_index = state["process_index"]
        logger.info(f"process_index: {process_index}")
        paper_info = state["search_paper_list"][process_index]
        paper_full_text = RetrievearXivTextNode(papers_dir=self.papers_dir).execute(
            arxiv_url=paper_info["arxiv_url"]
        )
        return {"paper_full_text": paper_full_text}

    @time_node("retrieve_paper_subgraph", "_extract_github_url_node")
    def _extract_github_url_node(self, state: RetrievePaperState) -> dict:
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
        process_index = state["process_index"]
        if github_url == "":
            process_index += 1
        return {"github_url": github_url, "process_index": process_index}

    def _check_github_urls(self, state: RetrievePaperState) -> str:
        if state["github_url"] == "":
            if state["process_index"] < state["search_paper_count"]:
                return "Next paper"
            else:
                return "All complete"
        else:
            return "Generate paper summary"

    @time_node("retrieve_paper_subgraph", "_summarize_base_paper_node")
    def _summarize_base_paper_node(self, state: RetrievePaperState) -> dict:
        paper_full_text = state["paper_full_text"]
        (
            main_contributions,
            methodology,
            experimental_setup,
            limitations,
            future_research_directions,
        ) = summarize_paper_node(
            llm_name="gemini-2.0-flash-001",
            prompt_template=summarize_paper_prompt_base,
            paper_text=paper_full_text,
        )

        process_index = state["process_index"]
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

    def _check_paper_count(self, state: RetrievePaperState) -> str:
        if state["process_index"] < state["search_paper_count"]:
            return "Next paper"
        else:
            return "All complete"

    @time_node("retrieve_paper_subgraph", "_base_select_best_paper_node")
    def _base_select_best_paper_node(self, state: RetrievePaperState) -> dict:
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

    # add paper
    @time_node("retrieve_paper_subgraph", "_generate_queries_node")
    def _generate_queries_node(self, state: RetrievePaperState) -> dict:
        all_queries = (
            state["generated_queries"]
            if "generated_queries" in state
            else state["queries"]
        )
        selected_base_paper_info = state["selected_base_paper_info"]
        new_generated_queries = generate_queries_node(
            llm_name=self.llm_name,
            prompt_template=generate_queries_prompt_add,
            selected_base_paper_info=selected_base_paper_info,
            queries=all_queries,
        )
        updated_all_queries = all_queries + new_generated_queries

        return {
            "generated_queries": updated_all_queries,
            "process_index": 0,
        }

    @time_node("retrieve_paper_subgraph", "_add_web_scrape_node")
    def _add_web_scrape_node(self, state: RetrievePaperState) -> dict:
        scraped_results = web_scrape_node(
            queries=state["generated_queries"], scrape_urls=self.scrape_urls
        )
        return {"scraped_results": scraped_results}

    @time_node("retrieve_paper_subgraph", "_summarize_add_paper_node")
    def _summarize_add_paper_node(self, state: RetrievePaperState) -> dict:
        paper_full_text = state["paper_full_text"]
        (
            main_contributions,
            methodology,
            experimental_setup,
            limitations,
            future_research_directions,
        ) = summarize_paper_node(
            llm_name="gemini-2.0-flash-001",
            prompt_template=summarize_paper_prompt_base,
            paper_text=paper_full_text,
        )

        process_index = state["process_index"]
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
            "candidate_add_papers_info_list": [
                CandidatePaperInfo(**candidate_papers_info)
            ],
        }

    @time_node("retrieve_paper_subgraph", "_add_select_best_paper_node")
    def _add_select_best_paper_node(self, state: RetrievePaperState) -> dict:
        candidate_papers_info_list = state["candidate_add_papers_info_list"]
        base_arxiv_id = state["selected_base_paper_info"]["arxiv_id"]
        filtered_candidates = [
            paper_info
            for paper_info in candidate_papers_info_list
            if paper_info["arxiv_id"] != base_arxiv_id
        ]

        selected_arxiv_ids = select_best_paper_node(
            llm_name="gemini-2.0-flash-001",
            prompt_template=select_add_paper_prompt,
            candidate_papers=filtered_candidates,
            selected_base_paper_info=state["selected_base_paper_info"],
            add_paper_num=self.add_paper_num,
        )

        # 選択された論文の情報を取得
        selected_paper_info_list = [
            paper_info
            for paper_info in candidate_papers_info_list
            if paper_info["arxiv_id"] in selected_arxiv_ids
        ]
        # 選択された論文を別のディレクトリにコピーする
        for paper_info in selected_paper_info_list:
            for ext in ["txt", "pdf"]:
                source_path = os.path.join(
                    self.papers_dir, f"{paper_info['arxiv_id']}.{ext}"
                )
                if os.path.exists(source_path):
                    shutil.copy(
                        source_path,
                        os.path.join(
                            self.selected_papers_dir, f"{paper_info['arxiv_id']}.{ext}"
                        ),
                    )

        return {
            "selected_add_paper_arxiv_ids": selected_arxiv_ids,
            "selected_add_paper_info_list": selected_paper_info_list,
        }

    def _check_add_paper_count(self, state: RetrievePaperState) -> str:
        if len(state["selected_add_paper_arxiv_ids"]) < self.add_paper_num:
            return "Regenerate queries"
        else:
            return "Continue"

    def _prepare_state(self, state: RetrievePaperState) -> dict:
        base_github_url = state["selected_base_paper_info"]["github_url"]
        base_method_text = state["selected_base_paper_info"]
        add_github_urls = [
            paper_info["github_url"]
            for paper_info in state["selected_add_paper_info_list"]
        ]
        add_method_texts = [
            paper_info for paper_info in state["selected_add_paper_info_list"]
        ]

        return {
            "base_github_url": base_github_url,
            "base_method_text": base_method_text,
            "add_github_urls": add_github_urls,
            "add_method_texts": add_method_texts,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(RetrievePaperState)

        graph_builder.add_node("initialize_state", self._initialize_state)
        # base paper
        graph_builder.add_node("base_web_scrape_node", self._base_web_scrape_node)
        graph_builder.add_node(
            "base_extract_paper_title_node", self._extract_paper_title_node
        )
        graph_builder.add_node(
            "base_search_arxiv_node", self._search_arxiv_node
        )  # TODO: 検索結果が空ならEND
        graph_builder.add_node(
            "base_retrieve_arxiv_full_text_node", self._retrieve_arxiv_full_text_node
        )
        graph_builder.add_node(
            "base_extract_github_urls_node", self._extract_github_url_node
        )
        graph_builder.add_node(
            "base_summarize_paper_node", self._summarize_base_paper_node
        )
        graph_builder.add_node(
            "base_select_best_paper_node", self._base_select_best_paper_node
        )

        # add paper
        graph_builder.add_node("generate_queries_node", self._generate_queries_node)
        graph_builder.add_node("add_web_scrape_node", self._add_web_scrape_node)
        graph_builder.add_node(
            "add_extract_paper_title_node", self._extract_paper_title_node
        )
        graph_builder.add_node(
            "add_search_arxiv_node", self._search_arxiv_node
        )  # TODO: 検索結果が空ならEND
        graph_builder.add_node(
            "add_retrieve_arxiv_full_text_node", self._retrieve_arxiv_full_text_node
        )
        graph_builder.add_node(
            "add_extract_github_urls_node", self._extract_github_url_node
        )
        graph_builder.add_node(
            "add_summarize_paper_node", self._summarize_add_paper_node
        )
        graph_builder.add_node(
            "add_select_best_paper_node", self._add_select_best_paper_node
        )

        graph_builder.add_node("prepare_state", self._prepare_state)

        # make edges
        # base paper
        graph_builder.add_edge(START, "initialize_state")
        graph_builder.add_edge("initialize_state", "base_web_scrape_node")
        graph_builder.add_edge("base_web_scrape_node", "base_extract_paper_title_node")
        graph_builder.add_conditional_edges(
            "base_extract_paper_title_node",
            path=self._check_extracted_titles,
            path_map={
                "Stop": END,
                "Continue": "base_search_arxiv_node",
            },
        )
        graph_builder.add_edge(
            "base_search_arxiv_node", "base_retrieve_arxiv_full_text_node"
        )
        graph_builder.add_edge(
            "base_retrieve_arxiv_full_text_node", "base_extract_github_urls_node"
        )
        graph_builder.add_conditional_edges(
            "base_extract_github_urls_node",
            path=self._check_github_urls,
            path_map={
                "Next paper": "base_retrieve_arxiv_full_text_node",
                "Generate paper summary": "base_summarize_paper_node",
                "All complete": "base_select_best_paper_node",
            },
        )
        graph_builder.add_conditional_edges(
            "base_summarize_paper_node",
            path=self._check_paper_count,
            path_map={
                "Next paper": "base_retrieve_arxiv_full_text_node",
                "All complete": "base_select_best_paper_node",
            },
        )

        # add paper
        graph_builder.add_edge("base_select_best_paper_node", "generate_queries_node")
        graph_builder.add_edge("generate_queries_node", "add_web_scrape_node")
        graph_builder.add_edge("add_web_scrape_node", "add_extract_paper_title_node")
        graph_builder.add_conditional_edges(
            "add_extract_paper_title_node",
            path=self._check_extracted_titles,
            path_map={
                "Regenerate queries": "generate_queries_node",
                "Continue": "add_search_arxiv_node",
            },
        )
        graph_builder.add_edge(
            "add_search_arxiv_node", "add_retrieve_arxiv_full_text_node"
        )
        graph_builder.add_edge(
            "add_retrieve_arxiv_full_text_node", "add_extract_github_urls_node"
        )
        graph_builder.add_conditional_edges(
            "add_extract_github_urls_node",
            path=self._check_github_urls,
            path_map={
                "Next paper": "add_retrieve_arxiv_full_text_node",
                "Generate paper summary": "add_summarize_paper_node",
                "All complete": "add_select_best_paper_node",
            },
        )
        graph_builder.add_conditional_edges(
            "add_summarize_paper_node",
            path=self._check_paper_count,
            path_map={
                "Next paper": "add_retrieve_arxiv_full_text_node",
                "All complete": "add_select_best_paper_node",
            },
        )
        graph_builder.add_conditional_edges(
            "add_select_best_paper_node",
            path=self._check_add_paper_count,
            path_map={
                "Regenerate queries": "generate_queries_node",
                "Continue": "prepare_state",
            },
        )
        graph_builder.add_edge("prepare_state", END)

        return graph_builder.compile()


RetrievePaper = create_wrapped_subgraph(
    RetrievePaperSubgraph,
    RetrievePaperInputState,
    RetrievePaperOutputState,
)

if __name__ == "__main__":
    scrape_urls = [
        "https://icml.cc/virtual/2024/papers.html?filter=title",
        "https://iclr.cc/virtual/2024/papers.html?filter=title",
        # "https://nips.cc/virtual/2024/papers.html?filter=title",
        # "https://cvpr.thecvf.com/virtual/2024/papers.html?filter=title",
    ]
    add_paper_num = 1

    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/researchgraph/data"

    github_repository = "auto-res2/test-tanaka-2"
    branch_name = "test"
    input = {
        "queries": ["diffusion model"],
    }

    retriever = RetrievePaper(
        github_repository=github_repository,
        branch_name=branch_name,
        perform_download=False,
        llm_name=llm_name,
        save_dir=save_dir,
        scrape_urls=scrape_urls,
        add_paper_num=add_paper_num,
    )

    result = retriever.run(input)
    print(f"result: {result}")
