import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.config.runner_type_info import RunnerType
from airas.core.base import BaseSubgraph
from airas.features.create.create_code_subgraph.nodes.push_files_to_github import (
    push_files_to_github,
)
from airas.features.create.fix_code_subgraph.input_data import (
    fix_code_subgraph_input_data,
)
from airas.features.create.fix_code_subgraph.nodes.fix_code import (
    fix_code,
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

fix_code_timed = lambda f: time_node("fix_code_subgraph")(f)  # noqa: E731


class FixCodeLLMMapping(BaseModel):
    fix_code: LLM_MODEL = DEFAULT_NODE_LLMS["fix_code"]


class FixCodeSubgraphInputState(TypedDict, total=False):
    github_repository_info: GitHubRepositoryInfo
    new_method: ResearchHypothesis
    executed_flag: bool  # This should be True if the GitHub Actions workflow was executed successfully
    experiment_iteration: int
    error_list: list[str]


class FixCodeSubgraphHiddenState(TypedDict):
    file_static_validations: dict[str, dict[str, list[str]]]
    static_validation_count: int


class FixCodeSubgraphOutputState(TypedDict):
    executed_flag: bool
    experiment_iteration: int
    is_code_pushed_to_github: bool
    error_list: list[str]


class FixCodeSubgraphState(
    FixCodeSubgraphInputState,
    FixCodeSubgraphHiddenState,
    FixCodeSubgraphOutputState,
    total=False,
):
    pass


class FixCodeSubgraph(BaseSubgraph):
    InputState = FixCodeSubgraphInputState
    OutputState = FixCodeSubgraphOutputState

    def __init__(
        self,
        runner_type: RunnerType = "ubuntu-latest",
        llm_mapping: dict[str, str] | FixCodeLLMMapping | None = None,
        secret_names: list[str] | None = None,
        max_static_validations: int = 3,
    ):
        self.runner_type = runner_type
        self.secret_names = secret_names or []
        self.max_static_validations = max_static_validations
        if llm_mapping is None:
            self.llm_mapping = FixCodeLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = FixCodeLLMMapping.model_validate(llm_mapping)
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, FixCodeLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or FixCodeLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        check_api_key(llm_api_key_check=True)

    @fix_code_timed
    def _initialize(
        self, state: FixCodeSubgraphState
    ) -> dict[str, int | list[str] | dict[str, dict[str, list[str]]]]:
        # NOTE: We increment the experiment_iteration here to reflect the next iteration
        return {
            "experiment_iteration": state["experiment_iteration"] + 1,
            "error_list": state.get("error_list", []),
            "file_static_validations": {},
            "static_validation_count": 0,
        }

    @fix_code_timed
    def _fix_code(
        self, state: FixCodeSubgraphState
    ) -> dict[str, ResearchHypothesis | list[str]]:
        result = fix_code(
            llm_name=self.llm_mapping.fix_code,
            new_method=state["new_method"],
            experiment_iteration=state["experiment_iteration"],
            runner_type=self.runner_type,
            secret_names=self.secret_names,
            error_list=state["error_list"],
            file_static_validations=state["file_static_validations"],
        )
        return {
            "new_method": result["new_method"],
            "error_list": result["error_list"],
        }

    @fix_code_timed
    def _static_validate_code(
        self, state: FixCodeSubgraphState
    ) -> dict[str, dict[str, dict[str, list[str]]] | int]:
        file_static_validations = static_validate_code(
            new_method=state["new_method"],
        )
        return {
            "file_static_validations": file_static_validations,
            "static_validation_count": state["static_validation_count"] + 1,
        }

    def _should_refix_code(self, state: FixCodeSubgraphState) -> str:
        file_static_validations = state["file_static_validations"]
        static_validation_count = state["static_validation_count"]

        if file_static_validations is None:
            return "push_fixed_files_node"

        has_errors = any(
            len(file_val.get("errors", [])) > 0
            for file_val in file_static_validations.values()
        )

        if not has_errors:
            logger.info("Static validation passed. Skipping fix_code...")
            return "push_fixed_files_node"

        if static_validation_count >= self.max_static_validations:
            logger.warning(
                f"Maximum static validation attempts ({self.max_static_validations}) reached. Proceeding to push files..."
            )
            return "push_fixed_files_node"

        logger.info(
            f"Static validation found errors. Running fix_code... (attempt {static_validation_count}/{self.max_static_validations})"
        )
        return "fix_code"

    @fix_code_timed
    def _push_fixed_files_node(self, state: FixCodeSubgraphState) -> dict[str, bool]:
        commit_message = (
            f"Fix code issues for iteration {state['experiment_iteration']}"
        )

        is_code_pushed_to_github = push_files_to_github(
            github_repository_info=state["github_repository_info"],
            files=state[
                "new_method"
            ].experimental_design.experiment_code.to_file_dict(),
            commit_message=commit_message,
        )

        return {
            "is_code_pushed_to_github": is_code_pushed_to_github,
            "executed_flag": False,  # Set to False after fixing, will need re-execution
        }

    def build_graph(self):
        graph_builder = StateGraph(FixCodeSubgraphState)
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node("fix_code", self._fix_code)
        graph_builder.add_node("static_validate_code", self._static_validate_code)
        graph_builder.add_node("push_fixed_files_node", self._push_fixed_files_node)

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "fix_code")
        graph_builder.add_edge("fix_code", "static_validate_code")
        graph_builder.add_conditional_edges(
            "static_validate_code",
            self._should_refix_code,
            {
                "fix_code": "fix_code",
                "push_fixed_files_node": "push_fixed_files_node",
            },
        )
        graph_builder.add_edge("push_fixed_files_node", END)

        return graph_builder.compile()


def main():
    result = FixCodeSubgraph().run(fix_code_subgraph_input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running FixCodeSubgraph: {e}")
        raise
