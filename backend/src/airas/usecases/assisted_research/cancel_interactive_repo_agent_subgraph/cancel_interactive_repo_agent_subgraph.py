import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("cancel_interactive_repo_agent_subgraph")(f)  # noqa: E731


class CancelInteractiveRepoAgentSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    workflow_run_id: int


class CancelInteractiveRepoAgentSubgraphOutputState(ExecutionTimeState):
    cancelled: bool


class CancelInteractiveRepoAgentSubgraphState(
    CancelInteractiveRepoAgentSubgraphInputState,
    CancelInteractiveRepoAgentSubgraphOutputState,
    total=False,
):
    pass


class CancelInteractiveRepoAgentSubgraph:
    def __init__(self, github_client: GithubClient):
        self.github_client = github_client

    @record_execution_time
    async def _cancel_interactive_repo_agent(
        self, state: CancelInteractiveRepoAgentSubgraphState
    ) -> dict[str, bool]:
        github_config = state["github_config"]
        workflow_run_id = state["workflow_run_id"]

        logger.info(
            f"Cancelling interactive repo agent (workflow_run_id={workflow_run_id})"
        )

        cancelled = await self.github_client.acancel_workflow_run(
            github_owner=github_config.github_owner,
            repository_name=github_config.repository_name,
            workflow_run_id=workflow_run_id,
        )

        if cancelled:
            logger.info(
                f"Interactive repo agent cancelled (workflow_run_id={workflow_run_id})"
            )
        else:
            logger.error(
                f"Interactive repo agent cancel failed (workflow_run_id={workflow_run_id})"
            )

        return {"cancelled": cancelled}

    def build_graph(self):
        graph_builder = StateGraph(
            CancelInteractiveRepoAgentSubgraphState,
            input_schema=CancelInteractiveRepoAgentSubgraphInputState,
            output_schema=CancelInteractiveRepoAgentSubgraphOutputState,
        )

        graph_builder.add_node(
            "cancel_interactive_repo_agent", self._cancel_interactive_repo_agent
        )

        graph_builder.add_edge(START, "cancel_interactive_repo_agent")
        graph_builder.add_edge("cancel_interactive_repo_agent", END)

        return graph_builder.compile()
