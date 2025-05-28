import argparse
import json
import logging
import os
import shutil

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.publication.latex_subgraph.input_data import latex_subgraph_input_data
from airas.publication.latex_subgraph.nodes.compile_to_pdf import LatexNode
from airas.publication.latex_subgraph.nodes.convert_to_latex import (
    convert_to_latex,
)
from airas.publication.latex_subgraph.prompt.convert_to_latex_prompt import (
    convert_to_latex_prompt,
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
latex_timed = lambda f: time_node("latex_subgraph")(f)  # noqa: E731


class LatexSubgraphInputState(TypedDict):
    github_repository: str
    branch_name: str
    paper_content: dict[str, str]


class LatexSubgraphHiddenState(TypedDict):
    github_owner: str
    repository_name: str
    figures_dir: str
    cleanup_tmp: bool
    paper_tex_content: dict[str, str]


class LatexSubgraphOutputState(TypedDict):
    tex_text: str


class LatexSubgraphState(
    LatexSubgraphInputState,
    LatexSubgraphHiddenState,
    LatexSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class LatexSubgraph:
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

        self.figures_dir = os.path.join(self.save_dir, "images")
        self.pdf_file_path = os.path.join(self.save_dir, "paper.pdf")
        check_api_key(llm_api_key_check=True)

    def _init(self, state: LatexSubgraphState) -> dict[str, str]:
        github_repository = state["github_repository"]
        if "/" in github_repository:
            github_owner, repository_name = github_repository.split("/", 1)
            return {
                "github_owner": github_owner,
                "repository_name": repository_name,
            }
        else:
            raise ValueError("Invalid repository name format.")
        
    @latex_timed
    def _prepare_figures(self, state: LatexSubgraphState) -> dict[str, str | None]:
        logger.info("---LatexSubgraph---")
        src_dir = fetch_figures_from_repository(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            tmp_dir=self.tmp_dir,
        )
        if src_dir is None:
            logger.warning("No figures found in the repository – skipping figure copy.")
            return {"figures_dir": None}
        
        if os.path.exists(self.figures_dir):
            shutil.rmtree(self.figures_dir)
        shutil.copytree(src_dir, self.figures_dir)

        return {"figures_dir": self.figures_dir}

    @latex_timed
    def _convert_to_latex_node(self, state: LatexSubgraphState) -> dict:
        paper_tex_content = convert_to_latex(
            llm_name=self.llm_name,
            paper_content=state["paper_content"],
            prompt_template=convert_to_latex_prompt,
        )
        return {"paper_tex_content": paper_tex_content}

    @latex_timed
    def _latex_node(self, state: LatexSubgraphState) -> dict:
        tex_text = LatexNode(
            llm_name=self.llm_name,
            figures_dir=state["figures_dir"],
            pdf_file_path=self.pdf_file_path,
            save_dir=self.save_dir,
            timeout=30,
        ).execute(
            paper_tex_content=state["paper_tex_content"],
        )
        return {
            "tex_text": tex_text,
        }
    
    @latex_timed
    def _cleanup_tmp_dir(self, state: LatexSubgraphState) -> dict[str, bool]:
        cleanup_tmp = cleanup_tmp_dir(
            tmp_dir=self.tmp_dir
        )
        return {"cleanup_tmp": cleanup_tmp}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(LatexSubgraphState)
        # make nodes
        graph_builder.add_node("init", self._init)
        graph_builder.add_node("prepare_figures", self._prepare_figures)
        graph_builder.add_node("convert_to_latex_node", self._convert_to_latex_node)
        graph_builder.add_node("latex_node", self._latex_node)
        graph_builder.add_node("cleanup_tmp_dir", self._cleanup_tmp_dir)
        # make edges
        graph_builder.add_edge(START, "init")
        graph_builder.add_edge("init", "prepare_figures")
        graph_builder.add_edge("prepare_figures", "convert_to_latex_node")
        graph_builder.add_edge("convert_to_latex_node", "latex_node")
        graph_builder.add_edge("latex_node", "cleanup_tmp_dir")
        graph_builder.add_edge("cleanup_tmp_dir", END)

        return graph_builder.compile()


def main():
    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/airas/data"
    tmp_dir = "/workspaces/airas/tmp"

    parser = argparse.ArgumentParser(
        description="LatexSubgraph"
    )
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    latex_subgraph = LatexSubgraph(
        llm_name=llm_name, 
        save_dir=save_dir, 
        tmp_dir=tmp_dir, 
    ).build_graph()
    result = latex_subgraph.invoke({
        **latex_subgraph_input_data, 
        "github_repository": args.github_repository, 
        "branch_name": args.branch_name, 
    })
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running LatexSubgraph: {e}")
        raise
