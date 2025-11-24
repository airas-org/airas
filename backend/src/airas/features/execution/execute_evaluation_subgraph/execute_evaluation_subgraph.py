import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.execution.execute_experiment_subgraph.nodes.execute_experiment import (
    execute_evaluation,
)
from airas.features.execution.execute_experiment_subgraph.nodes.retrieve_artifacts import (
    retrieve_evaluation_artifacts,
)
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_session import ResearchSession
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

execute_evaluation_timed = lambda f: time_node("execute_evaluation_subgraph")(f)  # noqa: E731


class ExecuteEvaluationSubgraphInputState(TypedDict, total=False):
    research_session: ResearchSession
    github_repository_info: GitHubRepositoryInfo


class ExecuteEvaluationSubgraphHiddenState(TypedDict):
    executed_flag: bool


class ExecuteEvaluationSubgraphOutputState(TypedDict):
    research_session: ResearchSession


class ExecuteEvaluationSubgraphState(
    ExecuteEvaluationSubgraphInputState,
    ExecuteEvaluationSubgraphHiddenState,
    ExecuteEvaluationSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class ExecuteEvaluationSubgraph(BaseSubgraph):
    InputState = ExecuteEvaluationSubgraphInputState
    OutputState = ExecuteEvaluationSubgraphOutputState

    def __init__(
        self,
        github_client: GithubClient,
    ):
        self.github_client = github_client

    @execute_evaluation_timed
    async def _execute_evaluation(
        self, state: ExecuteEvaluationSubgraphState
    ) -> dict[str, bool]:
        success = await execute_evaluation(
            github_repository=state["github_repository_info"],
            research_session=state["research_session"],
            github_client=self.github_client,
        )
        return {"executed_flag": success}

    @execute_evaluation_timed
    async def _retrieve_evaluation_artifacts(
        self, state: ExecuteEvaluationSubgraphState
    ) -> dict[str, ResearchSession]:
        research_session = await retrieve_evaluation_artifacts(
            github_repository=state["github_repository_info"],
            research_session=state["research_session"],
            github_client=self.github_client,
        )
        return {"research_session": research_session}

    def build_graph(self):
        graph_builder = StateGraph(ExecuteEvaluationSubgraphState)

        graph_builder.add_node("execute_evaluation", self._execute_evaluation)
        graph_builder.add_node(
            "retrieve_evaluation_artifacts", self._retrieve_evaluation_artifacts
        )

        graph_builder.add_edge(START, "execute_evaluation")
        graph_builder.add_edge("execute_evaluation", "retrieve_evaluation_artifacts")
        graph_builder.add_edge("retrieve_evaluation_artifacts", END)

        return graph_builder.compile()


def main():
    from airas.features.execution.execute_evaluation_subgraph.input_data import (
        execute_evaluation_subgraph_input_data,
    )

    result = ExecuteEvaluationSubgraph().run(execute_evaluation_subgraph_input_data)

    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running ExecuteEvaluationSubgraph: {e}")
        raise
