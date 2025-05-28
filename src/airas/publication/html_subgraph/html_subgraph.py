import argparse
import glob
import json
import logging
import os

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.publication.html_subgraph.input_data import html_subgraph_input_data
from airas.publication.html_subgraph.nodes.convert_pdf_to_png import convert_pdf_to_png
from airas.publication.html_subgraph.nodes.convert_to_html import convert_to_html
from airas.publication.html_subgraph.nodes.render_html import render_html
from airas.publication.html_subgraph.prompt.convert_to_html_prompt import (
    convert_to_html_prompt,
)
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging
from airas.write.writer_subgraph.nodes.cleanup_tmp_dir import cleanup_tmp_dir
from airas.write.writer_subgraph.nodes.fetch_figures_from_repository import (
    fetch_figures_from_repository,
)

setup_logging()
logger = logging.getLogger(__name__)
html_timed = lambda f: time_node("html_subgraph")(f)  # noqa: E731


class HtmlSubgraphInputState(TypedDict):
    github_repository: str
    branch_name: str
    paper_content: dict[str, str]


class HtmlSubgraphHiddenState(TypedDict):
    github_owner: str
    repository_name: str
    figures_dir: str
    cleanup_tmp: bool
    pdf_to_png: bool
    paper_html_content: str


class HtmlSubgraphOutputState(TypedDict):
    full_html: str


class HtmlSubgraphState(
    HtmlSubgraphInputState,
    HtmlSubgraphHiddenState,
    HtmlSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class HtmlSubgraph:
    def __init__(
        self,
        llm_name: str,
        save_dir: str,
        tmp_dir: str, 
    ):
        # NOTE: tmp_dir is a temporary directory used during execution and will be cleaned up at the end.
        self.llm_name = llm_name
        self.save_dir = save_dir
        self.tmp_dir = tmp_dir
        check_api_key(llm_api_key_check=True)

    def _init(self, state: HtmlSubgraphState) -> dict[str, str]:
        github_repository = state["github_repository"]
        if "/" in github_repository:
            github_owner, repository_name = github_repository.split("/", 1)
            return {
                "github_owner": github_owner,
                "repository_name": repository_name,
            }
        else:
            raise ValueError("Invalid repository name format.")
        
    @html_timed
    def _prepare_figures(self, state: HtmlSubgraphState) -> dict[str, str | None]:
        logger.info("---HtmlSubgraph---")
        figures_dir = fetch_figures_from_repository(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            tmp_dir=self.tmp_dir,
        )
        return {"figures_dir": figures_dir}

    @html_timed
    def _convert_pdf_to_png(self, state: HtmlSubgraphState) -> dict[str, bool]:
        pdf_to_png = convert_pdf_to_png(state["figures_dir"])
        return {
            "pdf_to_png": pdf_to_png
        }

    @html_timed
    def _convert_to_html_node(self, state: HtmlSubgraphState) -> dict:
        paper_html_content = convert_to_html(
            llm_name=self.llm_name,
            paper_content=state["paper_content"],
            prompt_template=convert_to_html_prompt, 
        )
        return {"paper_html_content": paper_html_content}

    @html_timed
    def _render_html_node(self, state: HtmlSubgraphState) -> dict:
        full_html = render_html(
            paper_html_content=state["paper_html_content"], save_dir=self.save_dir
        )
        return {"full_html": full_html}
    
    #gh-pagesブランチにアップロード
    
    @html_timed
    def _cleanup_tmp_dir(self, state: HtmlSubgraphState) -> dict[str, bool]:
        cleanup_tmp = cleanup_tmp_dir(
            tmp_dir=self.tmp_dir
        )
        return {"cleanup_tmp": cleanup_tmp}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(HtmlSubgraphState)
        # make nodes
        graph_builder.add_node("init", self._init)
        graph_builder.add_node("prepare_figures", self._prepare_figures)
        graph_builder.add_node("convert_pdf_to_png_node", self._convert_pdf_to_png)
        graph_builder.add_node("convert_to_html_node", self._convert_to_html_node)
        graph_builder.add_node("render_html_node", self._render_html_node)
        graph_builder.add_node("cleanup_tmp_dir", self._cleanup_tmp_dir)
        # make edges
        graph_builder.add_edge(START, "init")
        graph_builder.add_edge("init", "prepare_figures")
        graph_builder.add_edge("prepare_figures", "convert_pdf_to_png_node")
        graph_builder.add_edge("convert_pdf_to_png_node", "convert_to_html_node")
        graph_builder.add_edge("convert_to_html_node", "render_html_node")
        graph_builder.add_edge("render_html_node", "cleanup_tmp_dir")
        graph_builder.add_edge("cleanup_tmp_dir", END)

        return graph_builder.compile()


def main():
    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/airas/data"
    tmp_dir = "/workspaces/airas/tmp"

    parser = argparse.ArgumentParser(
        description="HtmlSubgraph"
    )
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    html_subgraph = HtmlSubgraph(
        llm_name=llm_name, 
        save_dir=save_dir, 
        tmp_dir=tmp_dir, 
    ).build_graph()
    result = html_subgraph.invoke({
        **html_subgraph_input_data, 
        "github_repository": args.github_repository, 
        "branch_name": args.branch_name, 
    })
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running HtmlSubgraph: {e}")
        raise