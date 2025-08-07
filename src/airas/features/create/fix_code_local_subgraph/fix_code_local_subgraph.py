import json
import logging
from typing import Dict, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import NotRequired, TypedDict

from airas.core.base import BaseSubgraph
from airas.features.create.create_code_local_subgraph.nodes.push_files_to_github import (
    push_files_to_github,
)
from airas.features.create.fix_code_local_subgraph.input_data import (
    FixCodeLocalSubgraphInputState,
)
from airas.features.create.fix_code_local_subgraph.nodes.analyze_and_fix_code import (
    analyze_and_fix_code,
    should_fix_code,
)
from airas.features.create.fix_code_local_subgraph.nodes.get_current_files import (
    get_current_files,
    get_python_files_from_error,
)
from airas.features.create.fix_code_local_subgraph.nodes.get_failed_run_info import (
    get_failed_run_info,
)
from airas.features.create.fix_code_local_subgraph.prompt.code_fix_prompt import (
    code_fix_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

fix_code_local_timed = lambda f: time_node("fix_code_local_subgraph")(f)  # noqa: E731


class FixCodeLocalSubgraphOutputState(TypedDict):
    push_completion: bool
    fixed_files: list[str]
    executed_flag: bool


class FixCodeLocalSubgraphState(TypedDict, total=False):
    # Input fields
    github_repository: str
    branch_name: str
    output_text_data: str
    error_text_data: str
    executed_flag: bool

    # Hidden fields
    needs_fixing: NotRequired[bool]
    failed_run_info: NotRequired[Dict | None]
    current_files: NotRequired[Dict[str, str]]
    fixed_files: NotRequired[Dict[str, str]]

    # Output fields
    push_completion: NotRequired[bool]

    # Execution time fields
    execution_times: NotRequired[Dict[str, float]]


class FixCodeLocalSubgraph(BaseSubgraph):
    InputState = FixCodeLocalSubgraphInputState
    OutputState = FixCodeLocalSubgraphOutputState

    def __init__(self, llm_name: str = "o3-mini-2025-01-31"):
        self.llm_name = llm_name
        check_api_key(
            llm_api_key_check=True,
            github_personal_access_token_check=True,
        )

    @fix_code_local_timed
    def _analyze_errors_node(self, state: FixCodeLocalSubgraphState) -> Dict[str, bool]:
        """Analyze if code needs fixing based on error data"""
        logger.info("---Analyze Errors Node---")

        if not state.get("executed_flag", True):
            raise ValueError(
                "Invalid state: GitHub Actions workflow was not executed (expected executed_flag == True)"
            )

        needs_fixing = should_fix_code(
            output_text_data=state["output_text_data"],
            error_text_data=state["error_text_data"],
        )

        logger.info(f"Code needs fixing: {needs_fixing}")
        return {"needs_fixing": needs_fixing}

    @fix_code_local_timed
    def _get_failed_run_info_node(
        self, state: FixCodeLocalSubgraphState
    ) -> Dict[str, Dict | None]:
        """Get information about failed workflow runs"""
        logger.info("---Get Failed Run Info Node---")

        failed_run_info = get_failed_run_info(
            github_repository=state["github_repository"],
            branch_name=state["branch_name"],
        )

        return {"failed_run_info": failed_run_info}

    @fix_code_local_timed
    def _get_current_files_node(
        self, state: FixCodeLocalSubgraphState
    ) -> Dict[str, Dict[str, str]]:
        """Get current files from GitHub repository"""
        logger.info("---Get Current Files Node---")

        # Extract file paths from error messages
        file_paths = get_python_files_from_error(state["error_text_data"])

        current_files = get_current_files(
            github_repository=state["github_repository"],
            branch_name=state["branch_name"],
            file_paths=file_paths,
        )

        return {"current_files": current_files}

    @fix_code_local_timed
    def _analyze_and_fix_code_node(
        self, state: FixCodeLocalSubgraphState
    ) -> Dict[str, Dict[str, str]]:
        """Analyze errors and generate fixed code"""
        logger.info("---Analyze and Fix Code Node---")

        if not state.get("current_files"):
            logger.error("No current files found in state")
            return {"fixed_files": {}}

        fixed_files = analyze_and_fix_code(
            llm_name=cast(LLM_MODEL, self.llm_name),
            output_text_data=state["output_text_data"],
            error_text_data=state["error_text_data"],
            current_files=state["current_files"],
            prompt_template=code_fix_prompt,
        )

        return {"fixed_files": fixed_files}

    @fix_code_local_timed
    def _push_fixed_files_node(
        self, state: FixCodeLocalSubgraphState
    ) -> Dict[str, bool | list[str]]:
        """Push fixed files to GitHub repository"""
        logger.info("---Push Fixed Files Node---")

        if not state.get("fixed_files"):
            logger.error("No fixed files found in state")
            return {"push_completion": False, "fixed_files": [], "executed_flag": False}

        commit_message = "Fix code issues based on error analysis"

        success = push_files_to_github(
            github_repository=state["github_repository"],
            branch_name=state["branch_name"],
            files=state["fixed_files"],
            commit_message=commit_message,
        )

        fixed_file_paths = list(state["fixed_files"].keys()) if success else []

        return {
            "push_completion": success,
            "fixed_files": fixed_file_paths,
            "executed_flag": False,  # Set to False after fixing, will need re-execution
        }

    def _route_fix_or_end(self, state: FixCodeLocalSubgraphState) -> str:
        """Route to fix code or end based on analysis"""
        if state.get("needs_fixing") is True:
            return "get_failed_run_info_node"
        return "finish"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(FixCodeLocalSubgraphState)

        graph_builder.add_node("analyze_errors_node", self._analyze_errors_node)
        graph_builder.add_node(
            "get_failed_run_info_node", self._get_failed_run_info_node
        )
        graph_builder.add_node("get_current_files_node", self._get_current_files_node)
        graph_builder.add_node(
            "analyze_and_fix_code_node", self._analyze_and_fix_code_node
        )
        graph_builder.add_node("push_fixed_files_node", self._push_fixed_files_node)

        graph_builder.add_edge(START, "analyze_errors_node")
        graph_builder.add_conditional_edges(
            "analyze_errors_node",
            self._route_fix_or_end,
            {
                "get_failed_run_info_node": "get_failed_run_info_node",
                "finish": END,
            },
        )
        graph_builder.add_edge("get_failed_run_info_node", "get_current_files_node")
        graph_builder.add_edge("get_current_files_node", "analyze_and_fix_code_node")
        graph_builder.add_edge("analyze_and_fix_code_node", "push_fixed_files_node")
        graph_builder.add_edge("push_fixed_files_node", END)

        return graph_builder.compile()


def main():
    # Use actual executor results from the previous run
    input_data = FixCodeLocalSubgraphInputState(
        github_repository="auto-res2/airas-test-horiguchi",
        branch_name="main",
        output_text_data="",
        error_text_data="",
        executed_flag=True,
    )

    result = FixCodeLocalSubgraph().run(input_data)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running FixCodeLocalSubgraph: {e}")
        raise
