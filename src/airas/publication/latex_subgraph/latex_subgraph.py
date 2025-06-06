import json
import logging
import os
import shutil
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import NotRequired, TypedDict

from airas.publication.latex_subgraph.input_data import latex_subgraph_input_data
from airas.publication.latex_subgraph.nodes.compile_to_pdf import LatexNode
from airas.publication.latex_subgraph.nodes.convert_to_latex import (
    convert_to_latex,
)
from airas.publication.latex_subgraph.nodes.generate_bib import generate_bib
from airas.publication.latex_subgraph.prompt.convert_to_latex_prompt import (
    convert_to_latex_prompt,
)
from airas.publication.latex_subgraph.prompt.generate_bib_prompt import (
    generate_bib_prompt,
)
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
latex_timed = lambda f: time_node("latex_subgraph")(f)  # noqa: E731


class LatexSubgraphInputState(TypedDict):
    paper_content_with_placeholders: dict[str, str]
    references: dict[str, dict[str, Any]]
    figures_dir: NotRequired[str]


class LatexSubgraphHiddenState(TypedDict):
    paper_tex_content: dict[str, str]
    references_bib: dict[str, str]


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
    ):
        self.llm_name = llm_name
        self.save_dir = save_dir

        self.latex_dir = os.path.join(save_dir, "latex")
        if os.path.exists(self.latex_dir):  # NOTE: Cleanup – remove existing contents in save_dir/latex/
            shutil.rmtree(self.latex_dir)
        os.makedirs(self.latex_dir, exist_ok=True)

        check_api_key(llm_api_key_check=True)

    @latex_timed
    def _generate_bib(self, state: LatexSubgraphState) -> dict:
        references_bib = generate_bib(
            llm_name=self.llm_name, 
            prompt_template=generate_bib_prompt, 
            references=state["references"]
        )
        return {"references_bib": references_bib}

    @latex_timed
    def _convert_to_latex(self, state: LatexSubgraphState) -> dict:
        paper_tex_content = convert_to_latex(
            llm_name=self.llm_name,
            prompt_template=convert_to_latex_prompt,
            paper_content_with_placeholders=state["paper_content_with_placeholders"],
            references_bib=state["references_bib"], 
        )
        return {"paper_tex_content": paper_tex_content}

    @latex_timed
    def _compile_to_pdf(self, state: LatexSubgraphState) -> dict:
        tex_text = LatexNode(
            llm_name=self.llm_name,
            save_dir=self.latex_dir,
            figures_dir=state["figures_dir"],
        ).compile_to_pdf(
            paper_tex_content=state["paper_tex_content"],
            references_bib=state["references_bib"], 
        )
        return {"tex_text": tex_text}
        
    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(LatexSubgraphState)
        graph_builder.add_node("generate_bib", self._generate_bib)
        graph_builder.add_node("convert_to_latex", self._convert_to_latex)
        graph_builder.add_node("compile_to_pdf", self._compile_to_pdf)

        graph_builder.add_edge(START, "generate_bib")
        graph_builder.add_edge("generate_bib", "convert_to_latex")
        graph_builder.add_edge("convert_to_latex", "compile_to_pdf")
        graph_builder.add_edge("compile_to_pdf", END)

        return graph_builder.compile()

    def run(
        self, 
        input: LatexSubgraphInputState, 
        config: dict | None = None
    ) -> LatexSubgraphOutputState:
        graph = self.build_graph()
        result = graph.invoke(input, config=config or {})

        output_keys = LatexSubgraphOutputState.__annotations__.keys()
        output = {k: result[k] for k in output_keys if k in result}
        return output


def main():
    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/airas/data"
    input = latex_subgraph_input_data

    result = LatexSubgraph(
        llm_name=llm_name, 
        save_dir=save_dir, 
    ).run(input)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running LatexSubgraph: {e}")
        raise
