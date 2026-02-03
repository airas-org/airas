import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.core.types.latex import LATEX_TEMPLATE_NAME, LATEX_TEMPLATE_REPOSITORY_INFO
from airas.core.types.paper import ICLR2024PaperContent, PaperContent
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.usecases.github.nodes.retrieve_github_repository_file import (
    retrieve_github_repository_file,
)
from airas.usecases.publication.generate_latex_subgraph.nodes.convert_pandoc_citations_to_latex import (
    convert_pandoc_citations_to_latex,
)
from airas.usecases.publication.generate_latex_subgraph.nodes.convert_to_latex import (
    convert_to_latex,
)
from airas.usecases.publication.generate_latex_subgraph.nodes.embed_in_latex_template import (
    embed_in_latex_template,
)

setup_logging()
logger = logging.getLogger(__name__)
record_execution_time = lambda f: time_node("generate_latex_subgraph")(f)  # noqa: E731


class GenerateLatexLLMMapping(BaseModel):
    convert_to_latex: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG["convert_to_latex"]


class GenerateLatexSubgraphInputState(TypedDict):
    references_bib: str
    paper_content: PaperContent


class GenerateLatexSubgraphOutputState(ExecutionTimeState):
    latex_text: str


class GenerateLatexSubgraphState(
    GenerateLatexSubgraphInputState,
    GenerateLatexSubgraphOutputState,
    total=False,
):
    latex_template_text: str
    latex_paper_content: PaperContent


class GenerateLatexSubgraph:
    def __init__(
        self,
        langchain_client: LangChainClient,
        github_client: GithubClient,
        latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024",
        llm_mapping: GenerateLatexLLMMapping | None = None,
    ):
        self.llm_mapping = llm_mapping or GenerateLatexLLMMapping()
        self.langchain_client = langchain_client
        self.github_client = github_client
        self.latex_template_name = latex_template_name
        if latex_template_name == "iclr2024":
            self.paper_content_model = ICLR2024PaperContent
        else:
            raise ValueError(
                "Unsupported latex template for paper content conversion: "
                f"{latex_template_name}"
            )

    @record_execution_time
    def _retrieve_latex_template(
        self, state: GenerateLatexSubgraphState
    ) -> dict[str, str]:
        latex_template_text = retrieve_github_repository_file(
            github_repository=LATEX_TEMPLATE_REPOSITORY_INFO,
            file_path=f".research/latex/{self.latex_template_name}/template.tex",
            github_client=self.github_client,
        )
        return {"latex_template_text": latex_template_text}

    @record_execution_time
    def _convert_pandoc_citations_to_latex(
        self, state: GenerateLatexSubgraphState
    ) -> dict[str, PaperContent]:
        paper_content = convert_pandoc_citations_to_latex(
            paper_content=state["paper_content"],
            references_bib=state["references_bib"],
            paper_content_model=self.paper_content_model,
        )
        return {"paper_content": paper_content}

    @record_execution_time
    async def _convert_to_latex(
        self, state: GenerateLatexSubgraphState
    ) -> dict[str, PaperContent]:
        latex_paper_content = await convert_to_latex(
            llm_config=self.llm_mapping.convert_to_latex,
            langchain_client=self.langchain_client,
            paper_content=state["paper_content"],
            references_bib=state["references_bib"],
            latex_template_text=state["latex_template_text"],
            paper_content_model=self.paper_content_model,
        )
        return {"latex_paper_content": latex_paper_content}

    @record_execution_time
    def _embed_in_latex_template(
        self, state: GenerateLatexSubgraphState
    ) -> dict[str, str]:
        latex_text = embed_in_latex_template(
            latex_formatted_paper_content=state["latex_paper_content"],
            latex_template_text=state["latex_template_text"],
        )
        return {
            "latex_text": latex_text,
        }

    def build_graph(self):
        graph_builder = StateGraph(
            GenerateLatexSubgraphState,
            input_schema=GenerateLatexSubgraphInputState,
            output_schema=GenerateLatexSubgraphOutputState,
        )
        graph_builder.add_node("retrieve_latex_template", self._retrieve_latex_template)
        graph_builder.add_node(
            "convert_pandoc_citations_to_latex", self._convert_pandoc_citations_to_latex
        )
        graph_builder.add_node("convert_to_latex", self._convert_to_latex)
        graph_builder.add_node("embed_in_latex_template", self._embed_in_latex_template)

        graph_builder.add_edge(START, "retrieve_latex_template")
        graph_builder.add_edge(START, "convert_pandoc_citations_to_latex")
        graph_builder.add_edge("retrieve_latex_template", "convert_to_latex")
        graph_builder.add_edge("convert_pandoc_citations_to_latex", "convert_to_latex")
        graph_builder.add_edge("convert_to_latex", "embed_in_latex_template")
        graph_builder.add_edge("embed_in_latex_template", END)

        return graph_builder.compile()
