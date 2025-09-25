import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.config.runner_type_info import RunnerType
from airas.core.base import BaseSubgraph
from airas.features.create.create_code_subgraph.input_data import (
    create_code_subgraph_input_data,
)
from airas.features.create.create_code_subgraph.nodes.derive_specific_experiments import (
    derive_specific_experiments,
)
from airas.features.create.create_code_subgraph.nodes.generate_core_code import (
    generate_core_code,
)
from airas.features.create.create_code_subgraph.nodes.push_files_to_github import (
    push_files_to_github,
)
from airas.features.create.create_code_subgraph.nodes.set_github_actions_secrets import (
    set_github_actions_secrets,
)
from airas.features.create.create_code_subgraph.nodes.validate_core_code import (
    validate_core_code,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_code_timed = lambda f: time_node("create_code_subgraph")(f)  # noqa: E731


class CreateCodeLLMMapping(BaseModel):
    generate_core_code: LLM_MODEL = DEFAULT_NODE_LLMS["generate_core_code"]
    validate_core_code: LLM_MODEL = DEFAULT_NODE_LLMS["validate_core_code"]
    derive_specific_experiments: LLM_MODEL = DEFAULT_NODE_LLMS[
        "derive_specific_experiments"
    ]


class CreateCodeSubgraphInputState(TypedDict, total=False):
    github_repository_info: GitHubRepositoryInfo
    new_method: ResearchHypothesis
    experiment_iteration: int
    consistency_feedback: list[str]


class CreateCodeSubgraphHiddenState(TypedDict):
    core_code_validation: tuple[bool, str]
    core_code_validation_count: int


class CreateCodeSubgraphOutputState(TypedDict):
    new_method: ResearchHypothesis
    is_code_pushed_to_github: bool
    experiment_iteration: int


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
        runner_type: RunnerType = "ubuntu-latest",
        llm_mapping: dict[str, str] | CreateCodeLLMMapping | None = None,
        secret_names: list[str] | None = None,
        max_core_code_validations: int = 3,
    ):
        self.runner_type = runner_type
        self.secret_names = secret_names or []
        self.max_core_code_validations = max_core_code_validations
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
        check_api_key(
            llm_api_key_check=True,
            github_personal_access_token_check=True,
        )

    @create_code_timed
    def _initialize(
        self, state: CreateCodeSubgraphState
    ) -> dict[str, int | tuple[bool, str]]:
        # Always increment experiment_iteration to create a new iteration folder
        return {
            "experiment_iteration": state.get("experiment_iteration", 0) + 1,
            "core_code_validation": (False, ""),
            "core_code_validation_count": 0,
        }

    @create_code_timed
    def _generate_core_code(
        self, state: CreateCodeSubgraphState
    ) -> dict[str, ResearchHypothesis]:
        new_method = generate_core_code(
            llm_name=self.llm_mapping.generate_core_code,
            new_method=state["new_method"],
            runner_type=cast(RunnerType, self.runner_type),
            secret_names=self.secret_names,
            github_repository_info=state["github_repository_info"],
            feedback_text=feedback[-1]
            if (feedback := state.get("consistency_feedback"))
            else None,
            core_code_validation=state.get("core_code_validation"),
        )
        return {"new_method": new_method}

    @create_code_timed
    def _validate_core_code(
        self, state: CreateCodeSubgraphState
    ) -> dict[str, tuple[bool, str] | int]:
        core_code_validation = validate_core_code(
            llm_name=self.llm_mapping.validate_core_code,
            new_method=state["new_method"],
            github_repository_info=state["github_repository_info"],
        )
        return {
            "core_code_validation": core_code_validation,
            "core_code_validation_count": state["core_code_validation_count"] + 1,
        }

    def _should_continue_after_code_validation(
        self, state: CreateCodeSubgraphState
    ) -> str:
        is_core_code_ready, issue = state["core_code_validation"]
        core_code_validation_count = state["core_code_validation_count"]

        if is_core_code_ready:
            logger.info(
                "Core code validation passed. Proceeding to derive specific experiments..."
            )
            return "derive_specific_experiments"

        if core_code_validation_count >= self.max_core_code_validations:
            logger.warning(
                f"Maximum core code validation attempts ({self.max_core_code_validations}) reached. Proceeding to derive experiments..."
            )
            return "derive_specific_experiments"

        logger.warning(
            f"Core code validation failed: {issue}. Re-running generate_core_code... (attempt {core_code_validation_count}/{self.max_core_code_validations})"
        )
        return "generate_core_code"

    # TODO: Generate code for each experiment and store it separately in the state.
    @create_code_timed
    def _derive_specific_experiments(
        self, state: CreateCodeSubgraphState
    ) -> dict[str, ResearchHypothesis]:
        new_method = derive_specific_experiments(
            llm_name=self.llm_mapping.derive_specific_experiments,
            new_method=state["new_method"],
            runner_type=cast(RunnerType, self.runner_type),
            secret_names=self.secret_names,
            github_repository_info=state["github_repository_info"],
        )
        return {"new_method": new_method}

    @create_code_timed
    def _push_files_to_github(self, state: CreateCodeSubgraphState) -> dict[str, bool]:
        commit_message = f"Add generated experiment files for iteration {state['experiment_iteration']}"

        is_code_pushed_to_github = push_files_to_github(
            github_repository_info=state["github_repository_info"],
            new_method=state["new_method"],
            commit_message=commit_message,
        )

        return {
            "is_code_pushed_to_github": is_code_pushed_to_github,
        }

    @create_code_timed
    def _set_github_actions_secrets(self, state: CreateCodeSubgraphState) -> dict:
        if not self.secret_names:
            logger.info(
                "No secret names provided, skipping GitHub Actions secrets setup"
            )
            return {}

        set_github_actions_secrets(
            github_repository_info=state["github_repository_info"],
            secret_names=self.secret_names,
        )
        return {}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateCodeSubgraphState)
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node("generate_core_code", self._generate_core_code)
        graph_builder.add_node(
            "derive_specific_experiments", self._derive_specific_experiments
        )
        graph_builder.add_node("validate_core_code", self._validate_core_code)
        graph_builder.add_node("push_files_to_github", self._push_files_to_github)
        graph_builder.add_node(
            "set_github_actions_secrets", self._set_github_actions_secrets
        )

        # Core generation -> Validation -> Experiment specialization workflow
        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "generate_core_code")
        graph_builder.add_edge("generate_core_code", "validate_core_code")

        graph_builder.add_conditional_edges(
            "validate_core_code",
            self._should_continue_after_code_validation,
            {
                "generate_core_code": "generate_core_code",
                "derive_specific_experiments": "derive_specific_experiments",
            },
        )

        graph_builder.add_edge("derive_specific_experiments", "push_files_to_github")
        graph_builder.add_edge("push_files_to_github", "set_github_actions_secrets")
        graph_builder.add_edge("set_github_actions_secrets", END)

        return graph_builder.compile()


def main():
    result = CreateCodeSubgraph(secret_names=["HF_TOKEN"]).run(
        create_code_subgraph_input_data
    )
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateCodeSubgraph: {e}")
        raise
