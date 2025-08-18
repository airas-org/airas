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
from airas.features.create.fix_code_with_devin_subgraph.nodes.should_fix_code import (
    should_fix_code,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

fix_code_timed = lambda f: time_node("fix_code_local_subgraph")(f)  # noqa: E731


class FixCodeLLMMapping(BaseModel):
    should_fix_code: LLM_MODEL = DEFAULT_NODE_LLMS["should_fix_code"]
    fix_code: LLM_MODEL = DEFAULT_NODE_LLMS["fix_code"]


class FixCodeSubgraphInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo
    generated_file_contents: dict[str, str]
    new_method: ResearchHypothesis
    executed_flag: bool  # This should be True if the GitHub Actions workflow was executed successfully
    experiment_iteration: int


class FixCodeSubgraphHiddenState(TypedDict):
    is_code_fix_needed: bool


class FixCodeSubgraphOutputState(TypedDict):
    is_code_pushed_to_github: bool
    executed_flag: bool
    generated_file_contents: dict[str, str]


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

    def __init__(self, llm_mapping: FixCodeLLMMapping | None = None):
        self.llm_mapping = llm_mapping or FixCodeLLMMapping()
        check_api_key(
            llm_api_key_check=True,
            github_personal_access_token_check=True,
        )

    @fix_code_timed
    def _initialize(self, state: FixCodeSubgraphState) -> dict:
        # NOTE: We increment the experiment_iteration here to reflect the next iteration
        return {"experiment_iteration": state["experiment_iteration"] + 1}

    @fix_code_timed
    def _should_fix_code(self, state: FixCodeSubgraphState) -> dict:
        if not state.get("executed_flag", True):
            raise ValueError(
                "Invalid state: GitHub Actions workflow was not executed (expected executed_flag == True)"
            )

        is_code_fix_needed = should_fix_code(
            llm_name=self.llm_mapping.should_fix_code,
            output_text_data=state["new_method"].experimental_results.result,
            error_text_data=state["new_method"].experimental_results.error,
        )
        return {
            "is_code_fix_needed": is_code_fix_needed,
        }

    @fix_code_timed
    def _fix_code(self, state: FixCodeSubgraphState) -> dict:
        """Analyze errors and generate fixed code"""
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
        """Push fixed files to GitHub repository"""
        commit_message = "Fix code issues based on error analysis"

        is_code_pushed_to_github = push_files_to_github(
            github_repository=state["github_repository_info"],
            files=state["generated_file_contents"],
            commit_message=commit_message,
        )

        return {
            "is_code_pushed_to_github": is_code_pushed_to_github,
            "executed_flag": False,  # Set to False after fixing, will need re-execution
        }

    def _route_fix_or_end(self, state: FixCodeSubgraphState) -> str:
        """Route to fix code or end based on analysis"""
        if state.get("is_code_fix_needed") is True:
            return "fix_code"
        return "finish"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(FixCodeSubgraphState)
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node("should_fix_code", self._should_fix_code)
        graph_builder.add_node("fix_code", self._fix_code)
        graph_builder.add_node("push_fixed_files_node", self._push_fixed_files_node)

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "should_fix_code")
        graph_builder.add_conditional_edges(
            "should_fix_code",
            self._route_fix_or_end,
            {
                "fix_code": "fix_code",
                "finish": END,
            },
        )
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
