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
from airas.features.evaluate.judge_execution_subgraph.nodes.judge_execution import (
    judge_execution,
)
from airas.features.execution.github_actions_executor_subgraph.nodes.create_experiment_branches import (
    create_experiment_branches,
)
from airas.features.execution.github_actions_executor_subgraph.nodes.execute_github_actions_workflow import (
    execute_github_actions_workflow,
)
from airas.features.execution.github_actions_executor_subgraph.nodes.retrieve_artifacts import (
    retrieve_full_experiment_artifacts,
    retrieve_smoke_test_artifacts,
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
    judge_execution: LLM_MODEL = DEFAULT_NODE_LLMS["judge_execution"]


class GitHubActionsExecutorSubgraphInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo
    new_method: ResearchHypothesis


class GitHubActionsExecutorSubgraphHiddenState(TypedDict):
    experiment_iteration: int
    smoke_test_results: ExperimentalResults
    smoke_test_passed: bool
    executed_flag: bool


class GitHubActionsExecutorSubgraphOutputState(TypedDict):
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
        self.runner_type = runner_type
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
            llm_api_key_check=True,
        )

    # TODO: `experiment_iteration` may become unnecessary
    @executor_timed
    def _initialize(
        self, state: ExecutorSubgraphState
    ) -> dict[str, int | tuple[bool, str] | dict[str, tuple[bool, str]]]:
        # Always increment experiment_iteration to create a new iteration folder
        return {
            "experiment_iteration": state.get("experiment_iteration", 0) + 1,
        }

    @executor_timed
    def _execute_smoke_test(
        self, state: ExecutorSubgraphState
    ) -> dict[str, bool | int]:
        executed_flag = execute_github_actions_workflow(
            github_repository=state["github_repository_info"],
            experiment_iteration=state["experiment_iteration"],
            runner_type=cast(RunnerType, self.runner_type),
        )
        return {
            "executed_flag": executed_flag,
            "experiment_iteration": state["experiment_iteration"] + 1,
        }

    @executor_timed
    def _retrieve_smoke_test_artifacts(
        self, state: ExecutorSubgraphState
    ) -> dict[str, ResearchHypothesis | ExperimentalResults]:
        new_method, smoke_test_results = retrieve_smoke_test_artifacts(
            github_repository=state["github_repository_info"],
            experiment_iteration=state["experiment_iteration"],
            new_method=state["new_method"],
        )
        return {
            "new_method": new_method,
            "smoke_test_results": smoke_test_results,
        }

    @executor_timed
    def _judge_execution(self, state: ExecutorSubgraphState) -> dict[str, bool]:
        if not (smoke_test_results := state["smoke_test_results"]):
            logger.error("No smoke_test_results found in state")
            return {"smoke_test_passed": False}

        is_successful = judge_execution(
            llm_name=self.llm_mapping.judge_execution,
            output_text_data=smoke_test_results.result or "",
            error_text_data=smoke_test_results.error or "",
            github_repository_info=state["github_repository_info"],
        )
        logger.info(f"Smoke test judgment: {'PASSED' if is_successful else 'FAILED'}")

        return {"smoke_test_passed": is_successful}

    @executor_timed
    def _create_experiment_branches(
        self, state: ExecutorSubgraphState
    ) -> dict[str, ResearchHypothesis]:
        new_method = create_experiment_branches(
            github_repository_info=state["github_repository_info"],
            new_method=state["new_method"],
        )
        return {"new_method": new_method}

    @executor_timed
    def _execute_full_experiments(
        self, state: ExecutorSubgraphState
    ) -> dict[str, bool | int]:
        # NOTE: Reset experiment_iteration for next cycle but iteration is not performed
        experiment_iteration = 1

        executed_flag = execute_github_actions_workflow(
            github_repository=state["github_repository_info"],
            experiment_iteration=experiment_iteration,
            runner_type=cast(RunnerType, self.runner_type),
        )
        return {
            "executed_flag": executed_flag,
            "experiment_iteration": experiment_iteration,
        }

    @executor_timed
    def _retrieve_full_experiment_artifacts(
        self, state: ExecutorSubgraphState
    ) -> dict[str, ResearchHypothesis]:
        new_method = retrieve_full_experiment_artifacts(
            experiment_iteration=state["experiment_iteration"],
            new_method=state["new_method"],
        )
        return {"new_method": new_method}

    def _should_retry_smoke_test(self, state: ExecutorSubgraphState) -> str:
        if state.get("smoke_test_passed", False):
            logger.info("Smoke test passed, proceeding to create experiment branches")
            return "create_experiment_branches"
        else:
            # TODO: Add max retry limit check using experiment_iteration
            logger.warning("Smoke test failed, retrying...")
            return "execute_smoke_test"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(ExecutorSubgraphState)

        graph_builder.add_node("execute_smoke_test", self._execute_smoke_test)
        graph_builder.add_node(
            "retrieve_smoke_test_artifacts", self._retrieve_smoke_test_artifacts
        )
        graph_builder.add_node("judge_execution", self._judge_execution)
        graph_builder.add_node(
            "create_experiment_branches", self._create_experiment_branches
        )
        graph_builder.add_node(
            "execute_full_experiments", self._execute_full_experiments
        )
        graph_builder.add_node(
            "retrieve_full_experiment_artifacts",
            self._retrieve_full_experiment_artifacts,
        )

        graph_builder.add_edge(START, "execute_smoke_test")
        graph_builder.add_edge("execute_smoke_test", "retrieve_smoke_test_artifacts")
        graph_builder.add_edge("retrieve_smoke_test_artifacts", "judge_execution")

        graph_builder.add_conditional_edges(
            "judge_execution",
            self._should_retry_smoke_test,
            {
                "execute_smoke_test": "execute_smoke_test",
                "create_experiment_branches": "create_experiment_branches",
            },
        )

        graph_builder.add_edge("create_experiment_branches", "execute_full_experiments")
        graph_builder.add_edge(
            "execute_full_experiments", "retrieve_full_experiment_artifacts"
        )
        graph_builder.add_edge("retrieve_full_experiment_artifacts", END)

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
