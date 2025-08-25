import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.publication.latex_subgraph.input_data import (
    latex_subgraph_input_data,
)
from airas.features.publication.latex_subgraph.nodes.convert_placeholders_to_citations import (
    convert_placeholders_to_citations,
)
from airas.features.publication.latex_subgraph.nodes.convert_to_latex import (
    convert_to_latex_str,
)
from airas.features.publication.latex_subgraph.nodes.embed_in_latex_template import (
    embed_in_latex_template,
)
from airas.features.publication.latex_subgraph.nodes.execute_latex_compile import (
    execute_latex_compile,
)
from airas.features.publication.latex_subgraph.nodes.fix_latex_text import (
    fix_latex_text,
)
from airas.features.publication.latex_subgraph.nodes.is_execution_successful import (
    is_execution_successful,
)
from airas.features.publication.latex_subgraph.nodes.retrieve_github_repository_file import (
    retrieve_github_repository_file,
)
from airas.features.publication.latex_subgraph.nodes.upload_latex_file import (
    upload_latex_file,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.latex import LATEX_TEMPLATE_NAME
from airas.types.paper import PaperContent
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
latex_timed = lambda f: time_node("latex_subgraph")(f)  # noqa: E731


class LatexLLMMapping(BaseModel):
    convert_to_latex: LLM_MODEL = DEFAULT_NODE_LLMS["convert_to_latex"]
    is_execution_successful: LLM_MODEL = DEFAULT_NODE_LLMS["is_execution_successful"]
    fix_latex_text: LLM_MODEL = DEFAULT_NODE_LLMS["fix_latex_text"]


class LatexSubgraphInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo
    references_bib: str
    paper_content: PaperContent


class LatexSubgraphHiddenState(TypedDict):
    latex_template_text: str
    latex_formatted_paper_content: PaperContent
    is_upload_successful: bool
    is_latex_compiled: bool
    latex_error_text: str
    is_successful: bool
    revision_count: int


class LatexSubgraphOutputState(TypedDict):
    latex_text: str


class LatexSubgraphState(
    LatexSubgraphInputState,
    LatexSubgraphHiddenState,
    LatexSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class LatexSubgraph(BaseSubgraph):
    InputState = LatexSubgraphInputState
    OutputState = LatexSubgraphOutputState

    def __init__(
        self,
        llm_mapping: dict[str, str] | LatexLLMMapping | None = None,
        latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024",
        paper_name: str = "generated_paper.pdf",
        max_revision_count: int = 3,
    ):
        if llm_mapping is None:
            self.llm_mapping = LatexLLMMapping()
        elif isinstance(llm_mapping, dict):
            self.llm_mapping = LatexLLMMapping(**llm_mapping)
        elif isinstance(llm_mapping, LatexLLMMapping):
            # すでに型が正しい場合も受け入れる
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or LatexLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.latex_template_name = latex_template_name
        self.paper_name = paper_name
        self.max_revision_count = max_revision_count
        check_api_key(llm_api_key_check=True)

    def _initialize(self, state: LatexSubgraphState) -> dict:
        """Initialize the latex subgraph with default revision count."""
        return {
            "revision_count": 1,
        }

    def _convert_placeholders_to_citations(self, state: LatexSubgraphState) -> dict:
        """Convert placeholder citations in paper content to proper citation format."""
        paper_content = convert_placeholders_to_citations(
            paper_content=state["paper_content"],
            references_bib=state["references_bib"],
        )
        return {"paper_content": paper_content}

    @latex_timed
    def _convert_to_latex_str(self, state: LatexSubgraphState) -> dict:
        """Convert paper content to LaTeX formatted string using LLM."""
        latex_formatted_paper_content = convert_to_latex_str(
            llm_name=self.llm_mapping.convert_to_latex,
            paper_content=state["paper_content"],
        )
        return {"latex_formatted_paper_content": latex_formatted_paper_content}

    @latex_timed
    def _retrieve_latex_template(self, state: LatexSubgraphState) -> dict:
        """Retrieve LaTeX template file from GitHub repository."""
        latex_template_text = retrieve_github_repository_file(
            github_repository=state["github_repository_info"],
            file_path=f".research/latex/{self.latex_template_name}/template.tex",
        )
        return {"latex_template_text": latex_template_text}

    @latex_timed
    def _embed_in_latex_template(self, state: LatexSubgraphState) -> dict:
        """Embed formatted paper content into LaTeX template."""
        latex_text = embed_in_latex_template(
            latex_formatted_paper_content=state["latex_formatted_paper_content"],
            latex_template_text=state["latex_template_text"],
        )
        return {"latex_text": latex_text}

    @latex_timed
    def _upload_latex_file(self, state: LatexSubgraphState) -> dict:
        """Upload LaTeX file to GitHub repository."""
        is_upload_successful = upload_latex_file(
            github_repository=state["github_repository_info"],
            latex_text=state["latex_text"],
            latex_template_name=cast(LATEX_TEMPLATE_NAME, self.latex_template_name),
        )
        return {"is_upload_successful": is_upload_successful}

    @latex_timed
    def _execute_latex_compile(self, state: LatexSubgraphState) -> dict:
        """Execute LaTeX compilation workflow in GitHub Actions."""
        is_latex_compiled = execute_latex_compile(
            github_repository=state["github_repository_info"],
            latex_template_name=cast(LATEX_TEMPLATE_NAME, self.latex_template_name),
        )
        return {"is_latex_compiled": is_latex_compiled}

    @latex_timed
    def _retrieve_latex_error_file(self, state: LatexSubgraphState) -> dict:
        """Retrieve LaTeX error log file from GitHub repository."""
        latex_error_text = retrieve_github_repository_file(
            github_repository=state["github_repository_info"],
            file_path=f".research/latex/{self.latex_template_name}/latex-error.log",
        )
        return {"latex_error_text": latex_error_text}

    @latex_timed
    def _is_execution_successful(self, state: LatexSubgraphState) -> dict:
        """Determine if LaTeX compilation was successful by analyzing error log."""
        is_successful = is_execution_successful(
            llm_name=self.llm_mapping.is_execution_successful,
            latex_text=state["latex_text"],
            latex_error_text=state["latex_error_text"],
        )
        return {
            "is_successful": is_successful,
        }

    @latex_timed
    def _fix_latex_text(self, state: LatexSubgraphState) -> dict:
        """Fix LaTeX errors using LLM analysis and increment revision count."""
        latex_text = fix_latex_text(
            llm_name=self.llm_mapping.fix_latex_text,
            latex_text=state["latex_text"],
            latex_error_text=state["latex_error_text"],
        )
        return {
            "latex_text": latex_text,
            "revision_count": state["revision_count"] + 1,
        }

    @latex_timed
    def _is_fix_needed(self, state: LatexSubgraphState) -> str:
        """Determine if further LaTeX fixes are needed based on success status and revision limit."""
        if state["is_successful"] or state["revision_count"] > self.max_revision_count:
            return "end"
        else:
            return "fix"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(LatexSubgraphState)
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node(
            "convert_placeholders_to_citations", self._convert_placeholders_to_citations
        )
        graph_builder.add_node("convert_to_latex", self._convert_to_latex_str)
        graph_builder.add_node("retrieve_latex_template", self._retrieve_latex_template)
        graph_builder.add_node("embed_in_latex_template", self._embed_in_latex_template)
        graph_builder.add_node("upload_latex_file", self._upload_latex_file)
        graph_builder.add_node("execute_latex_compile", self._execute_latex_compile)
        graph_builder.add_node(
            "retrieve_latex_error_file", self._retrieve_latex_error_file
        )
        graph_builder.add_node("is_execution_successful", self._is_execution_successful)
        graph_builder.add_node("fix_latex_text", self._fix_latex_text)

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "convert_placeholders_to_citations")
        graph_builder.add_edge("initialize", "retrieve_latex_template")
        graph_builder.add_edge("convert_placeholders_to_citations", "convert_to_latex")
        graph_builder.add_edge(
            ["retrieve_latex_template", "convert_to_latex"], "embed_in_latex_template"
        )
        graph_builder.add_edge("embed_in_latex_template", "upload_latex_file")
        graph_builder.add_edge("upload_latex_file", "execute_latex_compile")
        graph_builder.add_edge("execute_latex_compile", "retrieve_latex_error_file")
        graph_builder.add_edge("retrieve_latex_error_file", "is_execution_successful")
        graph_builder.add_conditional_edges(
            "is_execution_successful",
            self._is_fix_needed,
            {
                "fix": "fix_latex_text",
                "end": END,
            },
        )
        graph_builder.add_edge("fix_latex_text", "upload_latex_file")

        return graph_builder.compile()


def main():
    output = LatexSubgraph().run(latex_subgraph_input_data)

    print(output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running LatexSubgraph: {e}")
        raise
