import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.core.types.experiment_history import (
    ExperimentCycleDecision,
    ExperimentHistory,
)
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.infra.langchain_client import LangChainClient
from airas.usecases.analyzers.decide_experiment_cycle_subgraph.nodes.decide_experiment_cycle import (
    decide_experiment_cycle,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("decide_experiment_cycle_subgraph")(f)  # noqa: E731


class DecideExperimentCycleLLMMapping(BaseModel):
    decide_experiment_cycle: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "decide_experiment_cycle"
    ]


class DecideExperimentCycleSubgraphInputState(TypedDict):
    research_hypothesis: ResearchHypothesis
    experiment_history: ExperimentHistory


class DecideExperimentCycleSubgraphOutputState(ExecutionTimeState):
    experiment_cycle_decision: ExperimentCycleDecision


class DecideExperimentCycleSubgraphState(
    DecideExperimentCycleSubgraphInputState,
    DecideExperimentCycleSubgraphOutputState,
):
    pass


class DecideExperimentCycleSubgraph:
    def __init__(
        self,
        langchain_client: LangChainClient,
        llm_mapping: DecideExperimentCycleLLMMapping | None = None,
    ):
        self.langchain_client = langchain_client
        self.llm_mapping = llm_mapping or DecideExperimentCycleLLMMapping()

    @record_execution_time
    async def _decide_experiment_cycle(
        self, state: DecideExperimentCycleSubgraphState
    ) -> dict[str, ExperimentCycleDecision]:
        decision = await decide_experiment_cycle(
            llm_config=self.llm_mapping.decide_experiment_cycle,
            llm_client=self.langchain_client,
            research_hypothesis=state["research_hypothesis"],
            experiment_history=state["experiment_history"],
        )
        return {"experiment_cycle_decision": decision}

    def build_graph(self):
        graph_builder = StateGraph(
            DecideExperimentCycleSubgraphState,
            input_schema=DecideExperimentCycleSubgraphInputState,
            output_schema=DecideExperimentCycleSubgraphOutputState,
        )

        graph_builder.add_node("decide_experiment_cycle", self._decide_experiment_cycle)

        graph_builder.add_edge(START, "decide_experiment_cycle")
        graph_builder.add_edge("decide_experiment_cycle", END)

        return graph_builder.compile()
