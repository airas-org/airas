import json
import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
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
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_code_timed = lambda f: time_node("create_code_local_subgraph")(f)  # noqa: E731


class CreateCodeLLMMapping(BaseModel):
    generate_code_for_scripts: LLM_MODEL = DEFAULT_NODE_LLMS[
        "generate_code_for_scripts"
    ]


class CreateCodeSubgraphInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo
    new_method: ResearchHypothesis


class CreateCodeSubgraphHiddenState(TypedDict):
    pass


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
        self, llm_mapping: dict[str, str] | CreateCodeLLMMapping | None = None
    ):
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
    def _initialize(self, state: CreateCodeSubgraphState) -> dict:
        if "experiment_iteration" in state:
            return {"experiment_iteration": state["experiment_iteration"]}
        return {"experiment_iteration": 1}

    @create_code_timed
    def _generate_code_for_scripts(self, state: CreateCodeSubgraphState) -> dict:
        generated_file_contents = generate_code_for_scripts(
            llm_name=self.llm_mapping.generate_code_for_scripts,
            new_method=state["new_method"].method,
            experiment_code=cast(
                str, state["new_method"].experimental_design.experiment_code
            ),
            experiment_iteration=state["experiment_iteration"],
        )

        return {"generated_file_contents": generated_file_contents}

    @create_code_timed
    def _push_files_to_github_node(self, state: CreateCodeSubgraphState) -> dict:
        commit_message = f"Add generated experiment files for iteration {state['experiment_iteration']}"

        is_code_pushed_to_github = push_files_to_github(
            github_repository=state["github_repository_info"],
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
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node(
            "generate_code_for_scripts", self._generate_code_for_scripts
        )
        graph_builder.add_node(
            "push_files_to_github_node", self._push_files_to_github_node
        )
        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "generate_code_for_scripts")
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
