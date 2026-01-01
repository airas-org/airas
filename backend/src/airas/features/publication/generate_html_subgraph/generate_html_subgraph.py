import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.publication.generate_html_subgraph.nodes.convert_to_html import (
    convert_to_html,
)
from airas.features.publication.generate_html_subgraph.nodes.render_html import (
    render_html,
)
from airas.features.publication.generate_html_subgraph.nodes.replace_citation_keys_with_links import (
    replace_citation_keys_with_links,
)
from airas.features.publication.generate_html_subgraph.prompts.convert_to_html_prompt import (
    convert_to_html_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLMFacadeClient,
)
from airas.services.api_client.llm_specs import LLM_MODELS
from airas.types.paper import PaperContent
from airas.types.research_session import ResearchSession
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
html_timed = lambda f: time_node("generate_html_subgraph")(f)  # noqa: E731


class GenerateHtmlLLMMapping(BaseModel):
    convert_to_html: LLM_MODELS = DEFAULT_NODE_LLMS["convert_to_html"]


class GenerateHtmlSubgraphInputState(TypedDict):
    paper_content: PaperContent
    references_bib: str
    research_session: ResearchSession


class GenerateHtmlSubgraphHiddenState(TypedDict):
    paper_content_html: str


class GenerateHtmlSubgraphOutputState(TypedDict):
    full_html: str


class GenerateHtmlSubgraphState(
    GenerateHtmlSubgraphInputState,
    GenerateHtmlSubgraphHiddenState,
    GenerateHtmlSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class GenerateHtmlSubgraph(BaseSubgraph):
    InputState = GenerateHtmlSubgraphInputState
    OutputState = GenerateHtmlSubgraphOutputState

    def __init__(
        self,
        llm_client: LLMFacadeClient,
        llm_mapping: dict[str, str] | GenerateHtmlLLMMapping | None = None,
    ):
        if llm_mapping is None:
            self.llm_mapping = GenerateHtmlLLMMapping()
        elif isinstance(llm_mapping, dict):
            self.llm_mapping = GenerateHtmlLLMMapping(**llm_mapping)
        elif isinstance(llm_mapping, GenerateHtmlLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or GenerateHtmlLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.llm_client = llm_client

    @html_timed
    async def _convert_to_html(
        self, state: GenerateHtmlSubgraphState
    ) -> dict[str, str]:
        paper_content_html = await convert_to_html(
            llm_name=self.llm_mapping.convert_to_html,
            paper_content=state["paper_content"],
            research_session=state["research_session"],
            prompt_template=convert_to_html_prompt,
            llm_client=self.llm_client,
        )
        return {"paper_content_html": paper_content_html}

    @html_timed
    def _replace_citation_keys_with_links(
        self, state: GenerateHtmlSubgraphState
    ) -> dict[str, str]:
        paper_content_html = replace_citation_keys_with_links(
            html_text=state["paper_content_html"],
            references_bib=state["references_bib"],
        )
        return {"paper_content_html": paper_content_html}

    @html_timed
    def _render_html(self, state: GenerateHtmlSubgraphState) -> dict[str, str]:
        full_html = render_html(
            paper_content_html=state["paper_content_html"],
        )
        return {"full_html": full_html}

    def build_graph(self):
        graph_builder = StateGraph(GenerateHtmlSubgraphState)
        graph_builder.add_node("convert_to_html", self._convert_to_html)
        graph_builder.add_node(
            "replace_citation_keys_with_links", self._replace_citation_keys_with_links
        )
        graph_builder.add_node("render_html", self._render_html)

        graph_builder.add_edge(START, "convert_to_html")
        graph_builder.add_edge("convert_to_html", "replace_citation_keys_with_links")
        graph_builder.add_edge("replace_citation_keys_with_links", "render_html")
        graph_builder.add_edge("render_html", END)

        return graph_builder.compile()


def main():
    from airas.features.publication.generate_html_subgraph.input_data import (
        generate_html_subgraph_input_data,
    )

    result = GenerateHtmlSubgraph().run(generate_html_subgraph_input_data)
    print(f"Result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running GenerateHtmlSubgraph: {e}")
        raise
