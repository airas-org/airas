import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.review.paper_review_subgraph.input_data import (
    paper_review_subgraph_input_data,
)
from airas.features.review.paper_review_subgraph.nodes.paper_review import (
    paper_review,
)
from airas.features.review.paper_review_subgraph.prompts.paper_review_prompt import (
    paper_review_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.paper import PaperContent
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

paper_review_timed = lambda f: time_node("paper_review_subgraph")(f)  # noqa: E731


class PaperReviewSubgraphInputState(TypedDict):
    paper_content: PaperContent


class PaperReviewSubgraphHiddenState(TypedDict):
    pass


class PaperReviewSubgraphOutputState(TypedDict):
    novelty_score: int
    significance_score: int
    reproducibility_score: int
    experimental_quality_score: int


class PaperReviewSubgraphState(
    PaperReviewSubgraphInputState,
    PaperReviewSubgraphHiddenState,
    PaperReviewSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class PaperReviewSubgraph(BaseSubgraph):
    InputState = PaperReviewSubgraphInputState
    OutputState = PaperReviewSubgraphOutputState

    def __init__(
        self,
        llm_name: LLM_MODEL,
        prompt_template: str | None = None,
    ):
        self.llm_name = llm_name
        self.prompt_template = prompt_template or paper_review_prompt
        check_api_key(llm_api_key_check=True)

    @paper_review_timed
    def _paper_review(self, state: PaperReviewSubgraphState) -> dict[str, int]:
        review_result = paper_review(
            llm_name=self.llm_name,
            prompt_template=self.prompt_template,
            paper_content=state["paper_content"],
        )
        return review_result

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(PaperReviewSubgraphState)
        graph_builder.add_node("paper_review", self._paper_review)

        graph_builder.add_edge(START, "paper_review")
        graph_builder.add_edge("paper_review", END)
        return graph_builder.compile()


def main():
    llm_name = "o3-2025-04-16"
    input_data = paper_review_subgraph_input_data

    result = PaperReviewSubgraph(
        llm_name=llm_name,
    ).run(input_data)

    serializable_result = {}
    for key, value in result.items():
        if hasattr(value, "model_dump"):
            serializable_result[key] = value.model_dump()
        else:
            serializable_result[key] = value
    print(f"result: {json.dumps(serializable_result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running PaperReviewSubgraph: {e}")
        raise
