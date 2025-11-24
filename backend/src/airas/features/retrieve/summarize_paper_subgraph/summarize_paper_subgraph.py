import asyncio
import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
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
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_study import ResearchStudy
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

summarize_paper_subgraph_str = "summarize_paper_subgraph"
summarize_paper_subgraph_timed = lambda f: time_node(summarize_paper_subgraph_str)(f)  # noqa: E731


class SummarizePaperLLMMapping(BaseModel):
    summarize_paper: LLM_MODEL = DEFAULT_NODE_LLMS["summarize_paper"]


class SummarizePaperInputState(TypedDict):
    research_study_list: list[ResearchStudy]


class SummarizePaperHiddenState(TypedDict): ...


class SummarizePaperOutputState(TypedDict):
    research_study_list: list[ResearchStudy]


class SummarizePaperState(
    SummarizePaperInputState,
    SummarizePaperHiddenState,
    SummarizePaperOutputState,
    ExecutionTimeState,
): ...


class SummarizePaperSubgraph(BaseSubgraph):
    InputState = SummarizePaperInputState
    OutputState = SummarizePaperOutputState

    def __init__(
        self,
        llm_client: LLMFacadeClient,
        llm_mapping: dict[str, str] | SummarizePaperLLMMapping | None = None,
    ):
        self.llm_client = llm_client
        if llm_mapping is None:
            self.llm_mapping = SummarizePaperLLMMapping()
        elif isinstance(llm_mapping, dict):
            self.llm_mapping = SummarizePaperLLMMapping(**llm_mapping)
        elif isinstance(llm_mapping, SummarizePaperLLMMapping):
            # すでに型が正しい場合も受け入れる
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or SummarizePaperLLMMapping, "
                f"but got {type(llm_mapping)}"
            )

    @summarize_paper_subgraph_timed
    async def _summarize_paper(
        self, state: SummarizePaperState
    ) -> dict[str, list[ResearchStudy]]:
        research_study_list = await summarize_paper(
            llm_name=self.llm_mapping.summarize_paper,
            llm_client=self.llm_client,
            prompt_template=summarize_paper_prompt,
            research_study_list=state["research_study_list"],
        )
        return {"research_study_list": research_study_list}

    def build_graph(self):
        graph_builder = StateGraph(SummarizePaperState)
        graph_builder.add_node("summarize_paper", self._summarize_paper)

        graph_builder.add_edge(START, "summarize_paper")
        graph_builder.add_edge("summarize_paper", END)
        return graph_builder.compile()


async def main():
    input_data = summarize_paper_subgraph_input_data
    result = await SummarizePaperSubgraph().arun(input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise
