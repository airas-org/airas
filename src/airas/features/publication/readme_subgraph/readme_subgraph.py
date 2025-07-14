import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph

from airas.core.base import BaseSubgraph
from airas.features.publication.readme_subgraph.input_data import (
    readme_subgraph_input_data,
)
from airas.features.publication.readme_subgraph.nodes.readme_upload import readme_upload
from airas.types.github import GitHubRepository
from airas.types.research_study import ResearchStudy
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
readme_timed = lambda f: time_node("readme_subgraph")(f)  # noqa: E731


# class ReadmeSubgraphInputState(TypedDict):
#     github_repository: str
#     branch_name: str
#     paper_content: dict
#     experiment_devin_url: str


# class ReadmeSubgraphHiddenState(TypedDict):
#     github_owner: str
#     repository_name: str


# class ReadmeSubgraphOutputState(TypedDict):
#     readme_upload_result: bool


class ReadmeSubgraphState(
    # ReadmeSubgraphInputState,
    # ReadmeSubgraphHiddenState,
    # ReadmeSubgraphOutputState,
    ExecutionTimeState,
):
    experiment_repository: GitHubRepository
    generate_paper_data: ResearchStudy
    readme_upload_result: bool


class ReadmeSubgraph(BaseSubgraph):
    def __init__(
        self,
    ) -> None:
        pass

    @readme_timed
    def _readme_upload_node(self, state: ReadmeSubgraphState) -> dict:
        experiment_repository = state["experiment_repository"]
        generated_paper_data = state["generate_paper_data"]
        readme_upload_result = readme_upload(
            github_owner=experiment_repository.github_owner,
            repository_name=experiment_repository.repository_name,
            branch_name=experiment_repository.branch_name,
            title=generated_paper_data.paper_body.title,
            abstract=generated_paper_data.paper_body.abstract,
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
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running ReadmeSubgraph: {e}")
        raise
