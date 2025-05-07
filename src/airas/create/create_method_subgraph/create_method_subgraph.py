import argparse
import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.create.create_method_subgraph.nodes.generator_node import generator_node
from airas.typing.paper import CandidatePaperInfo
from airas.utils.api_client.llm_facade_client import LLM_MODEL
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class CreateMethodSubgraphInputState(TypedDict):
    base_method_text: CandidatePaperInfo
    add_method_texts: list[CandidatePaperInfo]


class CreateMethodSubgraphHiddenState(TypedDict):
    pass


class CreateMethodSubgraphOutputState(TypedDict):
    new_method: str

class CreateMethodSubgraphState(
    CreateMethodSubgraphInputState,
    CreateMethodSubgraphHiddenState,
    CreateMethodSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class CreateMethodSubgraph:
    def __init__(
        self,
        llm_name: LLM_MODEL,
    ):
        self.llm_name = llm_name
        check_api_key(llm_api_key_check=True)

    @time_node("create_method_subgraph", "_generator_node")
    def _generator_node(self, state: CreateMethodSubgraphState) -> dict:
        logger.info("---CreateMethodSubgraph---")
        new_method = generator_node(
            llm_name=self.llm_name,
            base_method_text=state["base_method_text"],
            add_method_texts=state["add_method_texts"],
        )
        return {"new_method": new_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateMethodSubgraphState)
        # make nodes
        graph_builder.add_node("generator_node", self._generator_node)
        # make edges
        graph_builder.add_edge(START, "generator_node")
        graph_builder.add_edge("generator_node", END)

        return graph_builder.compile()


CreateMethod = create_wrapped_subgraph(
    CreateMethodSubgraph,
    CreateMethodSubgraphInputState,
    CreateMethodSubgraphOutputState,
)


def main():
    llm_name = "o3-mini-2025-01-31"

    parser = argparse.ArgumentParser(description="Execute CreateMethodSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    cm = CreateMethod(
        github_repository=args.github_repository,
        branch_name=args.branch_name,
        llm_name=llm_name,
    )
    result = cm.run()
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateMethodSubgraph: {e}")
        raise
