import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.review.review_paper_subgraph.input_data import (
    review_paper_subgraph_input_data,
)
from airas.features.review.review_paper_subgraph.nodes.review_paper import (
    review_paper,
)
from airas.features.review.review_paper_subgraph.prompts.review_paper_prompt import (
    review_paper_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.paper import PaperContent, PaperReviewScores
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

review_paper_timed = lambda f: time_node("review_paper_subgraph")(f)  # noqa: E731


class ReviewPaperLLMMapping(BaseModel):
    review_paper: LLM_MODEL = DEFAULT_NODE_LLMS["review_paper"]


class ReviewPaperSubgraphInputState(TypedDict):
    paper_content: PaperContent


class ReviewPaperSubgraphHiddenState(TypedDict):
    pass


class ReviewPaperSubgraphOutputState(TypedDict):
    paper_review_scores: PaperReviewScores


class ReviewPaperSubgraphState(
    ReviewPaperSubgraphInputState,
    ReviewPaperSubgraphHiddenState,
    ReviewPaperSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class ReviewPaperSubgraph(BaseSubgraph):
    InputState = ReviewPaperSubgraphInputState
    OutputState = ReviewPaperSubgraphOutputState

    def __init__(
        self,
        llm_mapping: ReviewPaperLLMMapping | None = None,
        prompt_template: str | None = None,
    ):
        self.llm_mapping = llm_mapping or ReviewPaperLLMMapping()
        self.prompt_template = prompt_template or review_paper_prompt
        check_api_key(llm_api_key_check=True)

    @review_paper_timed
    def _review_paper(
        self, state: ReviewPaperSubgraphState
    ) -> dict[str, PaperReviewScores]:
        review_result = review_paper(
            llm_name=self.llm_mapping.review_paper,
            prompt_template=self.prompt_template,
            paper_content=state["paper_content"],
        )
        return review_result

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(ReviewPaperSubgraphState)
        graph_builder.add_node("review_paper", self._review_paper)

        graph_builder.add_edge(START, "review_paper")
        graph_builder.add_edge("review_paper", END)
        return graph_builder.compile()


def main():
    input_data = review_paper_subgraph_input_data

    result = ReviewPaperSubgraph().run(input_data)

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
