import logging
from typing import Literal

from langgraph.graph import START, StateGraph
from langgraph.types import Command
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experimental_analysis import ExperimentalAnalysis
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper import ICLR2024PaperContent, PaperContent
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.infra.langchain_client import LangChainClient
from airas.usecases.writers.write_subgraph.nodes.generate_note import generate_note
from airas.usecases.writers.write_subgraph.nodes.refine_paper import refine_paper
from airas.usecases.writers.write_subgraph.nodes.write_paper import write_paper
from airas.usecases.writers.write_subgraph.prompts.iclr2024.refine_prompt import (
    refine_prompt as iclr2024_refine_prompt,
)
from airas.usecases.writers.write_subgraph.prompts.iclr2024.section_tips_prompt import (
    iclr2024_section_tips_prompt,
)
from airas.usecases.writers.write_subgraph.prompts.iclr2024.write_prompt import (
    write_prompt as iclr2024_write_prompt,
)

setup_logging()
logger = logging.getLogger(__name__)
record_execution_time = lambda f: time_node("write_subgraph")(f)  # noqa: E731


class WriteLLMMapping(BaseModel):
    write_paper: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG["write_paper"]
    refine_paper: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG["refine_paper"]


class WriteSubgraphInputState(TypedDict):
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    experiment_code: ExperimentCode
    experimental_results: ExperimentalResults
    experimental_analysis: ExperimentalAnalysis
    research_study_list: list[ResearchStudy]
    references_bib: str


class WriteSubgraphOutputState(ExecutionTimeState):
    paper_content: PaperContent

    # NOTE: Citation Format
    # This subgraph generates manuscript text using Pandoc/Quarto citation format: [@citation_key]
    # Examples:
    #   - Single citation: [@vaswani-2017-attention]
    #   - Multiple citations: [@vaswani-2017-attention; @devlin-2018-bert]
    #   - With page numbers: [@vaswani-2017-attention, p. 23]
    # These citations will be converted to appropriate formats by downstream subgraphs:
    #   - Latex Subgraph: [@key] → \cite{key}
    #   - HTML Subgraph: [@key] → <a href="#ref-key">[1]</a>


class WriteSubgraphState(
    WriteSubgraphInputState, WriteSubgraphOutputState, total=False
):
    note: str
    refinement_count: int


class WriteSubgraph:
    def __init__(
        self,
        langchain_client: LangChainClient,
        llm_mapping: WriteLLMMapping | None = None,
        paper_content_refinement_iterations: int = 2,
        latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024",
    ):
        self.llm_mapping = llm_mapping or WriteLLMMapping()
        self.paper_content_refinement_iterations = paper_content_refinement_iterations
        self.langchain_client = langchain_client
        self.latex_template_name = latex_template_name

        if latex_template_name == "iclr2024":
            self.write_prompt = iclr2024_write_prompt
            self.refine_prompt = iclr2024_refine_prompt
            self.section_tips_prompt = iclr2024_section_tips_prompt
            self.paper_content_model = ICLR2024PaperContent
            self.prompt_prefix = latex_template_name
        else:
            raise ValueError(
                f"Unsupported latex template for writer prompts: {latex_template_name}"
            )

    @record_execution_time
    def _initialize(self, state: WriteSubgraphState) -> dict[str, int]:
        return {
            "refinement_count": 0,
        }

    @record_execution_time
    def _generate_note(self, state: WriteSubgraphState) -> dict[str, str]:
        note = generate_note(
            research_hypothesis=state["research_hypothesis"],
            experimental_design=state["experimental_design"],
            experiment_code=state["experiment_code"],
            experimental_results=state["experimental_results"],
            experimental_analysis=state["experimental_analysis"],
            research_study_list=state["research_study_list"],
            references_bib=state["references_bib"],
        )
        return {"note": note}

    @record_execution_time
    async def _write_paper(self, state: WriteSubgraphState) -> dict[str, PaperContent]:
        paper_content = await write_paper(
            llm_config=self.llm_mapping.write_paper,
            langchain_client=self.langchain_client,
            note=state["note"],
            prompt_template=self.write_prompt,
            section_tips_prompt=self.section_tips_prompt,
            paper_content_model=self.paper_content_model,
            prompt_prefix=self.prompt_prefix,
        )
        return {"paper_content": paper_content}

    @record_execution_time
    async def _refine_paper(
        self, state: WriteSubgraphState
    ) -> Command[Literal["refine_paper", "__end__"]]:
        paper_content = await refine_paper(
            llm_config=self.llm_mapping.refine_paper,
            langchain_client=self.langchain_client,
            paper_content=state["paper_content"],
            note=state["note"],
            write_prompt_template=self.write_prompt,
            refine_prompt_template=self.refine_prompt,
            section_tips_prompt=self.section_tips_prompt,
            paper_content_model=self.paper_content_model,
            prompt_prefix=self.prompt_prefix,
        )

        new_refinement_count = state["refinement_count"] + 1
        goto: Literal["refine_paper", "__end__"]
        if new_refinement_count < self.paper_content_refinement_iterations:
            goto = "refine_paper"
        else:
            goto = "__end__"

        return Command(
            update={
                "paper_content": paper_content,
                "refinement_count": new_refinement_count,
            },
            goto=goto,
        )

    def build_graph(self):
        graph_builder = StateGraph(
            WriteSubgraphState,
            input_schema=WriteSubgraphInputState,
            output_schema=WriteSubgraphOutputState,
        )
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node("generate_note", self._generate_note)
        graph_builder.add_node("write_paper", self._write_paper)
        graph_builder.add_node("refine_paper", self._refine_paper)

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "generate_note")
        graph_builder.add_edge("generate_note", "write_paper")
        graph_builder.add_edge("write_paper", "refine_paper")

        return graph_builder.compile()
