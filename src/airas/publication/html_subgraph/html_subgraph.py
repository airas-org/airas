import argparse
import glob
import json
import logging
import os

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.publication.html_subgraph.nodes.convert_to_html import convert_to_html
from airas.publication.html_subgraph.nodes.render_html import render_html
from airas.publication.html_subgraph.prompt.convert_to_html_prompt import (
    convert_to_html_prompt,
)
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class HtmlSubgraphInputState(TypedDict):
    paper_content: dict[str, str]


class HtmlSubgraphHiddenState(TypedDict):
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
    ):
        self.llm_name = llm_name
        self.save_dir = save_dir
        check_api_key(llm_api_key_check=True)

    @time_node("html_subgraph", "_convert_to_html_node")
    def _convert_to_html_node(self, state: HtmlSubgraphState) -> dict:
        paper_html_content = convert_to_html(
            llm_name=self.llm_name,
            paper_content=state["paper_content"],
            prompt_template=convert_to_html_prompt, 
        )
        return {"paper_html_content": paper_html_content}

    @time_node("html_subgraph", "_render_html_node")
    def _render_html_node(self, state: HtmlSubgraphState) -> dict:
        full_html = render_html(
            paper_html_content=state["paper_html_content"], save_dir=self.save_dir
        )
        return {"full_html": full_html}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(HtmlSubgraphState)
        # make nodes
        graph_builder.add_node("convert_to_html_node", self._convert_to_html_node)
        graph_builder.add_node("render_html_node", self._render_html_node)
        # make edges
        graph_builder.add_edge(START, "convert_to_html_node")
        graph_builder.add_edge("convert_to_html_node", "render_html_node")
        graph_builder.add_edge("render_html_node", END)

        return graph_builder.compile()


HtmlConvert = create_wrapped_subgraph(
    HtmlSubgraph, HtmlSubgraphInputState, HtmlSubgraphOutputState
)


def main():
    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/airas/data"
    figures_dir = "/workspaces/airas/data/images"
    pdf_files = glob.glob(os.path.join(figures_dir, "*.pdf"))


    parser = argparse.ArgumentParser(
        description="Execute HtmlSubgraph"
    )
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    extra_files = [
        {
            "upload_branch": "gh-pages",
            "upload_dir": "branches/{branch_name}/",
            "local_file_paths": [f"{save_dir}/index.html"],
        },
        {
            "upload_branch": "gh-pages",
            "upload_dir": "branches/{branch_name}/images/",
            "local_file_paths": pdf_files,
        },
    ]

    hc = HtmlConvert(
        github_repository=args.github_repository,
        branch_name=args.branch_name,
        extra_files=extra_files,
        llm_name=llm_name,
        save_dir=save_dir,
    )
    result = hc.run()
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running HtmlSubgraph: {e}")
        raise
