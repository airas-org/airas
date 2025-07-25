import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.retrieve.get_paper_titles_subgraph.input_data import (
    get_paper_titles_subgraph_input_data,
)
from airas.features.retrieve.get_paper_titles_subgraph.nodes.openai_websearch_titles import (
    openai_websearch_titles,
)
from airas.features.retrieve.get_paper_titles_subgraph.prompt.openai_websearch_titles_prompt import (
    openai_websearch_titles_prompt,
)
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

get_paper_titles_from_web_str = "get_paper_titles_from_web_subgraph"
get_paper_titles_from_web_timed = lambda f: time_node(get_paper_titles_from_web_str)(f)  # noqa: E731


class GetPaperTitlesFromWebInputState(TypedDict):
    queries: list[str]


class GetPaperTitlesFromWebHiddenState(TypedDict): ...


class GetPaperTitlesFromWebOutputState(TypedDict):
    research_study_list: list[dict]


class GetPaperTitlesFromWebState(
    GetPaperTitlesFromWebInputState,
    GetPaperTitlesFromWebHiddenState,
    GetPaperTitlesFromWebOutputState,
    ExecutionTimeState,
): ...


class GetPaperTitlesFromWebSubgraph(BaseSubgraph):
    InputState = GetPaperTitlesFromWebInputState
    OutputState = GetPaperTitlesFromWebOutputState

    def __init__(self):
        check_api_key(llm_api_key_check=True)

    @get_paper_titles_from_web_timed
    def _openai_websearch_titles(
        self, state: GetPaperTitlesFromWebState
    ) -> dict[str, list[dict]]:
        titles = openai_websearch_titles(
            queries=state["queries"], prompt_template=openai_websearch_titles_prompt
        )
        # Convert titles to research_study_list format
        research_study_list = [{"title": title} for title in (titles or [])]
        return {"research_study_list": research_study_list}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(GetPaperTitlesFromWebState)
        graph_builder.add_node("openai_websearch_titles", self._openai_websearch_titles)

        graph_builder.add_edge(START, "openai_websearch_titles")
        graph_builder.add_edge("openai_websearch_titles", END)
        return graph_builder.compile()


def main():
    input = get_paper_titles_subgraph_input_data
    result = GetPaperTitlesFromWebSubgraph().run(input)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
