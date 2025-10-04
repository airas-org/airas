import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.config.runner_type_info import RunnerType
from airas.core.base import BaseSubgraph
from airas.features.create.create_experimental_design_subgraph.input_data import (
    create_experimental_design_subgraph_input_data,
)
from airas.features.create.create_experimental_design_subgraph.nodes.generate_experiment_strategy import (
    generate_experiment_strategy,
)
from airas.features.create.create_experimental_design_subgraph.nodes.generate_experiments import (
    generate_experiments,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
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
    generate_experiments: LLM_MODEL = DEFAULT_NODE_LLMS["generate_experiments"]


class CreateExperimentalDesignSubgraphInputState(TypedDict, total=False):
    new_method: ResearchHypothesis
    consistency_feedback: list[str]
    github_repository_info: GitHubRepositoryInfo


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
        runner_type: RunnerType = "ubuntu-latest",
        llm_mapping: dict[str, str] | CreateExperimentalDesignLLMMapping | None = None,
        num_experiments: int = 5,
    ):
        self.runner_type = runner_type
        self.num_experiments = num_experiments
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
    def _prepare_iteration_history(
        self, state: CreateExperimentalDesignState
    ) -> dict[str, ResearchHypothesis | str | None]:
        current_method = state["new_method"]
        if current_method.experimental_design is not None:
            previous_method = current_method.model_copy(deep=True)
            previous_method.iteration_history = None

            current_method.iteration_history = current_method.iteration_history or []
            current_method.iteration_history.append(previous_method)

            for field in (
                "experimental_design",
                "experimental_results",
                "experimental_analysis",
            ):
                setattr(current_method, field, None)

        return {
            "new_method": current_method,
        }

    @create_experimental_design_timed
    def _generate_experiment_strategy(
        self, state: CreateExperimentalDesignState
    ) -> dict[str, ResearchHypothesis]:
        new_method = generate_experiment_strategy(
            llm_name=self.llm_mapping.generate_experiment_strategy,
            new_method=state["new_method"],
            runner_type=cast(RunnerType, self.runner_type),
            github_repository_info=state["github_repository_info"],
            feedback_text=feedback[-1]
            if (feedback := state.get("consistency_feedback"))
            else None,
        )
        return {"new_method": new_method}

    @create_experimental_design_timed
    def _generate_experiments(
        self, state: CreateExperimentalDesignState
    ) -> dict[str, ResearchHypothesis]:
        new_method = generate_experiments(
            llm_name=self.llm_mapping.generate_experiments,
            new_method=state["new_method"],
            runner_type=cast(RunnerType, self.runner_type),
            github_repository_info=state["github_repository_info"],
            num_experiments=self.num_experiments,
            feedback_text=feedback[-1]
            if (feedback := state.get("consistency_feedback"))
            else None,
        )
        return {"new_method": new_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateExperimentalDesignState)
        graph_builder.add_node(
            "prepare_iteration_history", self._prepare_iteration_history
        )
        graph_builder.add_node(
            "generate_experiment_strategy", self._generate_experiment_strategy
        )
        graph_builder.add_node("generate_experiments", self._generate_experiments)

        graph_builder.add_edge(START, "prepare_iteration_history")
        graph_builder.add_edge(
            "prepare_iteration_history", "generate_experiment_strategy"
        )
        graph_builder.add_edge("generate_experiment_strategy", "generate_experiments")
        graph_builder.add_edge("generate_experiments", END)

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
