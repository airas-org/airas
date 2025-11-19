import logging
import time

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.publication.publish_html_subgraph.nodes.prepare_images_for_html import (
    prepare_images_for_html,
)
from airas.features.publication.publish_html_subgraph.nodes.upload_html import (
    upload_html,
)
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_session import ResearchSession
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
html_timed = lambda f: time_node("publish_html_subgraph")(f)  # noqa: E731


class PublishHtmlSubgraphInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo
    full_html: str
    research_session: ResearchSession


class PublishHtmlSubgraphHiddenState(TypedDict):
    html_upload: bool


class PublishHtmlSubgraphOutputState(TypedDict):
    github_pages_url: str


class PublishHtmlSubgraphState(
    PublishHtmlSubgraphInputState,
    PublishHtmlSubgraphHiddenState,
    PublishHtmlSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class PublishHtmlSubgraph(BaseSubgraph):
    InputState = PublishHtmlSubgraphInputState
    OutputState = PublishHtmlSubgraphOutputState

    def __init__(
        self,
        github_client: GithubClient,
    ):
        self.github_client = github_client

    @html_timed
    def _upload_html(self, state: PublishHtmlSubgraphState) -> dict[str, bool]:
        ok = upload_html(
            github_repository=state["github_repository_info"],
            full_html=state["full_html"],
            github_client=self.github_client,
        )
        return {"html_upload": ok}

    @html_timed
    async def _prepare_images_for_html(
        self, state: PublishHtmlSubgraphState
    ) -> dict[str, bool]:
        time.sleep(3)  # NOTE: Wait for GitHub changes to propagate.
        github_pages_url = await prepare_images_for_html(
            github_repository=state["github_repository_info"],
            research_session=state["research_session"],
            github_client=self.github_client,
        )
        return {
            "github_pages_url": github_pages_url,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(PublishHtmlSubgraphState)
        graph_builder.add_node("upload_html", self._upload_html)
        graph_builder.add_node("prepare_images_for_html", self._prepare_images_for_html)

        graph_builder.add_edge(START, "upload_html")
        graph_builder.add_edge("upload_html", "prepare_images_for_html")
        graph_builder.add_edge("prepare_images_for_html", END)

        return graph_builder.compile()


def main():
    from airas.features.publication.publish_html_subgraph.input_data import (
        publish_html_subgraph_input_data,
    )

    result = PublishHtmlSubgraph().run(publish_html_subgraph_input_data)
    print(f"Result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running PublishHtmlSubgraph: {e}")
        raise
