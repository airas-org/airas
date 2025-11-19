import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.analysis.analyze_experiment_subgraph.nodes.analyze_experiment import (
    analyze_experiment,
)
from airas.features.analysis.analyze_experiment_subgraph.nodes.evaluate_method import (
    evaluate_method,
)
from airas.features.analysis.analyze_experiment_subgraph.nodes.select_best_iteration import (
    select_best_iteration,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_iteration import ExperimentEvaluation
from airas.types.research_session import ResearchSession
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

analytic_timed = lambda f: time_node("analyze_experiment_subgraph")(f)  # noqa: E731


class AnalyzeExperimentLLMMapping(BaseModel):
    analyze_experiment: LLM_MODEL = DEFAULT_NODE_LLMS["analyze_experiment"]
    evaluate_method: LLM_MODEL = DEFAULT_NODE_LLMS["evaluate_method"]


class AnalyzeExperimentSubgraphInputState(TypedDict, total=False):
    research_session: ResearchSession


class AnalyzeExperimentSubgraphHiddenState(TypedDict): ...


class AnalyzeExperimentSubgraphOutputState(TypedDict):
    research_session: ResearchSession


class AnalyzeExperimentSubgraphState(
    AnalyzeExperimentSubgraphInputState,
    AnalyzeExperimentSubgraphHiddenState,
    AnalyzeExperimentSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class AnalyzeExperimentSubgraph(BaseSubgraph):
    InputState = AnalyzeExperimentSubgraphInputState
    OutputState = AnalyzeExperimentSubgraphOutputState

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
    ) -> dict[str, ResearchSession]:
        research_session = state["research_session"]
        analysis_report = await analyze_experiment(
            llm_name=self.llm_mapping.analyze_experiment,
            research_session=research_session,
            llm_client=self.llm_client,
        )
        research_session.current_iteration.experimental_analysis.analysis_report = (
            analysis_report
        )
        return {"research_session": research_session}

    @analytic_timed
    async def _evaluate_method(
        self, state: AnalyzeExperimentSubgraphState
    ) -> dict[str, ResearchSession]:
        research_session = state["research_session"]
        method_feedback = await evaluate_method(
            llm_name=self.llm_mapping.evaluate_method,
            research_session=research_session,
            llm_client=self.llm_client,
        )
        if not research_session.current_iteration.experimental_analysis.evaluation:
            research_session.current_iteration.experimental_analysis.evaluation = (
                ExperimentEvaluation()
            )
        research_session.current_iteration.experimental_analysis.evaluation.method_feedback = method_feedback

        return {"research_session": research_session}

    @analytic_timed
    def _select_best_iteration(
        self, state: AnalyzeExperimentSubgraphState
    ) -> dict[str, ResearchSession]:
        research_session = select_best_iteration(state["research_session"])
        return {"research_session": research_session}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(AnalyzeExperimentSubgraphState)

        graph_builder.add_node("analyze_experiment", self._analyze_experiment)
        graph_builder.add_node("evaluate_method", self._evaluate_method)
        graph_builder.add_node("select_best_iteration", self._select_best_iteration)

        graph_builder.add_edge(START, "analyze_experiment")
        graph_builder.add_edge("analyze_experiment", "evaluate_method")
        graph_builder.add_edge("evaluate_method", "select_best_iteration")
        graph_builder.add_edge("select_best_iteration", END)

        return graph_builder.compile()


def main():
    from airas.features.analysis.analyze_experiment_subgraph.input_data import (
        analyze_experiment_subgraph_input_data,
    )

    result = AnalyzeExperimentSubgraph().run(
        analyze_experiment_subgraph_input_data,
    )

    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running AnalyzeExperimentSubgraph: {e}")
        raise
