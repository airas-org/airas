import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.create.create_experimental_design_subgraph.input_data import (
    create_experimental_design_subgraph_input_data,
)
from airas.create.create_experimental_design_subgraph.nodes.generate_advantage_criteria import (
    generate_advantage_criteria,
)
from airas.create.create_experimental_design_subgraph.nodes.generate_experiment_code import (
    generate_experiment_code,
)
from airas.create.create_experimental_design_subgraph.nodes.generate_experiment_details import (
    generate_experiment_details,
)
from airas.typing.paper import CandidatePaperInfo
from airas.utils.api_client.llm_facade_client import LLM_MODEL
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_experimental_design_timed = lambda f: time_node("create_experimental_design_subgraph")(f)  # noqa: E731


class CreateExperimentalDesignInputState(TypedDict):
    new_method: str
    base_method_text: CandidatePaperInfo
    base_experimental_code: str
    base_experimental_info: str


class CreateExperimentalDesignHiddenState(TypedDict):
    pass


class CreateExperimentalDesignOutputState(TypedDict):
    verification_policy: str
    experiment_details: str
    experiment_code: str


class CreateExperimentalDesignState(
    CreateExperimentalDesignInputState,
    CreateExperimentalDesignHiddenState,
    CreateExperimentalDesignOutputState,
    ExecutionTimeState,
):
    pass


class CreateExperimentalDesignSubgraph:
    def __init__(
        self, 
        llm_name: LLM_MODEL = "o3-mini-2025-01-31", 
    ):
        check_api_key(llm_api_key_check=True)
        self.llm_name = llm_name

    @create_experimental_design_timed
    def _generate_advantage_criteria_node(
        self, state: CreateExperimentalDesignState
    ) -> dict:
        verification_policy = generate_advantage_criteria(
            llm_name=self.llm_name,
            new_method=state["new_method"],
        )
        return {"verification_policy": verification_policy}

    @create_experimental_design_timed
    def _generate_experiment_details_node(
        self, state: CreateExperimentalDesignState
    ) -> dict:
        experimet_details = generate_experiment_details(
            llm_name=self.llm_name,
            verification_policy=state["verification_policy"],
            base_experimental_code=state["base_experimental_code"],
            base_experimental_info=state["base_experimental_info"],
        )
        return {"experiment_details": experimet_details}

    @create_experimental_design_timed
    def _generate_experiment_code_node(
        self, state: CreateExperimentalDesignState
    ) -> dict:
        experiment_code = generate_experiment_code(
            llm_name=self.llm_name,
            experiment_details=state["experiment_details"],
            base_experimental_code=state["base_experimental_code"],
            base_experimental_info=state["base_experimental_info"],
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

    def run(
        self, 
        input: CreateExperimentalDesignInputState, 
        config: dict | None = None
    ) -> CreateExperimentalDesignOutputState:
        graph = self.build_graph()
        full_result = graph.invoke(input, config=config or {})
        output_keys = CreateExperimentalDesignOutputState.__annotations__.keys()
        result = {k: full_result[k] for k in output_keys if k in full_result}
        return result


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
