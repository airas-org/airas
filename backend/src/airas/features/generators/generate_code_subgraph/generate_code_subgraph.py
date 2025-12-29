import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.features.generators.generate_code_subgraph.nodes.generate_experiment_code import (
    generate_experiment_code,
)
from airas.features.generators.generate_code_subgraph.nodes.generate_run_config import (
    generate_run_config,
)
from airas.features.generators.generate_code_subgraph.nodes.validate_experiment_code import (
    validate_experiment_code,
)
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS
from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_design import ExperimentalDesign
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.wandb import WandbConfig
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("generate_code_subgraph")(f)  # noqa: E731


class GenerateCodeLLMMapping(BaseModel):
    # TODO: Support reasoning_effort="high" for OpenAI reasoning models (o1, o3, o4)
    # and thinking_budget for Anthropic extended thinking models to improve code generation quality.
    # Currently, OpenAIParams are passed but not utilized in LangChainClient.structured_outputs.
    generate_run_config: LLM_MODELS = DEFAULT_NODE_LLMS["generate_run_config"]
    generate_experiment_code: LLM_MODELS = DEFAULT_NODE_LLMS["generate_experiment_code"]
    validate_experiment_code: LLM_MODELS = DEFAULT_NODE_LLMS["validate_experiment_code"]


class GenerateCodeSubgraphInputState(TypedDict):
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign


class GenerateCodeSubgraphOutputState(ExecutionTimeState):
    experiment_code: ExperimentCode


class GenerateCodeSubgraphState(
    GenerateCodeSubgraphInputState,
    GenerateCodeSubgraphOutputState,
):
    code_validation: tuple[bool, str]
    code_validation_count: int


class GenerateCodeSubgraph:
    def __init__(
        self,
        wandb_config: WandbConfig,
        langchain_client: LangChainClient,
        llm_mapping: GenerateCodeLLMMapping | None = None,
        max_code_validations: int = 3,
    ):
        self.wandb_config = wandb_config
        self.langchain_client = langchain_client
        self.llm_mapping = llm_mapping or GenerateCodeLLMMapping()
        self.max_code_validations = max_code_validations

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
            llm_client=self.langchain_client,
            research_hypothesis=state["research_hypothesis"],
            experimental_design=state["experimental_design"],
        )
        return {"experiment_code": ExperimentCode(run_configs=run_configs)}

    @record_execution_time
    async def _generate_experiment_code(
        self, state: GenerateCodeSubgraphState
    ) -> dict[str, ExperimentCode]:
        current_run_configs = state.get("experiment_code").run_configs

        generated_code = await generate_experiment_code(
            llm_name=self.llm_mapping.generate_experiment_code,
            llm_client=self.langchain_client,
            research_hypothesis=state["research_hypothesis"],
            experimental_design=state["experimental_design"],
            experiment_code=state.get("experiment_code"),
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
            llm_client=self.langchain_client,
            research_hypothesis=state["research_hypothesis"],
            experimental_design=state["experimental_design"],
            experiment_code=state.get("experiment_code"),
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
