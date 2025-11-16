import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.config.runner_type_info import RunnerType
from airas.core.base import BaseSubgraph
from airas.features.create.create_code_subgraph.nodes.generate_experiment_code import (
    generate_experiment_code,
)
from airas.features.create.create_code_subgraph.nodes.generate_run_config import (
    generate_run_config,
)
from airas.features.create.create_code_subgraph.nodes.validate_experiment_code import (
    validate_experiment_code,
)
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.llm_client.openai_client import OPENAI_MODEL
from airas.types.research_session import ResearchSession
from airas.types.wandb import WandbInfo
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("create_code_subgraph")(f)  # noqa: E731


class CreateCodeLLMMapping(BaseModel):
    generate_run_config: OPENAI_MODEL = DEFAULT_NODE_LLMS["generate_run_config"]
    generate_experiment_code: OPENAI_MODEL = DEFAULT_NODE_LLMS[
        "generate_experiment_code"
    ]
    validate_experiment_code: OPENAI_MODEL = DEFAULT_NODE_LLMS[
        "validate_experiment_code"
    ]


class CreateCodeSubgraphInputState(TypedDict, total=False):
    research_session: ResearchSession


class CreateCodeSubgraphHiddenState(TypedDict):
    code_validation: tuple[bool, str]
    code_validation_count: int


class CreateCodeSubgraphOutputState(TypedDict):
    research_session: ResearchSession


class CreateCodeSubgraphState(
    CreateCodeSubgraphInputState,
    CreateCodeSubgraphHiddenState,
    CreateCodeSubgraphOutputState,
    total=False,
):
    pass


class CreateCodeSubgraph(BaseSubgraph):
    InputState = CreateCodeSubgraphInputState
    OutputState = CreateCodeSubgraphOutputState

    def __init__(
        self,
        llm_client: LLMFacadeClient,
        runner_type: RunnerType = "ubuntu-latest",
        llm_mapping: dict[str, str] | CreateCodeLLMMapping | None = None,
        secret_names: list[str] | None = None,
        wandb_info: WandbInfo | None = None,
        max_code_validations: int = 3,
    ):
        self.runner_type = runner_type
        self.secret_names = secret_names or []
        self.wandb_info = wandb_info
        self.max_code_validations = max_code_validations
        if llm_mapping is None:
            self.llm_mapping = CreateCodeLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = CreateCodeLLMMapping.model_validate(llm_mapping)
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, CreateCodeLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or CreateCodeLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.llm_client = llm_client
        check_api_key(
            llm_api_key_check=True,
            github_personal_access_token_check=True,
        )

    @record_execution_time
    def _initialize(
        self, state: CreateCodeSubgraphState
    ) -> dict[str, int | tuple[bool, str]]:
        return {
            "code_validation": (False, ""),
            "code_validation_count": 0,
        }

    @record_execution_time
    async def _generate_run_config(
        self, state: CreateCodeSubgraphState
    ) -> dict[str, ResearchSession]:
        research_session = state["research_session"]
        run_configs = await generate_run_config(
            llm_name=self.llm_mapping.generate_run_config,
            llm_client=self.llm_client,
            research_session=research_session,
            runner_type=cast(RunnerType, self.runner_type),
        )

        config_dict = {cfg.run_id: cfg.run_config_yaml for cfg in run_configs}
        for exp_run in research_session.current_iteration.experiment_runs or []:
            exp_run.run_config = config_dict.get(exp_run.run_id)

        return {"research_session": research_session}

    @record_execution_time
    async def _generate_experiment_code(
        self, state: CreateCodeSubgraphState
    ) -> dict[str, ResearchSession]:
        research_session = state["research_session"]
        experiment_code = await generate_experiment_code(
            llm_name=self.llm_mapping.generate_experiment_code,
            llm_client=self.llm_client,
            research_session=research_session,
            runner_type=cast(RunnerType, self.runner_type),
            wandb_info=self.wandb_info,
            code_validation=state.get("code_validation"),
        )
        research_session.current_iteration.experimental_design.experiment_code = (
            experiment_code
        )

        return {"research_session": research_session}

    @record_execution_time
    async def _validate_experiment_code(
        self, state: CreateCodeSubgraphState
    ) -> dict[str, tuple[bool, str] | int]:
        code_validation = await validate_experiment_code(
            llm_name=self.llm_mapping.validate_experiment_code,
            llm_client=self.llm_client,
            research_session=state["research_session"],
            wandb_info=self.wandb_info,
        )
        return {
            "code_validation": code_validation,
            "code_validation_count": state["code_validation_count"] + 1,
        }

    def _should_continue_after_experiment_code_validation(
        self, state: CreateCodeSubgraphState
    ) -> str:
        is_code_ready, issue = state["code_validation"]
        code_validation_count = state["code_validation_count"]

        if is_code_ready:
            logger.info("Code validation passed. Proceeding to push files to GitHub...")
            return "end"

        if code_validation_count >= self.max_code_validations:
            logger.warning(
                f"Maximum code validation attempts ({self.max_code_validations}) reached. Proceeding to push files..."
            )
            return "end"

        logger.warning(
            f"Code validation failed: {issue}. Re-running generate_experiment_code... (attempt {code_validation_count}/{self.max_code_validations})"
        )
        return "generate_experiment_code"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateCodeSubgraphState)
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


def main():
    from airas.features.create.create_code_subgraph.input_data import (
        create_code_subgraph_input_data,
    )
    from airas.services.api_client.api_clients_container import sync_container
    from airas.types.wandb import WandbInfo

    sync_container.wire(modules=[__name__])

    secret_names = ["HF_TOKEN", "WANDB_API_KEY", "ANTHROPIC_API_KEY"]
    wandb_info = WandbInfo(entity="gengaru617-personal", project="251017-test")
    max_code_validations = 10
    result = CreateCodeSubgraph(
        secret_names=secret_names,
        wandb_info=wandb_info,
        max_code_validations=max_code_validations,
    ).run(create_code_subgraph_input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateCodeSubgraph: {e}")
        raise
