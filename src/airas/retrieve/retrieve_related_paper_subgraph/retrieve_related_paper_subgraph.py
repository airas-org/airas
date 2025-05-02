import os
import json
import shutil
import operator
import logging
from typing import Annotated, TypedDict
from pydantic import TypeAdapter

from langgraph.graph import START, END, StateGraph
from langgraph.graph.graph import CompiledGraph

from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.web_scrape_node import (
    web_scrape_node,
)  # NOTE: `firecrawl_client.py`を使用
from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.extract_paper_title_node import (
    extract_paper_title_node,
)
from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.arxiv_api_node import (
    ArxivNode,
)  # NOTE: `arxiv_client.py`を使用
from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.extract_github_url_node import (
    ExtractGithubUrlNode,
)
from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.generate_queries_node import (
    generate_queries_node,
)
from airas.retrieve.retrieve_related_paper_subgraph.prompt.generate_queries_node_prompt import (
    generate_queries_prompt,
)
from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.select_best_paper_node import (
    select_best_paper_node,
    select_add_paper_prompt,
)
from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.summarize_paper_node import (
    summarize_paper_node,
    summarize_paper_prompt_base,
)
from airas.retrieve.retrieve_paper_from_query_subgraph.nodes.retrieve_arxiv_text_node import (
    RetrievearXivTextNode,
)

from airas.utils.logging_utils import setup_logging
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import time_node, ExecutionTimeState
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph

from airas.typing.paper import CandidatePaperInfo

setup_logging()
logger = logging.getLogger(__name__)


class RetrieveRelatedPaperInputState(TypedDict):
    base_queries: list[str]
    base_github_url: str
    base_method_text: str
    add_queries: list[str] | None


class RetrieveRelatedPaperHiddenState(TypedDict):
    selected_base_paper_info: CandidatePaperInfo

    scraped_results: list[dict]
    extracted_paper_titles: list[str]
    search_paper_list: list[dict]
    search_paper_count: int
    paper_full_text: str
    github_url: str
    process_index: int
    candidate_add_papers_info_list: Annotated[list[CandidatePaperInfo], operator.add]
    selected_add_paper_arxiv_ids: list[str]
    selected_add_paper_info_list: list[CandidatePaperInfo]


class RetrieveRelatedPaperOutputState(TypedDict):
    generated_queries: list[str]
    add_github_urls: list[str]
    add_method_texts: list[str]


class RetrieveRelatedPaperState(
    RetrieveRelatedPaperInputState,
    RetrieveRelatedPaperHiddenState,
    RetrieveRelatedPaperOutputState,
    ExecutionTimeState,
):
    pass


class RetrieveRelatedPaperSubgraph:
    def __init__(
        self,
        llm_name: str,
        save_dir: str,
        scrape_urls: list,
        add_paper_num: int = 5,
        arxiv_query_batch_size: int = 10,
        arxiv_num_retrieve_paper: int = 1,
        arxiv_period_days: int | None = None,
    ):
        self.llm_name = llm_name
        self.save_dir = save_dir
        self.scrape_urls = scrape_urls
        self.add_paper_num = add_paper_num

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

    def _initialize_state(self, state: RetrieveRelatedPaperState) -> dict:
        selected_base_paper_info = json.loads(state["base_method_text"])
        selected_base_paper_info = TypeAdapter(CandidatePaperInfo).validate_python(
            selected_base_paper_info
        )
        return {
            "selected_base_paper_info": selected_base_paper_info,
            "generated_queries": [],
            "process_index": 0,
            "candidate_add_papers_info_list": [],
        }

    @time_node("retrieve_add_paper_subgraph", "_generate_queries_node")
    def _generate_queries_node(self, state: RetrieveRelatedPaperState) -> dict:
        add_queries = state.get("add_queries") or []
        all_queries = state["base_queries"] + add_queries + state["generated_queries"]
        new_generated_queries = generate_queries_node(
            llm_name=self.llm_name,
            prompt_template=generate_queries_prompt,
            selected_base_paper_info=state["selected_base_paper_info"],
            queries=all_queries,
        )
        return {
            "generated_queries": state["generated_queries"] + new_generated_queries,
            "process_index": 0,
        }

    @time_node("retrieve_add_paper_subgraph", "_web_scrape_node")
    def _web_scrape_node(self, state: RetrieveRelatedPaperState) -> dict:
        add_queries = state.get("add_queries") or []
        all_queries = state["base_queries"] + add_queries + state["generated_queries"]
        scraped_results = web_scrape_node(
            queries=all_queries,
            scrape_urls=self.scrape_urls,  # TODO: 2週目移行で無駄なクエリ検索が生じるため修正する
        )
        return {"scraped_results": scraped_results}

    @time_node("retrieve_add_paper_subgraph", "_extract_paper_title_node")
    def _extract_paper_title_node(self, state: RetrieveRelatedPaperState) -> dict:
        add_queries = state.get("add_queries") or []
        all_queries = state["base_queries"] + add_queries + state["generated_queries"]
        extracted_paper_titles = extract_paper_title_node(
            llm_name="o3-mini-2025-01-31",
            queries=all_queries,
            scraped_results=state["scraped_results"],
        )
        return {"extracted_paper_titles": extracted_paper_titles}

    def _check_extracted_titles(self, state: RetrieveRelatedPaperState) -> str:
        logger.info("check_extracted_titles")
        if not state.get("extracted_paper_titles"):
            return "Stop"
        return "Continue"

    @time_node("retrieve_add_paper_subgraph", "_search_arxiv_node")
    def _search_arxiv_node(self, state: RetrieveRelatedPaperState) -> dict:
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

    @time_node("retrieve_add_paper_subgraph", "_retrieve_arxiv_full_text_node")
    def _retrieve_arxiv_full_text_node(self, state: RetrieveRelatedPaperState) -> dict:
        process_index = state["process_index"]
        logger.info(f"process_index: {process_index}")
        paper_info = state["search_paper_list"][process_index]
        paper_full_text = RetrievearXivTextNode(papers_dir=self.papers_dir).execute(
            arxiv_url=paper_info["arxiv_url"]
        )
        return {"paper_full_text": paper_full_text}

    @time_node("retrieve_add_paper_subgraph", "_extract_github_url_node")
    def _extract_github_url_node(self, state: RetrieveRelatedPaperState) -> dict:
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

    def _check_github_urls(self, state: RetrieveRelatedPaperState) -> str:
        if state["github_url"] == "":
            if state["process_index"] < state["search_paper_count"]:
                return "Next paper"
            return "All complete"
        else:
            return "Generate paper summary"

    @time_node("retrieve_add_paper_subgraph", "_summarize_paper_node")
    def _summarize_paper_node(self, state: RetrieveRelatedPaperState) -> dict:
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

    def _check_paper_count(self, state: RetrieveRelatedPaperState) -> str:
        if state["process_index"] < state["search_paper_count"]:
            return "Next paper"
        return "All complete"

    @time_node("retrieve_add_paper_subgraph", "_select_best_paper_node")
    def _select_best_paper_node(self, state: RetrieveRelatedPaperState) -> dict:
        candidate_papers_info_list = state["candidate_add_papers_info_list"]
        base_arxiv_id = state["selected_base_paper_info"].arxiv_id
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
            if paper_info.arxiv_id in selected_arxiv_ids
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

    def _check_add_paper_count(self, state: RetrieveRelatedPaperState) -> str:
        if len(state["selected_add_paper_arxiv_ids"]) < self.add_paper_num:
            return "Regenerate queries"
        else:
            return "Continue"

    def _prepare_state(self, state: RetrieveRelatedPaperState) -> dict:
        add_github_urls = [
            paper_info["github_url"]
            for paper_info in state["selected_add_paper_info_list"]
        ]
        add_method_texts = [
            paper_info for paper_info in state["selected_add_paper_info_list"]
        ]

        return {
            "add_github_urls": add_github_urls,
            "add_method_texts": add_method_texts,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(RetrieveRelatedPaperState)

        graph_builder.add_node("initialize_state", self._initialize_state)
        graph_builder.add_node("generate_queries_node", self._generate_queries_node)
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
        graph_builder.add_edge("initialize_state", "generate_queries_node")
        graph_builder.add_edge("generate_queries_node", "web_scrape_node")
        graph_builder.add_edge("web_scrape_node", "extract_paper_title_node")
        graph_builder.add_conditional_edges(
            source="extract_paper_title_node",
            path=self._check_extracted_titles,
            path_map={
                "Regenerate queries": "generate_queries_node",
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
        graph_builder.add_conditional_edges(
            source="select_best_paper_node",
            path=self._check_add_paper_count,
            path_map={
                "Regenerate queries": "generate_queries_node",
                "Continue": "prepare_state",
            },
        )
        graph_builder.add_edge("prepare_state", END)

        return graph_builder.compile()


RetrieveRelatedPaper = create_wrapped_subgraph(
    RetrieveRelatedPaperSubgraph,
    RetrieveRelatedPaperInputState,
    RetrieveRelatedPaperOutputState,
)

if __name__ == "__main__":
    scrape_urls = [
        "https://icml.cc/virtual/2024/papers.html?filter=title",
        # "https://iclr.cc/virtual/2024/papers.html?filter=title",
        # "https://nips.cc/virtual/2024/papers.html?filter=title",
        # "https://cvpr.thecvf.com/virtual/2024/papers.html?filter=title",
    ]
    add_paper_num = 1

    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/researchgraph/data"

    github_repository = "auto-res2/experiment_script_matsuzawa"
    branch_name = "base-branch"
    input = {
        "add_queries": ["vision"],
    }

    add_paper_retriever = RetrieveRelatedPaper(
        github_repository=github_repository,
        branch_name=branch_name,
        llm_name=llm_name,
        save_dir=save_dir,
        scrape_urls=scrape_urls,
        add_paper_num=add_paper_num,
    )

    result = add_paper_retriever.run(input)
    print(f"result: {result}")
