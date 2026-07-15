# NOTE: Unlike GenerateExperimentalDesignSubgraph, which creates a design from scratch
# based on prior research papers, this subgraph refines an existing design based on
# the full experiment history and instructions from a user (LLM or human).

import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.core.types.experiment_history import ExperimentHistory
from airas.core.types.experimental_design import ComputeEnvironment, ExperimentalDesign
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.infra.langchain_client import LangChainClient
from airas.usecases.generators.refine_experimental_design_subgraph.nodes.refine_experimental_design import (
    refine_experimental_design,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("refine_experimental_design_subgraph")(f)  # noqa: E731


class RefineExperimentalDesignLLMMapping(BaseModel):
    refine_experimental_design: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "refine_experimental_design"
    ]


class RefineExperimentalDesignSubgraphInputState(TypedDict):
    research_hypothesis: ResearchHypothesis
    experiment_history: ExperimentHistory
    design_instruction: str


class RefineExperimentalDesignSubgraphOutputState(ExecutionTimeState):
    experimental_design: ExperimentalDesign


class RefineExperimentalDesignState(
    RefineExperimentalDesignSubgraphInputState,
    RefineExperimentalDesignSubgraphOutputState,
):
    pass


class RefineExperimentalDesignSubgraph:
    def __init__(
        self,
        langchain_client: LangChainClient,
        compute_environment: ComputeEnvironment,
        llm_mapping: RefineExperimentalDesignLLMMapping | None = None,
        num_models_to_use: int = 2,
        num_datasets_to_use: int = 2,
        num_comparative_methods: int = 2,
    ):
        self.langchain_client = langchain_client
        self.llm_mapping = llm_mapping or RefineExperimentalDesignLLMMapping()
        self.compute_environment = compute_environment
        self.num_models_to_use = num_models_to_use
        self.num_datasets_to_use = num_datasets_to_use
        self.num_comparative_methods = num_comparative_methods

    @record_execution_time
    async def _refine_experiment_design(
        self, state: RefineExperimentalDesignState
    ) -> dict[str, ExperimentalDesign]:
        experimental_design = await refine_experimental_design(
            llm_config=self.llm_mapping.refine_experimental_design,
            llm_client=self.langchain_client,
            research_hypothesis=state["research_hypothesis"],
            experiment_history=state["experiment_history"],
            design_instruction=state["design_instruction"],
            compute_environment=self.compute_environment,
            num_models_to_use=self.num_models_to_use,
            num_datasets_to_use=self.num_datasets_to_use,
            num_comparative_methods=self.num_comparative_methods,
        )

        return {"experimental_design": experimental_design}

    def build_graph(self):
        graph_builder = StateGraph(
            RefineExperimentalDesignState,
            input_schema=RefineExperimentalDesignSubgraphInputState,
            output_schema=RefineExperimentalDesignSubgraphOutputState,
        )
        graph_builder.add_node(
            "refine_experiment_design", self._refine_experiment_design
        )

        graph_builder.add_edge(START, "refine_experiment_design")
        graph_builder.add_edge("refine_experiment_design", END)

        return graph_builder.compile()
