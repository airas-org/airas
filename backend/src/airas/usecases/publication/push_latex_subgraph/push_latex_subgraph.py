import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.infra.github_client import GithubClient
from airas.usecases.publication.push_latex_subgraph.nodes.upload_latex_file import (
    upload_latex_file,
)

setup_logging()
logger = logging.getLogger(__name__)
record_execution_time = lambda f: time_node("push_latex_subgraph")(f)  # noqa: E731


class PushLatexSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    latex_text: str


class PushLatexSubgraphOutputState(ExecutionTimeState):
    is_upload_successful: bool


class PushLatexSubgraphState(
    PushLatexSubgraphInputState,
    PushLatexSubgraphOutputState,
    total=False,
):
    pass


# NOTE: Figures are no longer copied into the LaTeX directory here. The
# compile workflow and the Overleaf export materialize every figure PDF from
# .research/results/ and .research/diagrams/ into images/ at run time.
class PushLatexSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    ):
        self.github_client = github_client
        self.latex_template_name = latex_template_name

    @record_execution_time
    def _upload_latex_file(self, state: PushLatexSubgraphState) -> dict[str, bool]:
        is_upload_successful = upload_latex_file(
            github_config=state["github_config"],
            latex_text=state["latex_text"],
            latex_template_name=cast(LATEX_TEMPLATE_NAME, self.latex_template_name),
            github_client=self.github_client,
            paper_name="main",
        )
        return {"is_upload_successful": is_upload_successful}

    def build_graph(self):
        graph_builder = StateGraph(
            PushLatexSubgraphState,
            input_schema=PushLatexSubgraphInputState,
            output_schema=PushLatexSubgraphOutputState,
        )

        graph_builder.add_node("upload_latex_file", self._upload_latex_file)

        graph_builder.add_edge(START, "upload_latex_file")
        graph_builder.add_edge("upload_latex_file", END)

        return graph_builder.compile()
