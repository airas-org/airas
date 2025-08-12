import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.publication.readme_subgraph.input_data import (
    readme_subgraph_input_data,
)
from airas.features.publication.readme_subgraph.nodes.readme_upload import readme_upload
from airas.types.github import GitHubRepositoryInfo
from airas.types.paper import PaperContent
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
readme_timed = lambda f: time_node("readme_subgraph")(f)  # noqa: E731


class ReadmeSubgraphInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo
    paper_content: PaperContent
    experiment_devin_url: str


class ReadmeSubgraphHiddenState(TypedDict): ...


class ReadmeSubgraphOutputState(TypedDict):
    readme_upload_result: bool


class ReadmeSubgraphState(
    ReadmeSubgraphInputState,
    ReadmeSubgraphHiddenState,
    ReadmeSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class ReadmeSubgraph(BaseSubgraph):
    InputState = ReadmeSubgraphInputState
    OutputState = ReadmeSubgraphOutputState

    def __init__(
        self,
    ) -> None:
        pass

    @readme_timed
    def _readme_upload_node(self, state: ReadmeSubgraphState) -> dict:
        readme_upload_result = readme_upload(
            github_repository_info=state["github_repository_info"],
            title=state["paper_content"].title,
            abstract=state["paper_content"].abstract,
            devin_url=state["experiment_devin_url"],
        )
        return {"readme_upload_result": readme_upload_result}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(ReadmeSubgraphState)
        graph_builder.add_node("readme_upload_node", self._readme_upload_node)

        graph_builder.add_edge(START, "readme_upload_node")
        graph_builder.add_edge("readme_upload_node", END)

        return graph_builder.compile()


def main():
    input = readme_subgraph_input_data
    result = ReadmeSubgraph().run(input)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running ReadmeSubgraph: {e}")
        raise
