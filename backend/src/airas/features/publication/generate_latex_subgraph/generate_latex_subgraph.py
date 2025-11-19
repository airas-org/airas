import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.publication.generate_latex_subgraph.nodes.convert_placeholders_to_citations import (
    convert_placeholders_to_citations,
)
from airas.features.publication.generate_latex_subgraph.nodes.convert_to_latex import (
    convert_to_latex,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.paper import PaperContent
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
latex_timed = lambda f: time_node("generate_latex_subgraph")(f)  # noqa: E731


class GenerateLatexLLMMapping(BaseModel):
    convert_to_latex: LLM_MODEL = DEFAULT_NODE_LLMS["convert_to_latex"]


class GenerateLatexSubgraphInputState(TypedDict):
    references_bib: str
    paper_content: PaperContent


class GenerateLatexSubgraphHiddenState(TypedDict): ...


class GenerateLatexSubgraphOutputState(TypedDict):
    latex_formatted_paper_content: PaperContent


class GenerateLatexSubgraphState(
    GenerateLatexSubgraphInputState,
    GenerateLatexSubgraphHiddenState,
    GenerateLatexSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class GenerateLatexSubgraph(BaseSubgraph):
    InputState = GenerateLatexSubgraphInputState
    OutputState = GenerateLatexSubgraphOutputState

    def __init__(
        self,
        llm_client: LLMFacadeClient,
        llm_mapping: dict[str, str] | GenerateLatexLLMMapping | None = None,
    ):
        if llm_mapping is None:
            self.llm_mapping = GenerateLatexLLMMapping()
        elif isinstance(llm_mapping, dict):
            self.llm_mapping = GenerateLatexLLMMapping(**llm_mapping)
        elif isinstance(llm_mapping, GenerateLatexLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or GenerateLatexLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.llm_client = llm_client
        check_api_key(llm_api_key_check=True)

    @latex_timed
    def _convert_placeholders_to_citations(
        self, state: GenerateLatexSubgraphState
    ) -> dict[str, PaperContent]:
        paper_content = convert_placeholders_to_citations(
            paper_content=state["paper_content"],
            references_bib=state["references_bib"],
        )
        return {"paper_content": paper_content}

    @latex_timed
    async def _convert_to_latex_str(
        self, state: GenerateLatexSubgraphState
    ) -> dict[str, PaperContent]:
        latex_formatted_paper_content = await convert_to_latex(
            llm_name=self.llm_mapping.convert_to_latex,
            paper_content=state["paper_content"],
            llm_client=self.llm_client,
        )
        return {"latex_formatted_paper_content": latex_formatted_paper_content}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(GenerateLatexSubgraphState)
        graph_builder.add_node(
            "convert_placeholders_to_citations", self._convert_placeholders_to_citations
        )
        graph_builder.add_node("convert_to_latex", self._convert_to_latex_str)

        graph_builder.add_edge(START, "convert_placeholders_to_citations")
        graph_builder.add_edge("convert_placeholders_to_citations", "convert_to_latex")
        graph_builder.add_edge("convert_to_latex", END)

        return graph_builder.compile()


def main():
    from airas.features.publication.generate_latex_subgraph.input_data import (
        generate_latex_subgraph_input_data,
    )

    output = GenerateLatexSubgraph().run(generate_latex_subgraph_input_data)
    print(output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running GenerateLatexSubgraph: {e}")
        raise
