import argparse
import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.retrieve.retrieve_code_subgraph.node.extract_experimental_info import (
    extract_experimental_info,
)
from airas.retrieve.retrieve_code_subgraph.node.retrieve_repository_contents import (
    retrieve_repository_contents,
)
from airas.retrieve.retrieve_code_subgraph.prompt.extract_experimental_info_prompt import (
    extract_experimental_info_prompt,
)
from airas.typing.paper import CandidatePaperInfo
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class RetrieveCodeInputState(TypedDict):
    base_github_url: str
    base_method_text: CandidatePaperInfo


class RetrieveCodeHiddenState(TypedDict):
    repository_content_str: str


class RetrieveCodeOutputState(TypedDict):
    base_experimental_code: str
    base_experimental_info: str


class RetrieveCodeState(
    RetrieveCodeInputState,
    RetrieveCodeHiddenState,
    RetrieveCodeOutputState,
    ExecutionTimeState,
):
    pass


class RetrieveCodeSubgraph:
    def __init__(
        self, 
        llm_name: str = "gemini-2.0-flash-001", 
    ):
        check_api_key(llm_api_key_check=True)
        self.llm_name = llm_name

    @time_node("retrieve_code_subgraph", "retrieve_repository_contents")
    def _retrieve_repository_contents(self, state: RetrieveCodeState) -> dict:
        content_str = retrieve_repository_contents(github_url=state["base_github_url"])
        return {
            "repository_content_str": content_str,
        }

    @time_node("retrieve_code_subgraph", "extract_experimental_info")
    def _extract_experimental_info(self, state: RetrieveCodeState) -> dict:
        if state["repository_content_str"] == "":
            logger.warning("No repository content found. Skipping extraction.")
            return {
                "base_experimental_code": "",
                "base_experimental_info": "",
            }
        
        else:
            extract_code, experimental_info = extract_experimental_info(
                llm_name=self.llm_name,
                method_text=state["base_method_text"],
                repository_content_str=state["repository_content_str"],
                prompt_template=extract_experimental_info_prompt, 
            )
            return {
                "base_experimental_code": extract_code,
                "base_experimental_info": experimental_info,
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


def main():
    parser = argparse.ArgumentParser(description="Execute RetrieveCodeSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()
    
    rc = RetrieveCode(
        github_repository=args.github_repository,
        branch_name=args.branch_name,
    )
  
    # result = rc.run(retrieve_code_subgraph_input_data)
    result = rc.run()
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running RetrieveCodeSubgraph: {e}")
        raise
