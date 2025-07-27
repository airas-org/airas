import json
import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.create.create_experimental_design_subgraph.input_data import (
    create_experimental_design_subgraph_input_data,
)
from airas.features.create.create_experimental_design_subgraph.nodes.generate_advantage_criteria import (
    generate_advantage_criteria,
)
from airas.features.create.create_experimental_design_subgraph.nodes.generate_experiment_code import (
    generate_experiment_code,
)
from airas.features.create.create_experimental_design_subgraph.nodes.generate_experiment_details import (
    generate_experiment_details,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_str = "create_experimental_design_subgraph"
create_experimental_design_timed = lambda f: time_node(create_str)(f)  # noqa: E731


class CreateExperimentalDesignSubgraphInputState(TypedDict):
    new_method: str


class CreateExperimentalDesignSubgraphOutputState(TypedDict):
    verification_policy: str
    experiment_details: str
    experiment_code: str


class CreateExperimentalDesignState(
    CreateExperimentalDesignSubgraphInputState,
    CreateExperimentalDesignSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class CreateExperimentalDesignSubgraph(BaseSubgraph):
    InputState = CreateExperimentalDesignSubgraphInputState
    OutputState = CreateExperimentalDesignSubgraphOutputState

    def __init__(self, llm_name: LLM_MODEL = "o3-mini-2025-01-31"):
        self.llm_name = llm_name
        check_api_key(llm_api_key_check=True)

    @create_experimental_design_timed
    def _generate_advantage_criteria_node(
        self, state: CreateExperimentalDesignState
    ) -> dict:
        verification_policy = generate_advantage_criteria(
            llm_name=cast(LLM_MODEL, self.llm_name), new_method=state["new_method"]
        )
        return {"verification_policy": verification_policy}

    @create_experimental_design_timed
    def _generate_experiment_details_node(
        self, state: CreateExperimentalDesignState
    ) -> dict:
        experimet_details = generate_experiment_details(
            llm_name=cast(LLM_MODEL, self.llm_name),
            new_method=state["new_method"],
            verification_policy=state["verification_policy"],
        )
        return {"experiment_details": experimet_details}

    @create_experimental_design_timed
    def _generate_experiment_code_node(
        self, state: CreateExperimentalDesignState
    ) -> dict:
        experiment_code = generate_experiment_code(
            llm_name=cast(LLM_MODEL, self.llm_name),
            new_method=state["new_method"],
            experiment_details=state["experiment_details"],
        )
        return {"experiment_code": experiment_code}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateExperimentalDesignState)
        graph_builder.add_node(
            "generate_advantage_criteria_node", self._generate_advantage_criteria_node
        )
        graph_builder.add_node(
            "generate_experiment_details_node", self._generate_experiment_details_node
        )
        graph_builder.add_node(
            "generate_experiment_code_node", self._generate_experiment_code_node
        )

        graph_builder.add_edge(START, "generate_advantage_criteria_node")
        graph_builder.add_edge(
            "generate_advantage_criteria_node", "generate_experiment_details_node"
        )
        graph_builder.add_edge(
            "generate_experiment_details_node", "generate_experiment_code_node"
        )
        graph_builder.add_edge("generate_experiment_code_node", END)

        return graph_builder.compile()


def main():
    input = create_experimental_design_subgraph_input_data
    result = CreateExperimentalDesignSubgraph().run(input)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateExperimentalDesignSubgraph: {e}")
        raise
