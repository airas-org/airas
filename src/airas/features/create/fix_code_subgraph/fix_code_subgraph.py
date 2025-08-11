import json
import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import NotRequired, TypedDict

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
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

fix_code_timed = lambda f: time_node("fix_code_local_subgraph")(f)  # noqa: E731


class FixCodeSubgraphInputState(TypedDict):
    github_repository: dict[str, str]
    generated_file_contents: dict[str, str]
    output_text_data: str
    error_text_data: str
    executed_flag: bool  # This should be True if the GitHub Actions workflow was executed successfully
    experiment_iteration: int


class FixCodeSubgraphHiddenState(TypedDict):
    is_code_fix_needed: bool


class FixCodeSubgraphOutputState(TypedDict):
    is_code_pushed_to_github: bool
    fixed_files: dict[str, str]
    executed_flag: bool


class FixCodeSubgraphState(
    FixCodeSubgraphInputState,
    FixCodeSubgraphHiddenState,
    FixCodeSubgraphOutputState,
    total=False,
):
    needs_fixing: NotRequired[bool]
    failed_run_info: NotRequired[dict | None]
    current_files: NotRequired[dict[str, str]]


class FixCodeSubgraph(BaseSubgraph):
    InputState = FixCodeSubgraphInputState
    OutputState = FixCodeSubgraphOutputState

    def __init__(self, llm_name: str = "o3-mini-2025-01-31"):
        self.llm_name = llm_name
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
            llm_name=cast(LLM_MODEL, self.llm_name),
            output_text_data=state["output_text_data"],
            error_text_data=state["error_text_data"],
        )
        return {
            "is_code_fix_needed": is_code_fix_needed,
        }

    @fix_code_timed
    def _fix_code(self, state: FixCodeSubgraphState) -> dict:
        """Analyze errors and generate fixed code"""
        logger.info("---Analyze and Fix Code Node---")

        fixed_files = fix_code(
            llm_name=cast(LLM_MODEL, self.llm_name),
            output_text_data=state["output_text_data"],
            error_text_data=state["error_text_data"],
            current_files=state["generated_file_contents"],
            experiment_iteration=state["experiment_iteration"],
        )

        return {"fixed_files": fixed_files}

    @fix_code_timed
    def _push_fixed_files_node(self, state: FixCodeSubgraphState) -> dict:
        """Push fixed files to GitHub repository"""
        logger.info("---Push Fixed Files Node---")

        commit_message = "Fix code issues based on error analysis"

        success = push_files_to_github(
            github_repository=state["github_repository"],
            files=state["fixed_files"],
            commit_message=commit_message,
        )

        fixed_file_paths = list(state["fixed_files"].keys()) if success else []

        return {
            "is_code_pushed_to_github": success,
            "fixed_files": fixed_file_paths,
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
