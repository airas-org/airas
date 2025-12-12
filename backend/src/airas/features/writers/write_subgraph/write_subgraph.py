import logging
from typing import Literal

from langgraph.graph import START, StateGraph
from langgraph.types import Command
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.features.writers.write_subgraph.nodes.generate_note import generate_note
from airas.features.writers.write_subgraph.nodes.refine_paper import refine_paper
from airas.features.writers.write_subgraph.nodes.write_paper import write_paper
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS
from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_analysis import ExperimentalAnalysis
from airas.types.experimental_design import ExperimentalDesign
from airas.types.experimental_results import ExperimentalResults
from airas.types.paper import PaperContent
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
record_execution_time = lambda f: time_node("write_subgraph")(f)  # noqa: E731


class WriteLLMMapping(BaseModel):
    write_paper: LLM_MODELS = DEFAULT_NODE_LLMS["write_paper"]
    refine_paper: LLM_MODELS = DEFAULT_NODE_LLMS["refine_paper"]


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
        llm_mapping: dict[str, str] | WriteLLMMapping | None = None,
        writing_refinement_rounds: int = 2,
    ):
        if llm_mapping is None:
            self.llm_mapping = WriteLLMMapping()
        elif isinstance(llm_mapping, dict):
            self.llm_mapping = WriteLLMMapping(**llm_mapping)
        elif isinstance(llm_mapping, WriteLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or WriteLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.writing_refinement_rounds = writing_refinement_rounds
        self.langchain_client = langchain_client
        check_api_key(llm_api_key_check=True)

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
            llm_name=self.llm_mapping.write_paper,
            langchain_client=self.langchain_client,
            note=state["note"],
        )
        return {"paper_content": paper_content}

    @record_execution_time
    async def _refine_paper(
        self, state: WriteSubgraphState
    ) -> Command[Literal["refine_paper", "__end__"]]:
        paper_content = await refine_paper(
            llm_name=self.llm_mapping.refine_paper,
            langchain_client=self.langchain_client,
            paper_content=state["paper_content"],  # type: ignore[typeddict-item]
            note=state["note"],
        )

        new_refinement_count = state["refinement_count"] + 1
        goto: Literal["refine_paper", "__end__"]
        if new_refinement_count < self.writing_refinement_rounds:
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
