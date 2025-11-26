import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.generators.generate_code_subgraph.nodes.generate_experiment_code import (
    generate_experiment_code,
)
from airas.features.generators.generate_code_subgraph.nodes.generate_run_config import (
    generate_run_config,
)
from airas.features.generators.generate_code_subgraph.nodes.validate_experiment_code import (
    validate_experiment_code,
)
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.llm_client.openai_client import OPENAI_MODEL
from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_design import ExperimentalDesign
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.wandb import WandbConfig
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("generate_code_subgraph")(f)  # noqa: E731


class GenerateCodeLLMMapping(BaseModel):
    generate_run_config: OPENAI_MODEL = DEFAULT_NODE_LLMS["generate_run_config"]
    generate_experiment_code: OPENAI_MODEL = DEFAULT_NODE_LLMS[
        "generate_experiment_code"
    ]
    validate_experiment_code: OPENAI_MODEL = DEFAULT_NODE_LLMS[
        "validate_experiment_code"
    ]


class GenerateCodeSubgraphInputState(TypedDict):
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign


class GenerateCodeSubgraphHiddenState(TypedDict):
    code_validation: tuple[bool, str]
    code_validation_count: int


class GenerateCodeSubgraphOutputState(TypedDict):
    experiment_code: ExperimentCode


class GenerateCodeSubgraphState(
    GenerateCodeSubgraphInputState,
    GenerateCodeSubgraphHiddenState,
    GenerateCodeSubgraphOutputState,
):
    pass


class GenerateCodeSubgraph(BaseSubgraph):
    InputState = GenerateCodeSubgraphInputState
    OutputState = GenerateCodeSubgraphOutputState

    def __init__(
        self,
        wandb_config: WandbConfig,
        llm_client: LLMFacadeClient,
        llm_mapping: dict[str, str] | GenerateCodeLLMMapping | None = None,
        max_code_validations: int = 10,
    ):
        self.wandb_config = wandb_config
        self.max_code_validations = max_code_validations
        if llm_mapping is None:
            self.llm_mapping = GenerateCodeLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = GenerateCodeLLMMapping.model_validate(llm_mapping)
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, GenerateCodeLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or GenerateCodeLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.llm_client = llm_client
        check_api_key(
            llm_api_key_check=True,
        )

    @record_execution_time
    def _initialize(
        self, state: GenerateCodeSubgraphState
    ) -> dict[str, int | tuple[bool, str]]:
        return {
            "code_validation": (False, ""),
            "code_validation_count": 0,
        }

    @record_execution_time
    async def _generate_run_config(
        self, state: GenerateCodeSubgraphState
    ) -> dict[str, ExperimentCode]:
        run_configs = await generate_run_config(
            llm_name=self.llm_mapping.generate_run_config,
            llm_client=self.llm_client,
            research_hypothesis=state["research_hypothesis"],
            experimental_design=state["experimental_design"],
        )
        return {"experiment_code": ExperimentCode(run_configs=run_configs)}

    @record_execution_time
    async def _generate_experiment_code(
        self, state: GenerateCodeSubgraphState
    ) -> dict[str, ExperimentCode]:
        current_run_configs = state["experiment_code"].run_configs

        generated_code = await generate_experiment_code(
            llm_name=self.llm_mapping.generate_experiment_code,
            llm_client=self.llm_client,
            research_hypothesis=state["research_hypothesis"],
            experimental_design=state["experimental_design"],
            experiment_code=state["experiment_code"],
            wandb_config=self.wandb_config,
            code_validation=state.get("code_validation"),
        )
        generated_code.run_configs = current_run_configs

        return {"experiment_code": generated_code}

    @record_execution_time
    async def _validate_experiment_code(
        self, state: GenerateCodeSubgraphState
    ) -> dict[str, tuple[bool, str] | int]:
        code_validation = await validate_experiment_code(
            llm_name=self.llm_mapping.validate_experiment_code,
            llm_client=self.llm_client,
            research_hypothesis=state["research_hypothesis"],
            experimental_design=state["experimental_design"],
            experiment_code=state["experiment_code"],
            wandb_config=self.wandb_config,
        )
        return {
            "code_validation": code_validation,
            "code_validation_count": state["code_validation_count"] + 1,
        }

    def _should_continue_after_experiment_code_validation(
        self, state: GenerateCodeSubgraphState
    ) -> str:
        is_code_ready, issue = state["code_validation"]
        code_validation_count = state["code_validation_count"]

        if is_code_ready:
            logger.info("Code validation passed.")
            return "end"

        if code_validation_count >= self.max_code_validations:
            logger.warning(
                f"Maximum code validation attempts ({self.max_code_validations}) reached."
            )
            return "end"

        logger.warning(
            f"Code validation failed: {issue}. Re-running generate_experiment_code... (attempt {code_validation_count}/{self.max_code_validations})"
        )
        return "generate_experiment_code"

    def build_graph(self):
        graph_builder = StateGraph(
            GenerateCodeSubgraphState,
            input_schema=GenerateCodeSubgraphInputState,
            output_schema=GenerateCodeSubgraphOutputState,
        )
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node("generate_run_config", self._generate_run_config)
        graph_builder.add_node(
            "generate_experiment_code", self._generate_experiment_code
        )
        graph_builder.add_node(
            "validate_experiment_code", self._validate_experiment_code
        )

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "generate_run_config")
        graph_builder.add_edge("generate_run_config", "generate_experiment_code")
        graph_builder.add_edge("generate_experiment_code", "validate_experiment_code")
        graph_builder.add_conditional_edges(
            "validate_experiment_code",
            self._should_continue_after_experiment_code_validation,
            {
                "generate_experiment_code": "generate_experiment_code",
                "end": END,
            },
        )

        return graph_builder.compile()


async def main():
    from airas.core.container import container
    from airas.features.generators.generate_code_subgraph.input_data import (
        generate_code_subgraph_input_data,
    )

    container.wire(modules=[__name__])
    wandb_config = WandbConfig(entity="your-entity", project="your-project")

    try:
        llm_client = await container.llm_facade_client()
        result = await GenerateCodeSubgraph(
            llm_client=llm_client,
            wandb_config=wandb_config,
            max_code_validations=2,
        ).arun(generate_code_subgraph_input_data)

        print(f"Result: {result}")
        if "experiment_code" in result:
            print(
                f"Generated files: {list(result['experiment_code'].to_file_dict().keys())}"
            )
    finally:
        await container.shutdown_resources()


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running GenerateCodeSubgraph: {e}")
        raise
