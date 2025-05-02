import logging
from typing import TypedDict
from langgraph.graph import START, END, StateGraph
from langgraph.graph.graph import CompiledGraph

from airas.publication.readme_subgraph.nodes.readme_upload import readme_upload

from airas.utils.logging_utils import setup_logging
from airas.utils.execution_timers import time_node, ExecutionTimeState
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph

setup_logging()
logger = logging.getLogger(__name__)


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

    @time_node("readme_subgraph", "_readme_upload_node")
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
        # make nodes
        graph_builder.add_node("readme_upload_node", self._readme_upload_node)
        # make edges
        graph_builder.add_edge(START, "readme_upload_node")
        graph_builder.add_edge("readme_upload_node", END)

        return graph_builder.compile()


ReadmeUpload = create_wrapped_subgraph(
    ReadmeSubgraph,
    ReadmeSubgraphInputState,
    ReadmeSubgraphOutputState,
)

if __name__ == "__main__":
    github_repository = "auto-res2/experiment_script_matsuzawa"
    branch_name = "base-branch"

    readme_uploader = ReadmeUpload(
        github_repository=github_repository,
        branch_name=branch_name,
    )

    result = readme_uploader.run()
    print(f"result: {result}")
