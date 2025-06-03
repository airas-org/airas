import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.publication.readme_subgraph.input_data import readme_subgraph_input_data
from airas.publication.readme_subgraph.nodes.readme_upload import readme_upload
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
readme_timed = lambda f: time_node("readme_subgraph")(f)  # noqa: E731


class ReadmeSubgraphInputState(TypedDict):
    github_owner: str
    repository_name: str
    branch_name: str
    paper_content: dict
    output_text_data: str
    experiment_devin_url: str


class ReadmeSubgraphOutputState(TypedDict):
    readme_upload_result: bool


class ReadmeSubgraphState(
    ReadmeSubgraphInputState,
    ReadmeSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class ReadmeSubgraph:
    def __init__(
        self,
    ) -> None:
        pass

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
        graph_builder.add_node("readme_upload_node", self._readme_upload_node)

        graph_builder.add_edge(START, "readme_upload_node")
        graph_builder.add_edge("readme_upload_node", END)

        return graph_builder.compile()
    
    def run(
        self, 
        input: ReadmeSubgraphInputState, 
        config: dict | None = None
    ) -> ReadmeSubgraphOutputState:
        graph = self.build_graph()
        full_result = graph.invoke(input, config=config or {})
        output_keys = ReadmeSubgraphOutputState.__annotations__.keys()
        result = {k: full_result[k] for k in output_keys if k in full_result}
        return result


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
