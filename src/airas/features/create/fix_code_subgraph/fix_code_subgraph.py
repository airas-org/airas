import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
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


class FixCodeSubgraphInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo
    generated_file_contents: dict[str, str]
    new_method: ResearchHypothesis
    executed_flag: bool  # This should be True if the GitHub Actions workflow was executed successfully
    experiment_iteration: int


class FixCodeSubgraphHiddenState(TypedDict): ...


class FixCodeSubgraphOutputState(TypedDict):
    is_code_pushed_to_github: bool
    executed_flag: bool
    generated_file_contents: dict[str, str]
    experiment_iteration: int


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

    def __init__(self, llm_mapping: dict[str, str] | FixCodeLLMMapping | None = None):
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
    def _initialize(self, state: FixCodeSubgraphState) -> dict:
        # NOTE: We increment the experiment_iteration here to reflect the next iteration
        return {"experiment_iteration": state["experiment_iteration"] + 1}

    @fix_code_timed
    def _fix_code(self, state: FixCodeSubgraphState) -> dict:
        fixed_file_contents = fix_code(
            llm_name=self.llm_mapping.fix_code,
            output_text_data=state["new_method"].experimental_results.result,
            error_text_data=state["new_method"].experimental_results.error,
            current_files=state["generated_file_contents"],
            experiment_iteration=state["experiment_iteration"],
        )

        return {"generated_file_contents": fixed_file_contents}

    @fix_code_timed
    def _push_fixed_files_node(self, state: FixCodeSubgraphState) -> dict:
        commit_message = (
            f"Fix code issues for iteration {state['experiment_iteration']}"
        )

        is_code_pushed_to_github = push_files_to_github(
            github_repository=state["github_repository_info"],
            files=state["generated_file_contents"],
            commit_message=commit_message,
        )

        return {
            "is_code_pushed_to_github": is_code_pushed_to_github,
            "executed_flag": False,  # Set to False after fixing, will need re-execution
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(FixCodeSubgraphState)
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node("fix_code", self._fix_code)
        graph_builder.add_node("push_fixed_files_node", self._push_fixed_files_node)

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "fix_code")
        graph_builder.add_edge("fix_code", "push_fixed_files_node")
        graph_builder.add_edge("push_fixed_files_node", END)

        return graph_builder.compile()


def main():
    result = FixCodeSubgraph().run(fix_code_subgraph_input_data)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running FixCodeLocalSubgraph: {e}")
        raise
