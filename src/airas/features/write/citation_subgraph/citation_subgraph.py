import logging
from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.retrieve.generate_queries_subgraph.nodes.generate_queries import (
    generate_queries,
)
from airas.features.write.citation_subgraph.input_data import (
    citation_subgraph_input_data,
)
from airas.features.write.citation_subgraph.nodes.embed_placeholders import (
    embed_placeholders,
)
from airas.features.write.citation_subgraph.nodes.openalex_fetch_references import (
    openalex_fetch_references,
)
from airas.features.write.citation_subgraph.prompt.embed_placeholders_prompt import (
    embed_placeholders_prompt,
)
from airas.features.write.citation_subgraph.prompt.generate_queries_prompt import (
    generate_queries_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
citation_timed = lambda f: time_node("citation_subgraph")(f)  # noqa: E731


class CitationSubgraphInputState(TypedDict):
    paper_content: dict[str, str]
    # user_bib_entries: NotRequired[str]


class CitationSubgraphHiddenState(TypedDict):
    placeholder_keys: list[str]
    generated_citation_queries: dict[str, str]


class CitationSubgraphOutputState(TypedDict):
    paper_content_with_placeholders: dict[str, str]
    references: dict[str, dict[str, Any]]


class CitationSubgraphState(
    CitationSubgraphInputState,
    CitationSubgraphHiddenState,
    CitationSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class CitationSubgraph(BaseSubgraph):
    InputState = CitationSubgraphInputState
    OutputState = CitationSubgraphOutputState

    def __init__(
        self,
        llm_name: str,
    ):
        self.llm_name = llm_name
        check_api_key(llm_api_key_check=True)

    @citation_timed
    def _embed_placeholders(
        self, state: CitationSubgraphState
    ) -> dict[str, dict[str, str] | list[str]]:
        paper_content_with_placeholders, placeholder_keys = embed_placeholders(
            llm_name=cast(LLM_MODEL, self.llm_name),
            paper_content=state["paper_content"],
            prompt_template=embed_placeholders_prompt,
        )
        return {
            "paper_content_with_placeholders": paper_content_with_placeholders,
            "placeholder_keys": placeholder_keys,
        }

    @citation_timed
    def _generate_query(
        self, state: CitationSubgraphState
    ) -> dict[str, dict[str, str]]:
        generated_citation_queries = generate_queries(
            llm_name=cast(LLM_MODEL, self.llm_name),
            paper_info=state["paper_content_with_placeholders"],
            prompt_template=generate_queries_prompt,
            dict_keys=state["placeholder_keys"],
        )
        return {"generated_citation_queries": generated_citation_queries}

    @citation_timed
    def _search_references(self, state: CitationSubgraphState) -> dict[str, Any]:
        references = openalex_fetch_references(
            generated_citation_queries=state["generated_citation_queries"]
        )
        paper = state["paper_content_with_placeholders"]
        cleaned_paper = {}

        for section, content in paper.items():
            for placeholder, ref in references.items():
                if not ref:
                    content = content.replace(placeholder, "")
            cleaned_paper[section] = content

        return {
            "references": references,
            "paper_content_with_placeholders": cleaned_paper,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CitationSubgraphState)
        graph_builder.add_node("embed_placeholders", self._embed_placeholders)
        graph_builder.add_node("generate_query", self._generate_query)
        graph_builder.add_node("search_references", self._search_references)

        graph_builder.add_edge(START, "embed_placeholders")
        graph_builder.add_edge("embed_placeholders", "generate_query")
        graph_builder.add_edge("generate_query", "search_references")
        graph_builder.add_edge("search_references", END)

        return graph_builder.compile()


def main():
    llm_name = "o3-mini-2025-01-31"
    input = citation_subgraph_input_data

    result = CitationSubgraph(
        llm_name=llm_name,
    ).run(input)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CitationSubgraph: {e}")
        raise
