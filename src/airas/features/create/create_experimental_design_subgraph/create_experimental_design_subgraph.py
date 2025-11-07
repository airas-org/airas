import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.config.runner_type_info import RunnerType
from airas.core.base import BaseSubgraph
from airas.features.create.create_experimental_design_subgraph.nodes.generate_experiment_design import (
    generate_experiment_design,
)
from airas.features.create.create_experimental_design_subgraph.nodes.generate_experiment_runs import (
    generate_experiment_runs,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_session import ResearchSession
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_str = "create_experimental_design_subgraph"
create_experimental_design_timed = lambda f: time_node(create_str)(f)  # noqa: E731


class CreateExperimentalDesignLLMMapping(BaseModel):
    generate_experiment_design: LLM_MODEL = DEFAULT_NODE_LLMS[
        "generate_experiment_design"
    ]


class CreateExperimentalDesignSubgraphInputState(TypedDict, total=False):
    research_session: ResearchSession
    github_repository_info: GitHubRepositoryInfo


class CreateExperimentalDesignHiddenState(TypedDict): ...


class CreateExperimentalDesignSubgraphOutputState(TypedDict):
    research_session: ResearchSession


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
        num_models_to_use: int = 2,
        num_datasets_to_use: int = 2,
        num_comparative_methods: int = 2,
    ):
        self.runner_type = runner_type
        self.num_models_to_use = num_models_to_use
        self.num_datasets_to_use = num_datasets_to_use
        self.num_comparative_methods = num_comparative_methods
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
    def _generate_experiment_design(
        self, state: CreateExperimentalDesignState
    ) -> dict[str, ResearchSession]:
        research_session = state["research_session"]
        is_first_iteration = len(research_session.iterations) == 1

        experiment_design = generate_experiment_design(
            llm_name=self.llm_mapping.generate_experiment_design,
            research_session=research_session,
            runner_type=cast(RunnerType, self.runner_type),
            num_models_to_use=self.num_models_to_use,
            num_datasets_to_use=self.num_datasets_to_use,
            num_comparative_methods=self.num_comparative_methods
            if is_first_iteration
            else 0,
            github_repository_info=state["github_repository_info"],
        )

        # HACK: Running solely to change the hyperparameters during loop execution.
        # However, it's not ideal that it implicitly fixes the fields.
        FIXED_FIELDS = (
            "models_to_use",
            "datasets_to_use",
            "evaluation_metrics",
            "comparative_methods",
        )
        if not is_first_iteration:
            first_design = research_session.iterations[0].experimental_design
            for field in FIXED_FIELDS:
                setattr(experiment_design, field, getattr(first_design, field))

        research_session.current_iteration.experimental_design = experiment_design
        return {"research_session": research_session}

    @create_experimental_design_timed
    def _geneate_experiment_runs(
        self, state: CreateExperimentalDesignState
    ) -> dict[str, ResearchSession]:
        research_session = state["research_session"]
        experiment_runs = generate_experiment_runs(
            research_session=research_session,
        )
        research_session.current_iteration.experiment_runs = experiment_runs
        return {"research_session": research_session}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateExperimentalDesignState)
        graph_builder.add_node(
            "generate_experiment_design", self._generate_experiment_design
        )
        graph_builder.add_node(
            "generate_experiment_runs", self._geneate_experiment_runs
        )

        graph_builder.add_edge(START, "generate_experiment_design")
        graph_builder.add_edge("generate_experiment_design", "generate_experiment_runs")
        graph_builder.add_edge("generate_experiment_runs", END)

        return graph_builder.compile()


def main():
    from airas.features.create.create_experimental_design_subgraph.input_data import (
        create_experimental_design_subgraph_input_data,
    )
    from airas.services.api_client.api_clients_container import sync_container

    sync_container.wire(modules=[__name__])

    input = create_experimental_design_subgraph_input_data
    result = CreateExperimentalDesignSubgraph().run(input)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateExperimentalDesignSubgraph: {e}")
        raise
