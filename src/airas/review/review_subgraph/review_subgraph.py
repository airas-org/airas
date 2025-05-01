from typing import TypedDict, Optional
from langgraph.graph import START, END, StateGraph
from langgraph.graph.graph import CompiledGraph

from airas.review.review_subgraph.nodes.review_node import ReviewNode
from airas.review.review_subgraph.input_data import review_subgraph_input_data


class ReviewSubgraphInputState(TypedDict):
    verification_policy: Optional[str]
    experiment_details: Optional[str]
    experiment_code: Optional[str]
    output_text_data: Optional[str]
    tex_text: Optional[str]


class ReviewSubgraphOutputState(TypedDict):
    review_routing: Optional[str]
    review_feedback: str


class ReviewSubgraphState(ReviewSubgraphInputState, ReviewSubgraphOutputState):
    pass


class ReviewSubgraph:
    def __init__(
        self,
        llm_name: str,
        save_dir: str,
        review_target: str,
        threshold: float,
    ):
        self.llm_name = llm_name
        self.save_dir = save_dir
        self.review_target = review_target
        self.threshold = threshold

    def _review_node(self, state: ReviewSubgraphState) -> dict:
        print("---ReviewSubgraph---")
        review_routing, review_feedback = ReviewNode(
            llm_name=self.llm_name,
            save_dir=self.save_dir,
            review_target=self.review_target,
            threshold=self.threshold,
        ).execute(state)
        return {
            "review_routing": review_routing,
            "review_feedback": review_feedback,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(ReviewSubgraphState)
        # make nodes
        graph_builder.add_node("review_node", self._review_node)
        # make edges
        graph_builder.add_edge(START, "review_node")
        graph_builder.add_edge("review_node", END)

        return graph_builder.compile()


if __name__ == "__main__":
    llm_name = "gpt-4o-2024-11-20"
    # llm_name = "gpt-4o-mini-2024-07-18"
    save_dir = "/workspaces/researchgraph/data/review_log"
    review_target = "executor_subgraph"
    threshold = 3.5

    subgraph = ReviewSubgraph(
        llm_name,
        save_dir,
        review_target,
        threshold=threshold,
    ).build_graph()
    result = subgraph.invoke(review_subgraph_input_data)
