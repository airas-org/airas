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
from airas.features.execution.execute_experiment_subgraph.input_data import (
    execute_experiment_subgraph_input_data,
)
from airas.features.execution.execute_experiment_subgraph.nodes.create_experiment_branches import (
    create_experiment_branches,
)
from airas.features.execution.execute_experiment_subgraph.nodes.execute_experiment import (
    execute_full_experiments,
    execute_trial_experiment,
)
from airas.features.execution.execute_experiment_subgraph.nodes.retrieve_artifacts import (
    retrieve_trial_experiment_artifacts,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_iteration import ExperimentalResults
from airas.types.research_session import ResearchSession
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

executor_timed = lambda f: time_node("execute_experiment_subgraph")(f)  # noqa: E731


class ExecuteExperimentLLMMapping(BaseModel):
    judge_execution: LLM_MODEL = DEFAULT_NODE_LLMS["judge_execution"]


class ExecuteExperimentSubgraphInputState(TypedDict, total=False):
    github_repository_info: GitHubRepositoryInfo
    research_session: ResearchSession


class ExecuteExperimentSubgraphHiddenState(TypedDict):
    trial_experiment_results: ExperimentalResults
    trial_experiment_passed: bool
    experiment_iteration: int
    executed_flag: bool


class ExecuteExperimentSubgraphOutputState(TypedDict):
    research_session: ResearchSession


class ExecutorSubgraphState(
    ExecuteExperimentSubgraphInputState,
    ExecuteExperimentSubgraphHiddenState,
    ExecuteExperimentSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class ExecuteExperimentSubgraph(BaseSubgraph):
    InputState = ExecuteExperimentSubgraphInputState
    OutputState = ExecuteExperimentSubgraphOutputState

    def __init__(
        self,
        runner_type: RunnerType = "ubuntu-latest",
        llm_mapping: dict[str, str] | ExecuteExperimentLLMMapping | None = None,
    ):
        self.runner_type = runner_type

        if llm_mapping is None:
            self.llm_mapping = ExecuteExperimentLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = ExecuteExperimentLLMMapping.model_validate(
                    llm_mapping
                )
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, ExecuteExperimentLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or ExecuteExperimentLLMMapping, "
                f"but got {type(llm_mapping)}"
            )

        check_api_key(
            github_personal_access_token_check=True,
            llm_api_key_check=True,
        )

    @executor_timed
    def _initialize(
        self, state: ExecutorSubgraphState
    ) -> dict[str, int | tuple[bool, str] | dict[str, tuple[bool, str]]]:
        # Always increment experiment_iteration to create a new iteration folder
        return {
            "experiment_iteration": state.get("experiment_iteration", 0) + 1,
        }

    @executor_timed
    async def _execute_trial_experiment(
        self, state: ExecutorSubgraphState
    ) -> dict[str, bool]:
        success = await execute_trial_experiment(
            github_repository=state["github_repository_info"],
            experiment_iteration=state["experiment_iteration"],
            runner_type=cast(RunnerType, self.runner_type),
            research_session=state["research_session"],
        )
        return {"executed_flag": success}

    @executor_timed
    async def _retrieve_trial_experiment_artifacts(
        self, state: ExecutorSubgraphState
    ) -> dict[str, ResearchSession | ExperimentalResults]:
        (
            research_session,
            trial_experiment_results,
        ) = await retrieve_trial_experiment_artifacts(
            github_repository=state["github_repository_info"],
            experiment_iteration=state["experiment_iteration"],
            research_session=state["research_session"],
        )
        return {
            "research_session": research_session,
            "trial_experiment_results": trial_experiment_results,
        }

    @executor_timed
    def _judge_execution(self, state: ExecutorSubgraphState) -> dict[str, bool | int]:
        if not (trial_experiment_results := state["trial_experiment_results"]):
            logger.error("No trial_experiment_results found in state")
            return {
                "trial_experiment_passed": False,
            }

        is_successful = judge_execution(
            llm_name=self.llm_mapping.judge_execution,
            stdout_text=trial_experiment_results.stdout or "",
            stderr_text=trial_experiment_results.stderr or "",
            github_repository_info=state["github_repository_info"],
        )
        logger.info(
            f"Trial experiment judgment: {'PASSED' if is_successful else 'FAILED'}"
        )

        return {
            "trial_experiment_passed": is_successful,
        }

    @executor_timed
    async def _create_experiment_branches(
        self, state: ExecutorSubgraphState
    ) -> dict[str, ResearchSession]:
        research_session = await create_experiment_branches(
            github_repository_info=state["github_repository_info"],
            research_session=state["research_session"],
        )
        return {"research_session": research_session}

    @executor_timed
    async def _execute_full_experiments(
        self, state: ExecutorSubgraphState
    ) -> dict[str, bool]:
        success = await execute_full_experiments(
            github_repository=state["github_repository_info"],
            experiment_iteration=state["experiment_iteration"],
            runner_type=cast(RunnerType, self.runner_type),
            research_session=state["research_session"],
        )
        return {"executed_flag": success}

    def _should_retry_trial_experiment(self, state: ExecutorSubgraphState) -> str:
        if state.get("trial_experiment_passed", False):
            logger.info(
                "Trial experiment passed, proceeding to create experiment branches"
            )
            return "create_experiment_branches"
        else:
            # TODO: Add max retry limit check using experiment_iteration
            logger.warning("Trial experiment failed, retrying...")
            return "execute_trial_experiment"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(ExecutorSubgraphState)

        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node(
            "execute_trial_experiment", self._execute_trial_experiment
        )
        graph_builder.add_node(
            "retrieve_trial_experiment_artifacts",
            self._retrieve_trial_experiment_artifacts,
        )
        graph_builder.add_node("judge_execution", self._judge_execution)
        graph_builder.add_node(
            "create_experiment_branches", self._create_experiment_branches
        )
        graph_builder.add_node(
            "execute_full_experiments", self._execute_full_experiments
        )

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "execute_trial_experiment")
        graph_builder.add_edge(
            "execute_trial_experiment", "retrieve_trial_experiment_artifacts"
        )
        graph_builder.add_edge("retrieve_trial_experiment_artifacts", "judge_execution")
        graph_builder.add_conditional_edges(
            "judge_execution",
            self._should_retry_trial_experiment,
            {
                "execute_trial_experiment": "execute_trial_experiment",
                "create_experiment_branches": "create_experiment_branches",
            },
        )
        graph_builder.add_edge("create_experiment_branches", "execute_full_experiments")
        graph_builder.add_edge("execute_full_experiments", END)

        return graph_builder.compile()


def main():
    from airas.types.wandb import WandbInfo

    wandb_info = WandbInfo(entity="gengaru617-personal", project="251017-test")
    runner_type = "A100_80GM×8"
    result = ExecuteExperimentSubgraph(
        runner_type=runner_type,
        wandb_info=wandb_info,
    ).run(execute_experiment_subgraph_input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running ExecutorSubgraph: {e}")
        raise
