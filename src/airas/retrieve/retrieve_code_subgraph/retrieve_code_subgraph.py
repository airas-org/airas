import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.retrieve.retrieve_code_subgraph.input_data import (
    retrieve_code_subgraph_input_data,
)
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
from airas.utils.api_client.llm_facade_client import LLM_MODEL
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

retrieve_code_timed = lambda f: time_node("retrieve_code_subgraph")(f)  # noqa: E731


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
        llm_name: LLM_MODEL = "gemini-2.0-flash-001", 
    ):
        check_api_key(llm_api_key_check=True)
        self.llm_name = llm_name

    @retrieve_code_timed
    def _retrieve_repository_contents(self, state: RetrieveCodeState) -> dict:
        content_str = retrieve_repository_contents(github_url=state["base_github_url"])
        return {
            "repository_content_str": content_str,
        }

    @retrieve_code_timed
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
        graph_builder.add_node(
            "retrieve_repository_contents", self._retrieve_repository_contents
        )
        graph_builder.add_node(
            "extract_experimental_info", self._extract_experimental_info
        )

        graph_builder.add_edge(START, "retrieve_repository_contents")
        graph_builder.add_edge(
            "retrieve_repository_contents", "extract_experimental_info"
        )
        graph_builder.add_edge("extract_experimental_info", END)
        return graph_builder.compile()

    def run(
        self, 
        input: RetrieveCodeInputState, 
        config: dict | None = None
    ) -> dict:
        graph = self.build_graph()
        result = graph.invoke(input, config=config or {})

        # output_keys = RetrieveCodeOutputState.__annotations__.keys()
        # output = {k: result[k] for k in output_keys if k in result}
        return result


def main():
    input = retrieve_code_subgraph_input_data
    result = RetrieveCodeSubgraph().run(input)
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running RetrieveCodeSubgraph: {e}")
        raise
