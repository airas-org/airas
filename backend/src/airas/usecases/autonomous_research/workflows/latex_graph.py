import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubActionsAgent, GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper import PaperContent
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.usecases.github.poll_github_actions_subgraph.poll_github_actions_subgraph import (
    PollGithubActionsSubgraph,
)
from airas.usecases.publication.compile_latex_subgraph.compile_latex_subgraph import (
    CompileLatexLLMMapping,
    CompileLatexSubgraph,
)
from airas.usecases.publication.generate_latex_subgraph.generate_latex_subgraph import (
    GenerateLatexLLMMapping,
    GenerateLatexSubgraph,
)
from airas.usecases.publication.push_latex_subgraph.push_latex_subgraph import (
    PushLatexSubgraph,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("latex_graph")(f)  # noqa: E731

_LATEX_COMPILATION_RECURSION_LIMIT = 10000


class LaTeXGraphLLMMapping(BaseModel):
    generate_latex: GenerateLatexLLMMapping = GenerateLatexLLMMapping()
    compile_latex: CompileLatexLLMMapping = CompileLatexLLMMapping()


class LaTeXGraphInputState(TypedDict):
    github_config: GitHubConfig
    references_bib: str
    paper_content: PaperContent


class LaTeXGraphState(LaTeXGraphInputState, total=False):
    latex_text: str
    paper_url: str | None
    compile_latex_dispatched: bool


class LaTeXGraphOutputState(TypedDict):
    latex_text: str
    paper_url: str | None


class LaTeXGraph:
    def __init__(
        self,
        github_client: GithubClient,
        langchain_client: LangChainClient,
        latex_template_name: LATEX_TEMPLATE_NAME,
        github_actions_agent: GitHubActionsAgent,
        llm_mapping: LaTeXGraphLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.langchain_client = langchain_client
        self.latex_template_name = latex_template_name
        self.github_actions_agent = github_actions_agent
        self.llm_mapping = llm_mapping or LaTeXGraphLLMMapping()

    @record_execution_time
    async def _generate_latex(self, state: LaTeXGraphState) -> dict[str, str]:
        logger.info("=== Generate LaTeX ===")
        result = (
            await GenerateLatexSubgraph(
                langchain_client=self.langchain_client,
                github_client=self.github_client,
                latex_template_name=self.latex_template_name,
                llm_mapping=self.llm_mapping.generate_latex,
            )
            .build_graph()
            .ainvoke(
                {
                    "references_bib": state["references_bib"],
                    "paper_content": state["paper_content"],
                }
            )
        )
        return {"latex_text": result["latex_text"]}

    @record_execution_time
    async def _push_latex(self, state: LaTeXGraphState) -> dict[str, Any]:
        logger.info("=== Push LaTeX to GitHub ===")
        await (
            PushLatexSubgraph(
                github_client=self.github_client,
                latex_template_name=self.latex_template_name,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "latex_text": state["latex_text"],
                }
            )
        )
        return {}

    @record_execution_time
    async def _compile_latex(
        self, state: LaTeXGraphState
    ) -> dict[str, bool | str | None]:
        logger.info("=== Compile LaTeX ===")
        result = (
            await CompileLatexSubgraph(
                github_client=self.github_client,
                latex_template_name=self.latex_template_name,
                github_actions_agent=self.github_actions_agent,
                llm_mapping=self.llm_mapping.compile_latex,
            )
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )
        return {
            "compile_latex_dispatched": result["compile_latex_dispatched"],
            "paper_url": result.get("paper_url"),
        }

    @record_execution_time
    async def _poll_compile_latex(self, state: LaTeXGraphState) -> dict[str, Any]:
        logger.info("=== Poll Compile LaTeX Workflow ===")
        await (
            PollGithubActionsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {"github_config": state["github_config"]},
                {"recursion_limit": _LATEX_COMPILATION_RECURSION_LIMIT},
            )
        )
        return {}

    def build_graph(self):
        graph_builder = StateGraph(
            LaTeXGraphState,
            input_schema=LaTeXGraphInputState,
            output_schema=LaTeXGraphOutputState,
        )

        graph_builder.add_node("generate_latex", self._generate_latex)
        graph_builder.add_node("push_latex", self._push_latex)
        graph_builder.add_node("compile_latex", self._compile_latex)
        graph_builder.add_node("poll_compile_latex", self._poll_compile_latex)

        graph_builder.add_edge(START, "generate_latex")
        graph_builder.add_edge("generate_latex", "push_latex")
        graph_builder.add_edge("push_latex", "compile_latex")
        graph_builder.add_edge("compile_latex", "poll_compile_latex")
        graph_builder.add_edge("poll_compile_latex", END)

        return graph_builder.compile()
