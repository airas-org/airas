import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.retrieve.summarize_paper_subgraph.input_data import (
    summarize_paper_subgraph_input_data,
)
from airas.features.retrieve.summarize_paper_subgraph.nodes.summarize_paper import (
    summarize_paper,
)
from airas.features.retrieve.summarize_paper_subgraph.prompt.summarize_paper_prompt import (
    summarize_paper_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

summarize_paper_subgraph_str = "summarize_paper_subgraph"
summarize_paper_subgraph_timed = lambda f: time_node(summarize_paper_subgraph_str)(f)  # noqa: E731


class SummarizePaperInputState(TypedDict):
    research_study_list: list[dict]


class SummarizePaperHiddenState(TypedDict): ...


class SummarizePaperOutputState(TypedDict):
    research_study_list: list[dict]


class SummarizePaperState(
    SummarizePaperInputState,
    SummarizePaperHiddenState,
    SummarizePaperOutputState,
    ExecutionTimeState,
): ...


class SummarizePaperSubgraph(BaseSubgraph):
    InputState = SummarizePaperInputState
    OutputState = SummarizePaperOutputState

    def __init__(self, llm_name: LLM_MODEL):
        self.llm_name = llm_name

    @summarize_paper_subgraph_timed
    def _summarize_paper(self, state: SummarizePaperState) -> dict[str, list[dict]]:
        research_study_list = state["research_study_list"]

        for research_study in research_study_list:
            if research_study.get("llm_extracted_info"):
                logger.info(
                    f"Skipping summarization for '{research_study.get('title', 'N/A')}' as info already exists."
                )
                continue

            full_text = research_study.get("full_text", "")
            if full_text:
                (
                    main_contributions,
                    methodology,
                    experimental_setup,
                    limitations,
                    future_research_directions,
                ) = summarize_paper(
                    llm_name=self.llm_name,
                    prompt_template=summarize_paper_prompt,
                    paper_text=full_text,
                )

                research_study["llm_extracted_info"] = {
                    "main_contributions": main_contributions,
                    "methodology": methodology,
                    "experimental_setup": experimental_setup,
                    "limitations": limitations,
                    "future_research_directions": future_research_directions,
                }

        return {"research_study_list": research_study_list}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(SummarizePaperState)
        graph_builder.add_node("summarize_paper", self._summarize_paper)

        graph_builder.add_edge(START, "summarize_paper")
        graph_builder.add_edge("summarize_paper", END)
        return graph_builder.compile()


def main():
    llm_name = "o3-mini-2025-01-31"
    input_data = summarize_paper_subgraph_input_data
    result = SummarizePaperSubgraph(llm_name=llm_name).run(input_data)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
