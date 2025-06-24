import json
import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.publication.readme_subgraph.input_data import readme_subgraph_input_data
from airas.core.publication.readme_subgraph.nodes.readme_upload import readme_upload
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
readme_timed = lambda f: time_node("readme_subgraph")(f)  # noqa: E731


class ReadmeSubgraphInputState(TypedDict):
    github_repository: str
    branch_name: str
    paper_content: dict
    output_text_data: str
    experiment_devin_url: str


class ReadmeSubgraphHiddenState(TypedDict):
    github_owner: str
    repository_name: str


class ReadmeSubgraphOutputState(TypedDict):
    readme_upload_result: bool


class ReadmeSubgraphState(
    ReadmeSubgraphInputState,
    ReadmeSubgraphHiddenState,
    ReadmeSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class ReadmeSubgraph:
    def __init__(
        self,
    ) -> None:
        pass

    def _init_state(self, state: ReadmeSubgraphState) -> dict[str, str]:
        try:
            github_owner, repository_name = state["github_repository"].split("/", 1)
            return {
                "github_owner": github_owner,
                "repository_name": repository_name,
            }
        except ValueError:
            logger.error(
                f"Invalid github_repository format: {state['github_repository']}"
            )
            raise

    @readme_timed
    def _readme_upload_node(self, state: ReadmeSubgraphState) -> dict:
        readme_upload_result = readme_upload(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            title=state["paper_content"]["Title"],
            abstract=state["paper_content"]["Abstract"],
            devin_url=state["experiment_devin_url"],
        )
        return {"readme_upload_result": readme_upload_result}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(ReadmeSubgraphState)
        graph_builder.add_node("init_state", self._init_state)
        graph_builder.add_node("readme_upload_node", self._readme_upload_node)

        graph_builder.add_edge(START, "init_state")
        graph_builder.add_edge("init_state", "readme_upload_node")
        graph_builder.add_edge("readme_upload_node", END)

        return graph_builder.compile()

    def run(self, state: dict[str, Any], config: dict | None = None) -> dict[str, Any]:
        input_state_keys = ReadmeSubgraphInputState.__annotations__.keys()
        output_state_keys = ReadmeSubgraphOutputState.__annotations__.keys()

        input_state = {k: state[k] for k in input_state_keys if k in state}
        result = self.build_graph().invoke(input_state, config=config or {})
        output_state = {k: result[k] for k in output_state_keys if k in result}

        cleaned_state = {k: v for k, v in state.items() if k != "subgraph_name"}

        return {
            "subgraph_name": self.__class__.__name__,
            **cleaned_state,
            **output_state,
        }


def main():
    input = readme_subgraph_input_data
    result = ReadmeSubgraph().run(input)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running ReadmeSubgraph: {e}")
        raise
