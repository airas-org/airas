import logging

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
from airas.features.create.create_code_subgraph.nodes.convert_code_to_scripts import (
    convert_code_to_scripts,
)
from airas.features.create.create_code_subgraph.nodes.generate_experiment_code import (
    generate_experiment_code,
)
from airas.features.create.create_code_subgraph.nodes.push_files_to_github import (
    push_files_to_github,
)
from airas.features.create.create_code_subgraph.nodes.set_github_actions_secrets import (
    set_github_actions_secrets,
)
from airas.features.create.fix_code_subgraph.nodes.static_validate_code import (
    static_validate_code,
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
    generate_experiment_code: LLM_MODEL = DEFAULT_NODE_LLMS["generate_experiment_code"]
    convert_code_to_scripts: LLM_MODEL = DEFAULT_NODE_LLMS["convert_code_to_scripts"]


class CreateCodeSubgraphInputState(TypedDict, total=False):
    github_repository_info: GitHubRepositoryInfo
    new_method: ResearchHypothesis
    experiment_iteration: int
    consistency_feedback: list[str]
    generated_file_contents: dict[str, str]


class CreateCodeSubgraphHiddenState(TypedDict):
    file_validations: dict[str, dict[str, list[str]]]


class CreateCodeSubgraphOutputState(TypedDict):
    new_method: ResearchHypothesis
    is_code_pushed_to_github: bool
    created_files: list[str]
    experiment_iteration: int
    generated_file_contents: dict[str, str]


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
    ):
        self.runner_type = runner_type
        self.secret_names = secret_names or []
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
    ) -> dict[str, int | dict[str, str] | dict[str, dict[str, list[str]]]]:
        # Always increment experiment_iteration to create a new iteration folder
        current_iteration = state.get("experiment_iteration", 0)
        return {
            "experiment_iteration": current_iteration + 1,
            "generated_file_contents": state.get("generated_file_contents", {}),
            "file_validations": {},
        }

    @create_code_timed
    def _generate_experiment_code(
        self, state: CreateCodeSubgraphState
    ) -> dict[str, ResearchHypothesis]:
        new_method = generate_experiment_code(
            llm_name=self.llm_mapping.generate_experiment_code,
            new_method=state["new_method"],
            runner_type=self.runner_type,
            secret_names=self.secret_names,
            feedback_text=feedback[-1]
            if (feedback := state.get("consistency_feedback"))
            else None,
        )
        return {"new_method": new_method}

    @create_code_timed
    def _convert_code_to_scripts(
        self, state: CreateCodeSubgraphState
    ) -> dict[str, dict[str, str]]:
        generated_file_contents = convert_code_to_scripts(
            llm_name=self.llm_mapping.convert_code_to_scripts,
            new_method=state["new_method"],
            secret_names=self.secret_names,
            runner_type=self.runner_type,
            experiment_iteration=state["experiment_iteration"],
            file_validations=state["file_validations"],
            generated_file_contents=state["generated_file_contents"],
        )
        return {"generated_file_contents": generated_file_contents}

    @create_code_timed
    def _static_validate_code(
        self, state: CreateCodeSubgraphState
    ) -> dict[str, dict[str, dict[str, list[str]]]]:
        file_validations = static_validate_code(
            generated_file_contents=state["generated_file_contents"]
        )
        return {
            "file_validations": file_validations,
        }

    def _should_reconvert_code(self, state: CreateCodeSubgraphState) -> str:
        file_validations = state["file_validations"]
        if file_validations is None:
            return "push_files_to_github"

        has_errors = any(
            len(file_val.get("errors", [])) > 0
            for file_val in file_validations.values()
        )

        if has_errors:
            logger.warning(
                "Static validation found errors. Re-running convert_code_to_scripts..."
            )
            return "convert_code_to_scripts"
        else:
            logger.info("Static validation passed. Proceeding to push files...")
            return "push_files_to_github"

    @create_code_timed
    def _push_files_to_github(
        self, state: CreateCodeSubgraphState
    ) -> dict[str, bool | list[str]]:
        commit_message = f"Add generated experiment files for iteration {state['experiment_iteration']}"

        is_code_pushed_to_github = push_files_to_github(
            github_repository_info=state["github_repository_info"],
            files=state["generated_file_contents"],
            commit_message=commit_message,
        )
        created_files = (
            list(state["generated_file_contents"].keys())
            if is_code_pushed_to_github
            else []
        )
        return {
            "is_code_pushed_to_github": is_code_pushed_to_github,
            "created_files": created_files,
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
        graph_builder.add_node(
            "generate_experiment_code", self._generate_experiment_code
        )
        graph_builder.add_node("convert_code_to_scripts", self._convert_code_to_scripts)
        graph_builder.add_node("static_validate_code", self._static_validate_code)
        graph_builder.add_node("push_files_to_github", self._push_files_to_github)
        graph_builder.add_node(
            "set_github_actions_secrets", self._set_github_actions_secrets
        )

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "generate_experiment_code")
        graph_builder.add_edge("generate_experiment_code", "convert_code_to_scripts")
        graph_builder.add_edge("convert_code_to_scripts", "static_validate_code")
        graph_builder.add_conditional_edges(
            "static_validate_code",
            self._should_reconvert_code,
            {
                "convert_code_to_scripts": "convert_code_to_scripts",
                "push_files_to_github": "push_files_to_github",
            },
        )
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
