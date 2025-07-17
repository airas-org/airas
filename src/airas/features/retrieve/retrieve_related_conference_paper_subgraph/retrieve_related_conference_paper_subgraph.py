import json
import logging
import operator
import os
import shutil
from typing import Annotated, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import TypeAdapter
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.retrieve.nodes.extract_github_url_from_text import (
    extract_github_url_from_text,
)
from airas.features.retrieve.nodes.generate_queries import (
    generate_queries,
)
from airas.features.retrieve.nodes.get_filtered_papers_from_conference import (
    get_filterd_papers_from_conference,
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
    select_related_paper_prompt,
)
from airas.features.retrieve.prompt.summarize_paper_prompt import (
    summarize_paper_prompt,
)
from airas.features.retrieve.retrieve_related_conference_paper_subgraph.input_data import (
    retrieve_related_paper_subgraph_input_data,
)
from airas.features.retrieve.retrieve_related_conference_paper_subgraph.prompt.generate_queries_prompt import (
    generate_queries_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.paper import CandidatePaperInfo
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

retrieve_str = "retrieve_paper_from_query_subgraph"
retrieve_paper_from_query_timed = lambda f: time_node(retrieve_str)(f)  # noqa: E731


class RetrieveRelatedConferencePaperInputState(TypedDict):
    base_queries: list[str]
    base_github_url: str
    base_method_text: CandidatePaperInfo
    add_queries: list[str] | None


class RetrieveRelatedConferencePaperHiddenState(TypedDict):
    selected_base_paper_info: CandidatePaperInfo

    extracted_paper_titles: list[str]
    search_paper_list: list[dict]
    search_paper_count: int
    paper_full_text: str
    github_url: str
    process_index: int
    candidate_add_papers_info_list: Annotated[list[CandidatePaperInfo], operator.add]
    selected_add_paper_arxiv_ids: list[str]
    selected_add_paper_info_list: list[CandidatePaperInfo]


class RetrieveRelatedConferencePaperOutputState(TypedDict):
    generated_queries: list[str]
    add_github_urls: list[str]
    add_method_texts: list[CandidatePaperInfo]


class RetrieveRelatedConferencePaperState(
    RetrieveRelatedConferencePaperInputState,
    RetrieveRelatedConferencePaperHiddenState,
    RetrieveRelatedConferencePaperOutputState,
    ExecutionTimeState,
):
    pass


class RetrieveRelatedConferencePaperSubgraph(BaseSubgraph):
    InputState = RetrieveRelatedConferencePaperInputState
    OutputState = RetrieveRelatedConferencePaperOutputState

    def __init__(
        self,
        llm_name: str,
        save_dir: str,
        paper_json_urls: list[str],
        add_paper_num: int = 5,
        n_query: int = 5,
        arxiv_query_batch_size: int = 10,
        arxiv_num_retrieve_paper: int = 1,
        arxiv_period_days: int | None = None,
    ):
        self.llm_name = llm_name
        self.save_dir = save_dir
        self.paper_json_urls = paper_json_urls
        self.add_paper_num = add_paper_num
        self.n_query = n_query

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

    def _initialize_state(self, state: RetrieveRelatedConferencePaperState) -> dict:
        # selected_base_paper_info = json.loads(state["base_method_text"])
        selected_base_paper_info = TypeAdapter(CandidatePaperInfo).validate_python(
            state["base_method_text"]
        )
        return {
            "selected_base_paper_info": selected_base_paper_info,
            "generated_queries": [],
            "process_index": 0,
            "candidate_add_papers_info_list": [],
        }

    @retrieve_paper_from_query_timed
    def _generate_queries_node(
        self, state: RetrieveRelatedConferencePaperState
    ) -> dict:
        add_queries = state.get("add_queries") or []
        all_queries = state["base_queries"] + add_queries + state["generated_queries"]
        new_generated_queries = generate_queries(
            llm_name=cast(LLM_MODEL, self.llm_name),
            prompt_template=generate_queries_prompt,
            paper_info=state["selected_base_paper_info"],
            n_queries=self.n_query,
            previous_queries=all_queries,
        )
        return {
            "generated_queries": state["generated_queries"] + new_generated_queries,
            "process_index": 0,
        }

    @retrieve_paper_from_query_timed
    def _get_filtered_papers_from_conference_node(
        self, state: RetrieveRelatedConferencePaperState
    ) -> dict[str, list[str]]:
        extracted_paper_titles = get_filterd_papers_from_conference(
            json_urls=self.paper_json_urls,
            queries=state["base_queries"],
        )
        return {"extracted_paper_titles": extracted_paper_titles}

    def _check_extracted_titles(
        self, state: RetrieveRelatedConferencePaperState
    ) -> str:
        logger.info("check_extracted_titles")
        if not state.get("extracted_paper_titles"):
            return "Regenerate queries"  # TODO: Add a state to loop count and define a "Stop" case
        return "Continue"

    @retrieve_paper_from_query_timed
    def _search_arxiv_node(self, state: RetrieveRelatedConferencePaperState) -> dict:
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
        self, state: RetrieveRelatedConferencePaperState
    ) -> dict:
        process_index = state["process_index"]
        logger.info(f"process_index: {process_index}")
        paper_info = state["search_paper_list"][process_index]
        paper_full_text = retrieve_arxiv_text_from_url(
            papers_dir=self.papers_dir, arxiv_url=paper_info["arxiv_url"]
        )
        return {"paper_full_text": paper_full_text}

    @retrieve_paper_from_query_timed
    def _extract_github_url_from_text_node(
        self, state: RetrieveRelatedConferencePaperState
    ) -> dict:
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

    def _check_github_urls(self, state: RetrieveRelatedConferencePaperState) -> str:
        if state["github_url"] == "":
            if state["process_index"] < state["search_paper_count"]:
                return "Next paper"
            return "All complete"
        else:
            return "Generate paper summary"

    @retrieve_paper_from_query_timed
    def _summarize_paper_node(self, state: RetrieveRelatedConferencePaperState) -> dict:
        paper_full_text = state["paper_full_text"]
        (
            main_contributions,
            methodology,
            experimental_setup,
            limitations,
            future_research_directions,
        ) = summarize_paper(
            llm_name="gemini-2.0-flash-001",
            prompt_template=summarize_paper_prompt,
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

    def _check_paper_count(self, state: RetrieveRelatedConferencePaperState) -> str:
        if state["process_index"] < state["search_paper_count"]:
            return "Next paper"
        return "All complete"

    @retrieve_paper_from_query_timed
    def _select_best_paper_node(
        self, state: RetrieveRelatedConferencePaperState
    ) -> dict:
        candidate_papers_info_list = state["candidate_add_papers_info_list"]
        base_arxiv_id = state["selected_base_paper_info"]["arxiv_id"]
        filtered_candidates = [
            paper_info
            for paper_info in candidate_papers_info_list
            if paper_info["arxiv_id"] != base_arxiv_id
        ]

        selected_arxiv_ids = select_best_paper(
            llm_name="gemini-2.0-flash-001",
            prompt_template=select_related_paper_prompt,
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

    def _check_add_paper_count(self, state: RetrieveRelatedConferencePaperState) -> str:
        if len(state["selected_add_paper_arxiv_ids"]) < self.add_paper_num:
            return "Regenerate queries"
        else:
            return "Continue"

    def _prepare_state(self, state: RetrieveRelatedConferencePaperState) -> dict:
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
        graph_builder = StateGraph(RetrieveRelatedConferencePaperState)

        graph_builder.add_node("initialize_state", self._initialize_state)
        graph_builder.add_node("generate_queries_node", self._generate_queries_node)
        graph_builder.add_node(
            "get_filtered_papers_from_conference",
            self._get_filtered_papers_from_conference_node,
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
        graph_builder.add_edge("initialize_state", "generate_queries_node")
        graph_builder.add_edge(
            "generate_queries_node", "get_filtered_papers_from_conference"
        )
        graph_builder.add_conditional_edges(
            source="get_filtered_papers_from_conference",
            path=self._check_extracted_titles,
            path_map={
                "Regenerate queries": "generate_queries_node",
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


def main():
    JSON_URLS = [
        "https://icml.cc/static/virtual/data/icml-2024-orals-posters.json",
        "https://iclr.cc/static/virtual/data/iclr-2024-orals-posters.json",
        "https://nips.cc/static/virtual/data/neurips-2024-orals-posters.json",
        "https://cvpr.thecvf.com/static/virtual/data/cvpr-2024-orals-posters.json",
    ]

    add_paper_num = 1
    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/airas/data"
    input = retrieve_related_paper_subgraph_input_data

    result = RetrieveRelatedConferencePaperSubgraph(
        llm_name=llm_name,
        save_dir=save_dir,
        paper_json_urls=JSON_URLS,
        add_paper_num=add_paper_num,
    ).run(input)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
