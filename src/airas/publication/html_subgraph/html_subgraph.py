import json
import logging
import os
import shutil

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

setup_logging()
logger = logging.getLogger(__name__)
html_timed = lambda f: time_node("html_subgraph")(f)  # noqa: E731


class HtmlSubgraphInputState(TypedDict):
    paper_content: dict[str, str]
    figures_dir: str | None


class HtmlSubgraphHiddenState(TypedDict):
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
    ):
        self.llm_name = llm_name
        self.save_dir = save_dir

        self.html_dir = os.path.join(save_dir, "html")
        if os.path.exists(self.html_dir):   # NOTE: Cleanup – remove existing contents in save_dir/html/
            shutil.rmtree(self.html_dir)
        os.makedirs(self.html_dir, exist_ok=True)

        check_api_key(llm_api_key_check=True)

    @html_timed
    def _convert_pdf_to_png(self, state: HtmlSubgraphState) -> dict[str, bool]:
        pdf_dir = state["figures_dir"]
        if pdf_dir is None:
            logger.info("No images available. Skipping PDF to PNG conversion.")
            return {"pdf_to_png": False}
        
        to_png_dir = os.path.join(self.html_dir, "images")
        pdf_to_png = convert_pdf_to_png(pdf_dir, to_png_dir)
        return {
            "pdf_to_png": pdf_to_png
        }

    @html_timed
    def _convert_to_html(self, state: HtmlSubgraphState) -> dict:
        paper_html_content = convert_to_html(
            llm_name=self.llm_name,
            paper_content=state["paper_content"],
            prompt_template=convert_to_html_prompt, 
        )
        return {"paper_html_content": paper_html_content}

    @html_timed
    def _render_html(self, state: HtmlSubgraphState) -> dict:
        full_html = render_html(
            paper_html_content=state["paper_html_content"], 
            save_dir=self.html_dir, 
        )
        return {"full_html": full_html}
    
    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(HtmlSubgraphState)
        graph_builder.add_node("convert_pdf_to_png", self._convert_pdf_to_png)
        graph_builder.add_node("convert_to_html", self._convert_to_html)
        graph_builder.add_node("render_html", self._render_html)

        graph_builder.add_edge(START, "convert_pdf_to_png")
        graph_builder.add_edge("convert_pdf_to_png", "convert_to_html")
        graph_builder.add_edge("convert_to_html", "render_html")
        graph_builder.add_edge("render_html", END)

        return graph_builder.compile()
    
    def run(
        self, 
        input: HtmlSubgraphInputState, 
        config: dict | None = None
    ) -> HtmlSubgraphOutputState:
        graph = self.build_graph()
        full_result = graph.invoke(input, config=config or {})
        output_keys = HtmlSubgraphOutputState.__annotations__.keys()
        result = {k: full_result[k] for k in output_keys if k in full_result}
        return result


def main():
    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/airas/data"
    input = html_subgraph_input_data

    result = HtmlSubgraph(
        llm_name=llm_name, 
        save_dir=save_dir, 
    ).run(input)
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running HtmlSubgraph: {e}")
        raise