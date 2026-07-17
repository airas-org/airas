import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.infra.github_client import GithubClient
from airas.usecases.publication.open_in_overleaf_subgraph.nodes.build_overleaf_export import (
    build_overleaf_export,
)
from airas.usecases.publication.open_in_overleaf_subgraph.nodes.collect_latex_project_files import (
    collect_latex_project_files,
)

setup_logging()
logger = logging.getLogger(__name__)
record_execution_time = lambda f: time_node("open_in_overleaf_subgraph")(f)  # noqa: E731


class OpenInOverleafSubgraphInputState(TypedDict):
    github_config: GitHubConfig


class OpenInOverleafSubgraphOutputState(ExecutionTimeState):
    overleaf_html: str
    file_names: list[str]


class OpenInOverleafSubgraphState(
    OpenInOverleafSubgraphInputState,
    OpenInOverleafSubgraphOutputState,
    total=False,
):
    latex_files: dict[str, bytes]


# NOTE: Overleaf 自体は GitHub を要求しない（zip を base64 の data URL としてブラウザから
# POST するだけ）が、このサブグラフは実験リポジトリの .research/latex/{template}/ に
# push_latex 済みであることを前提にしている。main.tex・図版（GitHub Actions の実験成果物）・
# テンプレート資材（.cls / .bst 等）がそこに揃っているため。
# TODO: push_latex 前でも使えるように、latex_text を直接受け取る変種も検討する。
# その場合テンプレート資材は airas-org/airas-template から取得できるが、図版は手元に
# ないため含められない（\includegraphics が壊れた状態で Overleaf に渡る）。
class OpenInOverleafSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    ):
        self.github_client = github_client
        self.latex_template_name = latex_template_name

    @record_execution_time
    def _collect_latex_project_files(
        self, state: OpenInOverleafSubgraphState
    ) -> dict[str, dict[str, bytes] | list[str]]:
        latex_files = collect_latex_project_files(
            github_config=state["github_config"],
            latex_template_name=cast(LATEX_TEMPLATE_NAME, self.latex_template_name),
            github_client=self.github_client,
        )
        return {
            "latex_files": latex_files,
            "file_names": sorted(latex_files),
        }

    @record_execution_time
    def _build_overleaf_export(
        self, state: OpenInOverleafSubgraphState
    ) -> dict[str, str]:
        github_config = state["github_config"]
        overleaf_html = build_overleaf_export(
            latex_files=state["latex_files"],
            project_name=f"{github_config.repository_name}-{github_config.branch_name}",
        )
        return {"overleaf_html": overleaf_html}

    def build_graph(self):
        graph_builder = StateGraph(
            OpenInOverleafSubgraphState,
            input_schema=OpenInOverleafSubgraphInputState,
            output_schema=OpenInOverleafSubgraphOutputState,
        )
        graph_builder.add_node(
            "collect_latex_project_files", self._collect_latex_project_files
        )
        graph_builder.add_node("build_overleaf_export", self._build_overleaf_export)

        graph_builder.add_edge(START, "collect_latex_project_files")
        graph_builder.add_edge("collect_latex_project_files", "build_overleaf_export")
        graph_builder.add_edge("build_overleaf_export", END)

        return graph_builder.compile()
