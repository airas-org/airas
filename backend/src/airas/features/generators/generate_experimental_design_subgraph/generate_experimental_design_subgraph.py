import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.generators.generate_experimental_design_subgraph.nodes.generate_experimental_design import (
    generate_experimental_design,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.experimental_design import ExperimentalDesign, RunnerConfig
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("generate_experimental_design_subgraph")(f)  # noqa: E731


class GenerateExperimentalDesignLLMMapping(BaseModel):
    generate_experimental_design: LLM_MODEL = DEFAULT_NODE_LLMS[
        "generate_experimental_design"
    ]


class GenerateExperimentalDesignSubgraphInputState(TypedDict):
    research_hypothesis: ResearchHypothesis


class GenerateExperimentalDesignHiddenState(TypedDict): ...


class GenerateExperimentalDesignSubgraphOutputState(TypedDict):
    experimental_design: ExperimentalDesign


class GenerateExperimentalDesignState(
    GenerateExperimentalDesignSubgraphInputState,
    GenerateExperimentalDesignHiddenState,
    GenerateExperimentalDesignSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class GenerateExperimentalDesignSubgraph(BaseSubgraph):
    InputState = GenerateExperimentalDesignSubgraphInputState
    OutputState = GenerateExperimentalDesignSubgraphOutputState

    def __init__(
        self,
        llm_client: LLMFacadeClient,
        runner_config: RunnerConfig,
        llm_mapping: dict[str, str]
        | GenerateExperimentalDesignLLMMapping
        | None = None,
        num_models_to_use: int = 2,
        num_datasets_to_use: int = 2,
        num_comparative_methods: int = 2,
    ):
        self.llm_client = llm_client
        self.runner_config = runner_config
        self.num_models_to_use = num_models_to_use
        self.num_datasets_to_use = num_datasets_to_use
        self.num_comparative_methods = num_comparative_methods
        if llm_mapping is None:
            self.llm_mapping = GenerateExperimentalDesignLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = GenerateExperimentalDesignLLMMapping.model_validate(
                    llm_mapping
                )
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, GenerateExperimentalDesignLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or GenerateExperimentalDesignLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        check_api_key(llm_api_key_check=True)

    @record_execution_time
    async def _generate_experiment_design(
        self, state: GenerateExperimentalDesignState
    ) -> dict[str, ExperimentalDesign]:
        experimental_design = await generate_experimental_design(
            llm_name=self.llm_mapping.generate_experimental_design,
            llm_client=self.llm_client,
            research_hypothesis=state["research_hypothesis"],
            runner_config=self.runner_config,
            num_models_to_use=self.num_models_to_use,
            num_datasets_to_use=self.num_datasets_to_use,
            num_comparative_methods=self.num_comparative_methods,
        )

        return {"experimental_design": experimental_design}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(GenerateExperimentalDesignState)
        graph_builder.add_node(
            "generate_experiment_design", self._generate_experiment_design
        )

        graph_builder.add_edge(START, "generate_experiment_design")
        graph_builder.add_edge("generate_experiment_design", END)

        return graph_builder.compile()


async def main():
    from airas.core.container import container
    from airas.features.generators.generate_experimental_design_subgraph.input_data import (
        default_runner_config,
        generate_experimental_design_subgraph_input_data,
    )

    container.wire(modules=[__name__])

    try:
        llm_client = await container.llm_facade_client()

        result = await GenerateExperimentalDesignSubgraph(
            llm_client=llm_client,
            runner_config=default_runner_config,
        ).arun(generate_experimental_design_subgraph_input_data)
        print(f"result: {result}")
    finally:
        await container.shutdown_resources()


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running GenerateExperimentalDesignSubgraph: {e}")
        raise
