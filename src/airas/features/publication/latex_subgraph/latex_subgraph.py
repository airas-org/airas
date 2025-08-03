import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

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
from airas.types.latex import LATEX_TEMPLATE_NAME
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
latex_timed = lambda f: time_node("latex_subgraph")(f)  # noqa: E731


class LatexSubgraphInputState(TypedDict):
    github_repository: dict[str, str]
    references_bib: str
    paper_content: dict[str, str]
    image_file_name_list: list[str]


class LatexSubgraphHiddenState(TypedDict):
    latex_template_text: str
    latex_content: dict[str, str]

    is_upload_successful: bool
    is_latex_compiled: bool
    latex_error_text: str
    is_successful: bool


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
        llm_name: str,
        latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024",
        paper_name: str = "generated_paper.pdf",
    ):
        self.llm_name = llm_name
        self.latex_template_name = latex_template_name
        self.paper_name = paper_name
        check_api_key(llm_api_key_check=True)

    def _convert_placeholders_to_citations(self, state: LatexSubgraphState) -> dict:
        paper_content = convert_placeholders_to_citations(
            paper_content=state["paper_content"],
            references_bib=state["references_bib"],
        )
        return {"paper_content": paper_content}

    # latexに与えるデータに変化する処理
    @latex_timed
    def _convert_to_latex_str(self, state: LatexSubgraphState) -> dict:
        latex_content = convert_to_latex_str(
            llm_name=cast(LLM_MODEL, self.llm_name),
            paper_content=state["paper_content"],
        )
        return {"latex_content": latex_content}

    # latex template　ファイルを取得する
    @latex_timed
    def _retrieve_latex_template(self, state: LatexSubgraphState) -> dict:
        latex_template_text = retrieve_github_repository_file(
            github_repository=state["github_repository"],
            file_path=f".research/latex/{self.latex_template_name}/template.tex",
        )
        return {"latex_template_text": latex_template_text}

    # latex templateに埋め込む
    @latex_timed
    def _embed_in_latex_template(self, state: LatexSubgraphState) -> dict:
        latex_text = embed_in_latex_template(
            latex_content=state["latex_content"],
            latex_template_text=state["latex_template_text"],
            references_bib=state["references_bib"],
            figures_name=state["image_file_name_list"],
            llm_name=cast(LLM_MODEL, self.llm_name),
        )
        return {"latex_text": latex_text}

    # latexファイルをアップロード
    @latex_timed
    def _upload_latex_file(self, state: LatexSubgraphState) -> dict[str, bool]:
        is_upload_successful = upload_latex_file(
            github_repository=state["github_repository"],
            latex_text=state["latex_text"],
            latex_template_name=cast(LATEX_TEMPLATE_NAME, self.latex_template_name),
        )
        return {"is_upload_successful": is_upload_successful}

    # latexのコンパイルを行うワークフローの実行
    @latex_timed
    def _execute_latex_compile(self, state: LatexSubgraphState) -> dict[str, bool]:
        is_latex_compiled = execute_latex_compile(
            github_repository=state["github_repository"],
            latex_template_name=cast(LATEX_TEMPLATE_NAME, self.latex_template_name),
        )
        return {"is_latex_compiled": is_latex_compiled}

    # latexのエラーファイルを取得する処理
    @latex_timed
    def _retrieve_latex_error_file(self, state: LatexSubgraphState) -> dict:
        latex_error_text = retrieve_github_repository_file(
            github_repository=state["github_repository"],
            file_path=f".research/latex/{self.latex_template_name}/latex-error.log",
        )
        return {"latex_error_text": latex_error_text}

    # latexの実行が成功したかを判定する処理
    @latex_timed
    def _is_execution_successful(self, state: LatexSubgraphState) -> dict:
        is_successful = is_execution_successful(
            llm_name=cast(LLM_MODEL, self.llm_name),
            latex_text=state["latex_text"],
            latex_error_text=state["latex_error_text"],
        )
        return {
            "is_successful": is_successful,
        }

    # Latexのエラーを修正する処理
    @latex_timed
    def _fix_latex_text(self, state: LatexSubgraphState) -> dict:
        latex_text = fix_latex_text(
            llm_name=cast(LLM_MODEL, self.llm_name),
            latex_text=state["latex_text"],
            latex_error_text=state["latex_error_text"],
        )
        return {
            "latex_text": latex_text,
        }

    @latex_timed
    def _is_fix_needed(self, state: LatexSubgraphState) -> str:
        if state["is_successful"]:
            return "end"
        else:
            return "fix"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(LatexSubgraphState)
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

        graph_builder.add_edge(START, "convert_placeholders_to_citations")
        graph_builder.add_edge(START, "retrieve_latex_template")
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
    llm_name = "o3-mini-2025-01-31"

    output = LatexSubgraph(
        llm_name=llm_name,
    ).run(latex_subgraph_input_data)

    print(output)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running LatexSubgraph: {e}")
        raise
