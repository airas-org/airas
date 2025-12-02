import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.features.analyzers.analyze_experiment_subgraph.nodes.analyze_experiment import (
    analyze_experiment,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
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

analytic_timed = lambda f: time_node("analyze_experiment_subgraph")(f)  # noqa: E731


class AnalyzeExperimentLLMMapping(BaseModel):
    analyze_experiment: LLM_MODEL = DEFAULT_NODE_LLMS["analyze_experiment"]


class AnalyzeExperimentSubgraphInputState(TypedDict, total=False):
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    experimental_code: ExperimentCode
    experimental_results: ExperimentalResults


class AnalyzeExperimentSubgraphOutputState(ExecutionTimeState, total=False):
    experimental_analysis: ExperimentalAnalysis


class AnalyzeExperimentSubgraphState(
    AnalyzeExperimentSubgraphInputState,
    AnalyzeExperimentSubgraphOutputState,
):
    pass


class AnalyzeExperimentSubgraph:
    def __init__(
        self,
        llm_client: LLMFacadeClient,
        llm_mapping: dict[str, str] | AnalyzeExperimentLLMMapping | None = None,
    ):
        if llm_mapping is None:
            self.llm_mapping = AnalyzeExperimentLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = AnalyzeExperimentLLMMapping.model_validate(
                    llm_mapping
                )
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, AnalyzeExperimentLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or AnalyzeExperimentLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.llm_client = llm_client
        check_api_key(llm_api_key_check=True)

    @analytic_timed
    async def _analyze_experiment(
        self, state: AnalyzeExperimentSubgraphState
    ) -> dict[str, ExperimentalAnalysis]:
        analysis_report = await analyze_experiment(
            llm_name=self.llm_mapping.analyze_experiment,
            research_hypothesis=state["research_hypothesis"],
            experimental_design=state["experimental_design"],
            experimental_code=state["experimental_code"],
            experimental_results=state["experimental_results"],
            llm_client=self.llm_client,
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


async def main():
    from airas.core.container import container
    from airas.features.analyzers.analyze_experiment_subgraph.input_data import (
        analyze_experiment_subgraph_input_data,
    )

    container.wire(modules=[__name__])

    try:
        llm_client = await container.llm_facade_client()

        subgraph = AnalyzeExperimentSubgraph(llm_client=llm_client)
        graph = subgraph.build_graph()
        result = await graph.ainvoke(analyze_experiment_subgraph_input_data)
        print(f"result: {result}")
    finally:
        await container.shutdown_resources()


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running AnalyzeExperimentSubgraph: {e}")
        raise
