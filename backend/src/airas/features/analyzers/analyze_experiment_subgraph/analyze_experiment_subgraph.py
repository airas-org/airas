import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.features.analyzers.analyze_experiment_subgraph.nodes.analyze_experiment import (
    analyze_experiment,
)
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS
from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_analysis import ExperimentalAnalysis
from airas.types.experimental_design import ExperimentalDesign
from airas.types.experimental_results import ExperimentalResults
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("analyze_experiment_subgraph")(f)  # noqa: E731


class AnalyzeExperimentLLMMapping(BaseModel):
    analyze_experiment: LLM_MODELS = DEFAULT_NODE_LLMS["analyze_experiment"]


class AnalyzeExperimentSubgraphInputState(TypedDict, total=False):
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    experiment_code: ExperimentCode
    experimental_results: ExperimentalResults


class AnalyzeExperimentSubgraphOutputState(ExecutionTimeState):
    experimental_analysis: ExperimentalAnalysis


class AnalyzeExperimentSubgraphState(
    AnalyzeExperimentSubgraphInputState,
    AnalyzeExperimentSubgraphOutputState,
    total=False,
):
    pass


class AnalyzeExperimentSubgraph:
    def __init__(
        self,
        langchain_client: LangChainClient,
        llm_mapping: AnalyzeExperimentLLMMapping | None = None,
    ):
        self.llm_mapping = llm_mapping or AnalyzeExperimentLLMMapping
        self.langchain_client = langchain_client
        check_api_key(llm_api_key_check=True)

    @record_execution_time
    async def _analyze_experiment(
        self, state: AnalyzeExperimentSubgraphState
    ) -> dict[str, ExperimentalAnalysis]:
        analysis_report = await analyze_experiment(
            llm_name=self.llm_mapping.analyze_experiment,
            research_hypothesis=state["research_hypothesis"],
            experimental_design=state["experimental_design"],
            experiment_code=state["experiment_code"],
            experimental_results=state["experimental_results"],
            langchain_client=self.langchain_client,
        )
        experimental_analysis = ExperimentalAnalysis(analysis_report=analysis_report)
        return {"experimental_analysis": experimental_analysis}

    def build_graph(self):
        graph_builder = StateGraph(
            AnalyzeExperimentSubgraphState,
            input_schema=AnalyzeExperimentSubgraphInputState,
            output_schema=AnalyzeExperimentSubgraphOutputState,
        )

        graph_builder.add_node("analyze_experiment", self._analyze_experiment)

        graph_builder.add_edge(START, "analyze_experiment")
        graph_builder.add_edge("analyze_experiment", END)

        return graph_builder.compile()
