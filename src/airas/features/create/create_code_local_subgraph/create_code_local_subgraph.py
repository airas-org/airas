import json
import logging
from typing import Dict

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import NotRequired, TypedDict

from airas.core.base import BaseSubgraph
from airas.features.create.create_code_local_subgraph.input_data import (
    CreateCodeLocalSubgraphInputState,
)
from airas.features.create.create_code_local_subgraph.nodes.generate_code_files import (
    generate_code_files,
)
from airas.features.create.create_code_local_subgraph.nodes.push_files_to_github import (
    push_files_to_github,
)
from airas.features.create.create_code_local_subgraph.prompt.code_generation_prompt import (
    code_generation_prompt,
)
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_code_local_timed = lambda f: time_node("create_code_local_subgraph")(f)  # noqa: E731


class CreateCodeLocalSubgraphOutputState(TypedDict):
    push_completion: bool
    created_files: list[str]


class CreateCodeLocalSubgraphState(TypedDict, total=False):
    # Input fields
    github_repository: str
    branch_name: str
    new_method: str
    experiment_code: str
    experiment_iteration: int

    # Hidden fields
    generated_files: NotRequired[Dict[str, str]]

    # Output fields
    push_completion: NotRequired[bool]
    created_files: NotRequired[list[str]]

    # Execution time fields
    execution_times: NotRequired[Dict[str, float]]


class CreateCodeLocalSubgraph(BaseSubgraph):
    InputState = CreateCodeLocalSubgraphInputState
    OutputState = CreateCodeLocalSubgraphOutputState

    def __init__(self, llm_name: str = "o3-mini-2025-01-31"):
        self.llm_name = llm_name
        check_api_key(
            llm_api_key_check=True,
            github_personal_access_token_check=True,
        )

    @create_code_local_timed
    def _generate_code_files_node(
        self, state: CreateCodeLocalSubgraphState
    ) -> Dict[str, Dict[str, str]]:
        """Generate code files using LLM"""
        logger.info("---Generate Code Files Node---")

        generated_files = generate_code_files(
            llm_name=self.llm_name,
            new_method=state["new_method"],
            experiment_code=state["experiment_code"],
            experiment_iteration=state["experiment_iteration"],
            prompt_template=code_generation_prompt,
        )

        return {"generated_files": generated_files}

    @create_code_local_timed
    def _push_files_to_github_node(
        self, state: CreateCodeLocalSubgraphState
    ) -> Dict[str, bool | list[str]]:
        """Push generated files to GitHub repository"""
        logger.info("---Push Files to GitHub Node---")

        if not state.get("generated_files"):
            logger.error("No generated files found in state")
            return {"push_completion": False, "created_files": []}

        commit_message = f"Add generated experiment files for iteration {state['experiment_iteration']}"

        success = push_files_to_github(
            github_repository=state["github_repository"],
            branch_name=state["branch_name"],
            files=state["generated_files"],
            commit_message=commit_message,
        )

        created_files = list(state["generated_files"].keys()) if success else []

        return {
            "push_completion": success,
            "created_files": created_files,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateCodeLocalSubgraphState)

        graph_builder.add_node(
            "generate_code_files_node", self._generate_code_files_node
        )
        graph_builder.add_node(
            "push_files_to_github_node", self._push_files_to_github_node
        )

        graph_builder.add_edge(START, "generate_code_files_node")
        graph_builder.add_edge("generate_code_files_node", "push_files_to_github_node")
        graph_builder.add_edge("push_files_to_github_node", END)

        return graph_builder.compile()


def main():
    input_data = CreateCodeLocalSubgraphInputState(
        github_repository="auto-res2/test-tanaka-v11",
        branch_name="develop",
        new_method="A novel approach to image classification using attention mechanisms",
        experiment_code="Implement a CNN with attention layers for CIFAR-10 classification",
        experiment_iteration=1,
    )

    result = CreateCodeLocalSubgraph().run(input_data)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateCodeLocalSubgraph: {e}")
        raise
