import argparse
import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.publication.readme_subgraph.nodes.readme_upload import readme_upload
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.github_utils.graph_wrapper import create_wrapped_subgraph
from airas.utils.logging_utils import setup_logging

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


def main():
    parser = argparse.ArgumentParser(
        description="Execute ReadmeSubgraph"
    )
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    pw = ReadmeUpload(
        github_repository=args.github_repository,
        branch_name=args.branch_name,
    )
    result = pw.run()
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running ReadmeSubgraph: {e}")
        raise
