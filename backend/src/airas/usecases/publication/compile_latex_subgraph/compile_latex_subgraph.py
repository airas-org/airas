import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.core.types.coding_agent import GitHubActionsCodingAgent
from airas.core.types.github import GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.dispatch_workflow import dispatch_workflow

setup_logging()
logger = logging.getLogger(__name__)
record_execution_time = lambda f: time_node("compile_latex_subgraph")(f)  # noqa: E731


class CompileLatexLLMMapping(BaseModel):
    compile_latex: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG["compile_latex"]


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
        github_actions_latex_compile_agent: GitHubActionsCodingAgent = "claude_code",
        llm_mapping: CompileLatexLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.latex_template_name = latex_template_name
        self.paper_name = paper_name
        self.github_actions_coding_agent = github_actions_latex_compile_agent
        if github_actions_latex_compile_agent == "open_code":
            self.workflow_file = "dev_compile_latex_with_open_code.yml"
            # `llm_mapping` が未指定の場合は後方互換性のためデフォルトにフォールバックする
            self.llm_mapping = llm_mapping or CompileLatexLLMMapping()
        elif github_actions_latex_compile_agent == "claude_code":
            self.workflow_file = "dev_compile_latex_with_claude_code.yml"
            if llm_mapping is not None:
                raise ValueError(
                    "llm_mapping must be None when github_actions_latex_compile_agent is 'claude_code'"
                )
            self.llm_mapping = None
        else:
            raise ValueError(
                f"Invalid github_actions_latex_compile_agent: {github_actions_latex_compile_agent}. "
                "Choose either 'open_code' or 'claude_code'."
            )

    @record_execution_time
    async def _compile_latex(self, state: CompileLatexSubgraphState) -> dict:
        github_config = state["github_config"]
        inputs = {
            "subdir": self.latex_template_name,
            "branch_name": github_config.branch_name,
        }
        if self.github_actions_coding_agent == "open_code":
            inputs["model_name"] = self.llm_mapping.compile_latex.llm_name
        success = await dispatch_workflow(
            github_client=self.github_client,
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            branch_name=github_config.branch_name,
            workflow_file=self.workflow_file,
            inputs=inputs,
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
