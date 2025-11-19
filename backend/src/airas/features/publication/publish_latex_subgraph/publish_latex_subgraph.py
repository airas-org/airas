import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.publication.publish_latex_subgraph.nodes.compile_latex import (
    compile_latex,
)
from airas.features.publication.publish_latex_subgraph.nodes.embed_in_latex_template import (
    embed_in_latex_template,
)
from airas.features.publication.publish_latex_subgraph.nodes.retrieve_github_repository_file import (
    retrieve_github_repository_file,
)
from airas.features.publication.publish_latex_subgraph.nodes.upload_latex_file import (
    upload_latex_file,
)
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.latex import LATEX_TEMPLATE_NAME, LATEX_TEMPLATE_REPOSITORY_INFO
from airas.types.paper import PaperContent
from airas.types.research_session import ResearchSession
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
latex_timed = lambda f: time_node("publish_latex_subgraph")(f)  # noqa: E731


class PublishLatexSubgraphInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo
    research_session: ResearchSession  # NOTE: It's necessary for compile_latex
    latex_formatted_paper_content: PaperContent  # From GenerateLatexSubgraph


class PublishLatexSubgraphHiddenState(TypedDict):
    latex_template_text: str
    latex_text: str
    is_upload_successful: bool
    is_compiled: bool


class PublishLatexSubgraphOutputState(TypedDict):
    is_upload_successful: bool
    is_compiled: bool


class PublishLatexSubgraphState(
    PublishLatexSubgraphInputState,
    PublishLatexSubgraphHiddenState,
    PublishLatexSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class PublishLatexSubgraph(BaseSubgraph):
    InputState = PublishLatexSubgraphInputState
    OutputState = PublishLatexSubgraphOutputState

    def __init__(
        self,
        github_client: GithubClient,
        latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024",
        paper_name: str = "generated_paper.pdf",
    ):
        self.github_client = github_client
        self.latex_template_name = latex_template_name
        self.paper_name = paper_name

    @latex_timed
    def _retrieve_latex_template(
        self, state: PublishLatexSubgraphState
    ) -> dict[str, str]:
        latex_template_text = retrieve_github_repository_file(
            github_repository=LATEX_TEMPLATE_REPOSITORY_INFO,
            file_path=f".research/latex/{self.latex_template_name}/template.tex",
            github_client=self.github_client,
        )
        return {"latex_template_text": latex_template_text}

    @latex_timed
    def _embed_in_latex_template(
        self, state: PublishLatexSubgraphState
    ) -> dict[str, str]:
        latex_text = embed_in_latex_template(
            latex_formatted_paper_content=state["latex_formatted_paper_content"],
            latex_template_text=state["latex_template_text"],
        )
        return {"latex_text": latex_text}

    @latex_timed
    def _upload_latex_file(self, state: PublishLatexSubgraphState) -> dict[str, bool]:
        is_upload_successful = upload_latex_file(
            github_repository=state["github_repository_info"],
            latex_text=state["latex_text"],
            latex_template_name=cast(LATEX_TEMPLATE_NAME, self.latex_template_name),
            github_client=self.github_client,
        )
        return {"is_upload_successful": is_upload_successful}

    @latex_timed
    async def _compile_latex(self, state: PublishLatexSubgraphState) -> dict[str, bool]:
        is_compiled = await compile_latex(
            github_repository_info=state["github_repository_info"],
            research_session=state["research_session"],
            latex_template_name=cast(LATEX_TEMPLATE_NAME, self.latex_template_name),
            github_client=self.github_client,
        )
        return {"is_compiled": is_compiled}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(PublishLatexSubgraphState)

        graph_builder.add_node("retrieve_latex_template", self._retrieve_latex_template)
        graph_builder.add_node("embed_in_latex_template", self._embed_in_latex_template)
        graph_builder.add_node("upload_latex_file", self._upload_latex_file)
        graph_builder.add_node("compile_latex", self._compile_latex)

        graph_builder.add_edge(START, "retrieve_latex_template")
        graph_builder.add_edge("retrieve_latex_template", "embed_in_latex_template")
        graph_builder.add_edge("embed_in_latex_template", "upload_latex_file")
        graph_builder.add_edge("upload_latex_file", "compile_latex")
        graph_builder.add_edge("compile_latex", END)

        return graph_builder.compile()


def main():
    from airas.features.publication.publish_latex_subgraph.input_data import (
        publish_latex_subgraph_input_data,
    )

    output = PublishLatexSubgraph(latex_template_name="agents4science_2025").run(
        publish_latex_subgraph_input_data
    )
    print(output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running PublishLatexSubgraph: {e}")
        raise
