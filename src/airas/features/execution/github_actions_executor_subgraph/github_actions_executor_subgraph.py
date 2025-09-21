import argparse
import json
import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.config.runner_type_info import RunnerType
from airas.core.base import BaseSubgraph

# from airas.execution.executor_subgraph.input_data import executor_subgraph_input_data
from airas.features.execution.github_actions_executor_subgraph.nodes.execute_github_actions_workflow import (
    execute_github_actions_workflow,
)
from airas.features.execution.github_actions_executor_subgraph.nodes.extract_required_info import (
    extract_required_info,
)
from airas.features.execution.github_actions_executor_subgraph.nodes.retrieve_github_actions_results import (
    retrieve_github_actions_results,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ExperimentalResults, ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

executor_timed = lambda f: time_node("executor_subgraph")(f)  # noqa: E731


class GitHubActionsExecutorLLMMapping(BaseModel):
    extract_required_info: LLM_MODEL = DEFAULT_NODE_LLMS["extract_required_info"]


class GitHubActionsExecutorSubgraphInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo
    new_method: ResearchHypothesis
    experiment_iteration: int
    is_code_pushed_to_github: bool


class GitHubActionsExecutorSubgraphHiddenState(TypedDict):
    output_text_data: str
    error_text_data: str
    image_file_name_list: list[str]


class GitHubActionsExecutorSubgraphOutputState(TypedDict):
    executed_flag: bool
    new_method: ResearchHypothesis


class ExecutorSubgraphState(
    GitHubActionsExecutorSubgraphInputState,
    GitHubActionsExecutorSubgraphHiddenState,
    GitHubActionsExecutorSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class GitHubActionsExecutorSubgraph(BaseSubgraph):
    InputState = GitHubActionsExecutorSubgraphInputState
    OutputState = GitHubActionsExecutorSubgraphOutputState

    def __init__(
        self,
        runner_type: RunnerType = "ubuntu-latest",
        llm_mapping: dict[str, str] | GitHubActionsExecutorLLMMapping | None = None,
    ):
        if llm_mapping is None:
            self.llm_mapping = GitHubActionsExecutorLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = GitHubActionsExecutorLLMMapping.model_validate(
                    llm_mapping
                )
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, GitHubActionsExecutorLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or GitHubActionsExecutorLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        check_api_key(
            github_personal_access_token_check=True,
        )
        self.runner_type = runner_type

    @executor_timed
    def _execute_github_actions_workflow_node(
        self, state: ExecutorSubgraphState
    ) -> dict:
        if not state.get("is_code_pushed_to_github", True):
            raise ValueError(
                "ExecutorSubgraph was called without a successful code push (expected is_code_pushed_to_github == True)"
            )

        executed_flag = execute_github_actions_workflow(
            github_repository=state["github_repository_info"],
            experiment_iteration=state["experiment_iteration"],
            runner_type=cast(RunnerType, self.runner_type),
        )
        return {"executed_flag": executed_flag}

    @executor_timed
    def _retrieve_github_actions_results(self, state: ExecutorSubgraphState) -> dict:
        output_text_data, error_text_data, image_file_name_list = (
            retrieve_github_actions_results(
                github_repository=state["github_repository_info"],
                experiment_iteration=state["experiment_iteration"],
            )
        )
        return {
            "output_text_data": output_text_data,
            "error_text_data": error_text_data,
            "image_file_name_list": image_file_name_list,
        }

    @executor_timed
    def _extract_required_info(self, state: ExecutorSubgraphState) -> dict:
        new_method = state["new_method"]
        extract_output, extract_error = extract_required_info(
            llm_name=self.llm_mapping.extract_required_info,
            output_text_data=state["output_text_data"],
            error_text_data=state["error_text_data"],
            github_repository_info=state["github_repository_info"],
        )
        new_method.experimental_results = ExperimentalResults(
            result=extract_output,
            error=extract_error,
            image_file_name_list=state["image_file_name_list"],
        )
        return {
            "new_method": new_method,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(ExecutorSubgraphState)
        graph_builder.add_node(
            "execute_github_actions_workflow_node",
            self._execute_github_actions_workflow_node,
        )
        graph_builder.add_node(
            "retrieve_github_actions_artifacts_node",
            self._retrieve_github_actions_results,
        )
        graph_builder.add_node(
            "extract_required_info_node", self._extract_required_info
        )

        graph_builder.add_edge(START, "execute_github_actions_workflow_node")
        graph_builder.add_edge(
            "execute_github_actions_workflow_node",
            "retrieve_github_actions_artifacts_node",
        )
        graph_builder.add_edge(
            "retrieve_github_actions_artifacts_node", "extract_required_info_node"
        )
        graph_builder.add_edge("extract_required_info_node", END)
        return graph_builder.compile()


def main():
    parser = argparse.ArgumentParser(description="ExecutorSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    state = {
        "github_repository": args.github_repository,
        "branch_name": args.branch_name,
        "experiment_iteration": 1,
        "push_completion": True,  # Set to True to indicate a successful code push
    }
    result = GitHubActionsExecutorSubgraph(runner_type="ubuntu-latest").run(state)
    print(f"result: {json.dumps(result, indent=2, ensure_ascii=False)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running ExecutorSubgraph: {e}")
        raise
