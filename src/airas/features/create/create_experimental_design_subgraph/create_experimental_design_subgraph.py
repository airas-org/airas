import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.config.runtime_prompt import RuntimeKeyType
from airas.core.base import BaseSubgraph
from airas.features.create.create_experimental_design_subgraph.input_data import (
    create_experimental_design_subgraph_input_data,
)
from airas.features.create.create_experimental_design_subgraph.nodes.generate_experiment_code import (
    generate_experiment_code,
)
from airas.features.create.create_experimental_design_subgraph.nodes.generate_experiment_details import (
    generate_experiment_details,
)
from airas.features.create.create_experimental_design_subgraph.nodes.generate_experiment_strategy import (
    generate_experiment_strategy,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_str = "create_experimental_design_subgraph"
create_experimental_design_timed = lambda f: time_node(create_str)(f)  # noqa: E731


class CreateExperimentalDesignLLMMapping(BaseModel):
    generate_experiment_strategy: LLM_MODEL = DEFAULT_NODE_LLMS[
        "generate_experiment_strategy"
    ]
    generate_experiment_details: LLM_MODEL = DEFAULT_NODE_LLMS[
        "generate_experiment_details"
    ]
    generate_experiment_code: LLM_MODEL = DEFAULT_NODE_LLMS["generate_experiment_code"]


class CreateExperimentalDesignSubgraphInputState(TypedDict, total=False):
    new_method: ResearchHypothesis
    consistency_feedback: list[str]


class CreateExperimentalDesignHiddenState(TypedDict): ...


class CreateExperimentalDesignSubgraphOutputState(TypedDict):
    new_method: ResearchHypothesis


class CreateExperimentalDesignState(
    CreateExperimentalDesignSubgraphInputState,
    CreateExperimentalDesignHiddenState,
    CreateExperimentalDesignSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class CreateExperimentalDesignSubgraph(BaseSubgraph):
    InputState = CreateExperimentalDesignSubgraphInputState
    OutputState = CreateExperimentalDesignSubgraphOutputState

    def __init__(
        self,
        runtime_name: RuntimeKeyType = "default",
        llm_mapping: dict[str, str] | CreateExperimentalDesignLLMMapping | None = None,
    ):
        self.runtime_name = runtime_name
        if llm_mapping is None:
            self.llm_mapping = CreateExperimentalDesignLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = CreateExperimentalDesignLLMMapping.model_validate(
                    llm_mapping
                )
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, CreateExperimentalDesignLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or CreateExperimentalDesignLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        check_api_key(llm_api_key_check=True)

    @create_experimental_design_timed
    def _generate_experiment_strategy(
        self, state: CreateExperimentalDesignState
    ) -> dict[str, ResearchHypothesis]:
        new_method = generate_experiment_strategy(
            llm_name=self.llm_mapping.generate_experiment_strategy,
            new_method=state["new_method"],
            runtime_name=self.runtime_name,
            consistency_feedback=state.get("consistency_feedback"),
        )
        return {"new_method": new_method}

    @create_experimental_design_timed
    def _generate_experiment_details(
        self, state: CreateExperimentalDesignState
    ) -> dict[str, ResearchHypothesis]:
        new_method = generate_experiment_details(
            llm_name=self.llm_mapping.generate_experiment_details,
            new_method=state["new_method"],
            runtime_name=self.runtime_name,
            consistency_feedback=state.get("consistency_feedback"),
        )
        return {"new_method": new_method}

    @create_experimental_design_timed
    def _generate_experiment_code(
        self, state: CreateExperimentalDesignState
    ) -> dict[str, ResearchHypothesis]:
        new_method = generate_experiment_code(
            llm_name=self.llm_mapping.generate_experiment_code,
            new_method=state["new_method"],
            runtime_name=self.runtime_name,
            consistency_feedback=state.get("consistency_feedback"),
        )
        return {"new_method": new_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateExperimentalDesignState)
        graph_builder.add_node(
            "generate_experiment_strategy", self._generate_experiment_strategy
        )
        graph_builder.add_node(
            "generate_experiment_details", self._generate_experiment_details
        )
        graph_builder.add_node(
            "generate_experiment_code", self._generate_experiment_code
        )

        graph_builder.add_edge(START, "generate_experiment_strategy")
        graph_builder.add_edge(
            "generate_experiment_strategy", "generate_experiment_details"
        )
        graph_builder.add_edge(
            "generate_experiment_details", "generate_experiment_code"
        )
        graph_builder.add_edge("generate_experiment_code", END)

        return graph_builder.compile()


def main():
    input = create_experimental_design_subgraph_input_data
    result = CreateExperimentalDesignSubgraph().run(input)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateExperimentalDesignSubgraph: {e}")
        raise
