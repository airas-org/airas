import logging
from typing import TypedDict
from langgraph.graph import START, END, StateGraph
from langgraph.graph.graph import CompiledGraph

from airas.retrieve.retrieve_code_subgraph.node.retrieve_repository_contents import (
    retrieve_repository_contents,
)
from airas.retrieve.retrieve_code_subgraph.node.extract_experimental_info import (
    extract_experimental_info,
)
from airas.retrieve.retrieve_code_subgraph.input_data import (
    retrieve_code_subgraph_input_data,
)

from airas.utils.check_api_key import check_api_key
from airas.utils.logging_utils import setup_logging
from airas.utils.execution_timers import time_node, ExecutionTimeState
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph

setup_logging()
logger = logging.getLogger(__name__)


class RetrieveCodeInputState(TypedDict):
    base_github_url: str
    base_method_text: str


class RetrieveCodeHiddenState(TypedDict):
    repository_content_str: str


class RetrieveCodeOutputState(TypedDict):
    experimental_code: str
    experimental_info: str


class RetrieveCodeState(
    RetrieveCodeInputState,
    RetrieveCodeHiddenState,
    RetrieveCodeOutputState,
    ExecutionTimeState,
):
    pass


class RetrieveCodeSubgraph:
    def __init__(self):
        check_api_key(llm_api_key_check=True)

    @time_node("retrieve_code_subgraph", "retrieve_repository_contents")
    def _retrieve_repository_contents(self, state: RetrieveCodeState) -> dict:
        content_str = retrieve_repository_contents(github_url=state["base_github_url"])
        return {
            "repository_content_str": content_str,
        }

    @time_node("retrieve_code_subgraph", "extract_experimental_info")
    def _extract_experimental_info(self, state: RetrieveCodeState) -> dict:
        extract_code, experimental_info = extract_experimental_info(
            model_name="gemini-2.0-flash-001",
            method_text=state["base_method_text"],
            repository_content_str=state["repository_content_str"],
        )
        return {
            "experimental_code": extract_code,
            "experimental_info": experimental_info,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(RetrieveCodeState)
        # make nodes
        graph_builder.add_node(
            "retrieve_repository_contents", self._retrieve_repository_contents
        )
        graph_builder.add_node(
            "extract_experimental_info", self._extract_experimental_info
        )
        # make edges
        graph_builder.add_edge(START, "retrieve_repository_contents")
        graph_builder.add_edge(
            "retrieve_repository_contents", "extract_experimental_info"
        )
        graph_builder.add_edge("extract_experimental_info", END)

        return graph_builder.compile()


RetrieveCode = create_wrapped_subgraph(
    RetrieveCodeSubgraph,
    RetrieveCodeInputState,
    RetrieveCodeOutputState,
)

if __name__ == "__main__":
    subgraph = RetrieveCodeSubgraph()
    compiled_graph = subgraph.build_graph()
    output = compiled_graph.invoke(retrieve_code_subgraph_input_data)
    print("Output:", output)
