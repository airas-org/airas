import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.features.github.nodes.dispatch_workflow import dispatch_workflow
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig
from airas.types.latex import LATEX_TEMPLATE_NAME
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
record_execution_time = lambda f: time_node("compile_latex_subgraph")(f)  # noqa: E731


class CompileLatexSubgraphInputState(TypedDict):
    github_config: GitHubConfig


class CompileLatexSubgraphOutputState(ExecutionTimeState):
    compile_latex_dispatched: bool
    paper_url: str | None


class CompileLatexSubgraphState(
    CompileLatexSubgraphInputState,
    CompileLatexSubgraphOutputState,
    total=False,
):
    pass


class CompileLatexSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024",
        paper_name: str = "generated_paper",
        workflow_file: str = "dev_compile_latex_with_claude_code.yml",
    ):
        self.github_client = github_client
        self.latex_template_name = latex_template_name
        self.paper_name = paper_name
        self.workflow_file = workflow_file

    @record_execution_time
    async def _compile_latex(self, state: CompileLatexSubgraphState) -> dict:
        github_config = state["github_config"]

        success = await dispatch_workflow(
            github_client=self.github_client,
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            branch_name=github_config.branch_name,
            workflow_file=self.workflow_file,
            inputs={
                "subdir": self.latex_template_name,
            },
        )

        if success:
            logger.info(f"Workflow {self.workflow_file} dispatched successfully")
            paper_url = (
                f"https://github.com/{github_config.github_owner}/"
                f"{github_config.repository_name}/blob/{github_config.branch_name}/"
                f".research/latex/{self.latex_template_name}/{self.paper_name}.pdf"
            )
            return {"compile_latex_dispatched": True, "paper_url": paper_url}
        else:
            logger.error(f"Failed to dispatch workflow: {self.workflow_file}")
            return {"compile_latex_dispatched": False, "paper_url": None}

    def build_graph(self):
        graph_builder = StateGraph(
            CompileLatexSubgraphState,
            input_schema=CompileLatexSubgraphInputState,
            output_schema=CompileLatexSubgraphOutputState,
        )
        graph_builder.add_node("compile_latex", self._compile_latex)

        graph_builder.add_edge(START, "compile_latex")
        graph_builder.add_edge("compile_latex", END)

        return graph_builder.compile()
