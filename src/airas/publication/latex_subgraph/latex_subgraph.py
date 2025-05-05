import logging
import os

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.publication.latex_subgraph.nodes.compile_to_pdf import LatexNode
from airas.publication.latex_subgraph.nodes.convert_to_latex import (
    convert_to_latex,
    convert_to_latex_prompt,
)
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class LatexSubgraphInputState(TypedDict):
    paper_content: dict[str, str]


class LatexSubgraphHiddenState(TypedDict):
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
        save_dir: str,
        llm_name: str,
    ):
        self.save_dir = save_dir
        self.llm_name = llm_name
        self.figures_dir = os.path.join(self.save_dir, "images")
        os.makedirs(self.figures_dir, exist_ok=True)
        self.pdf_file_path = os.path.join(self.save_dir, "paper.pdf")
        check_api_key(llm_api_key_check=True)

    @time_node("latex_subgraph", "_latex_node")
    def _convert_to_latex_node(self, state: LatexSubgraphState) -> dict:
        paper_tex_content = convert_to_latex(
            llm_name=self.llm_name,
            prompt_template=convert_to_latex_prompt,
            paper_content=state["paper_content"],
        )
        return {"paper_tex_content": paper_tex_content}

    @time_node("latex_subgraph", "_latex_node")
    def _latex_node(self, state: LatexSubgraphState) -> dict:
        tex_text = LatexNode(
            llm_name=self.llm_name,
            figures_dir=self.figures_dir,
            pdf_file_path=self.pdf_file_path,
            save_dir=self.save_dir,
            timeout=30,
        ).execute(
            paper_tex_content=state["paper_tex_content"],
        )
        return {
            "tex_text": tex_text,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(LatexSubgraphState)
        # make nodes
        graph_builder.add_node("convert_to_latex_node", self._convert_to_latex_node)
        graph_builder.add_node("latex_node", self._latex_node)
        # make edges
        graph_builder.add_edge(START, "convert_to_latex_node")
        graph_builder.add_edge("convert_to_latex_node", "latex_node")
        graph_builder.add_edge("latex_node", END)

        return graph_builder.compile()


LatexConvert = create_wrapped_subgraph(
    LatexSubgraph, LatexSubgraphInputState, LatexSubgraphOutputState
)


if __name__ == "__main__":
    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/researchgraph/data"

    github_repository = "auto-res2/experiment_script_matsuzawa"
    branch_name = "base-branch"
    extra_files = [
        {
            "upload_branch": "{{ branch_name }}",
            "upload_dir": ".research/",
            "local_file_paths": [f"{save_dir}/paper.pdf"],
        }
    ]

    latex_converter = LatexConvert(
        github_repository=github_repository,
        branch_name=branch_name,
        extra_files=extra_files,
        llm_name=llm_name,
        save_dir=save_dir,
    )

    result = latex_converter.run({})
    print(f"result: {result}")
