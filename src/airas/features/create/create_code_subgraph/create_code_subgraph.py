import json
import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.create.create_code_subgraph.input_data import (
    create_code_subgraph_input_data,
)
from airas.features.create.create_code_subgraph.nodes.generate_code_for_scripts import (
    generate_code_for_scripts,
)
from airas.features.create.create_code_subgraph.nodes.push_files_to_github import (
    push_files_to_github,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_code_timed = lambda f: time_node("create_code_local_subgraph")(f)  # noqa: E731


class CreateCodeSubgraphInputState(TypedDict):
    github_repository: dict[str, str]
    new_method: str
    experiment_code: str
    experiment_iteration: int


class CreateCodeSubgraphHiddenState(TypedDict):
    pass


class CreateCodeSubgraphOutputState(TypedDict):
    generated_file_contents: dict[str, str]
    is_code_pushed_to_github: bool
    created_files: list[str]


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

    def __init__(self, llm_name: str = "o3-mini-2025-01-31"):
        self.llm_name = llm_name
        check_api_key(
            llm_api_key_check=True,
            github_personal_access_token_check=True,
        )

    @create_code_timed
    def _generate_code_for_scripts(self, state: CreateCodeSubgraphState) -> dict:
        generated_file_contents = generate_code_for_scripts(
            llm_name=cast(LLM_MODEL, self.llm_name),
            new_method=state["new_method"],
            experiment_code=state["experiment_code"],
            experiment_iteration=state["experiment_iteration"],
        )

        return {"generated_file_contents": generated_file_contents}

    @create_code_timed
    def _push_files_to_github_node(self, state: CreateCodeSubgraphState) -> dict:
        commit_message = f"Add generated experiment files for iteration {state['experiment_iteration']}"

        is_code_pushed_to_github = push_files_to_github(
            github_repository=state["github_repository"],
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

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateCodeSubgraphState)

        graph_builder.add_node(
            "generate_code_for_scripts", self._generate_code_for_scripts
        )
        graph_builder.add_node(
            "push_files_to_github_node", self._push_files_to_github_node
        )

        graph_builder.add_edge(START, "generate_code_for_scripts")
        graph_builder.add_edge("generate_code_for_scripts", "push_files_to_github_node")
        graph_builder.add_edge("push_files_to_github_node", END)

        return graph_builder.compile()


def main():
    result = CreateCodeSubgraph().run(create_code_subgraph_input_data)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateCodeLocalSubgraph: {e}")
        raise
