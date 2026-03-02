import asyncio
import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubActionsAgent, GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.dispatch_workflow_and_get_run_id import (
    dispatch_workflow_and_get_run_id,
)
from airas.usecases.github.nodes.download_artifact import (
    download_and_parse_artifact_by_id,
)

setup_logging()
logger = logging.getLogger(__name__)


def record_execution_time(f):
    return time_node("dispatch_interactive_repo_agent_subgraph")(f)  # noqa: E731


# NOTE: Dispatch and session URL retrieval are intentionally combined in a single subgraph.
# Since the Cloudflare Tunnel URL is generated shortly after the workflow starts,
# polling for the artifact here avoids an extra round-trip from the caller.

_ARTIFACT_POLL_INTERVAL_SECONDS = 10
_ARTIFACT_MAX_ATTEMPTS = 12  # max ~120s; process normally completes in ~50s
_ARTIFACT_NAME = "tunnel-url"


class DispatchInteractiveRepoAgentLLMMapping(BaseModel):
    dispatch_interactive_repo_agent: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "dispatch_interactive_repo_agent"
    ]


class DispatchInteractiveRepoAgentSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    github_actions_agent: GitHubActionsAgent


class DispatchInteractiveRepoAgentSubgraphOutputState(ExecutionTimeState):
    dispatched: bool
    workflow_run_id: int | None
    artifact_data: dict


class DispatchInteractiveRepoAgentSubgraphState(
    DispatchInteractiveRepoAgentSubgraphInputState,
    DispatchInteractiveRepoAgentSubgraphOutputState,
    total=False,
):
    pass


class DispatchInteractiveRepoAgentSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        session_username: str,
        session_password: str,
        workflow_file: str = "run_interactive_repo_agent.yml",
        llm_mapping: DispatchInteractiveRepoAgentLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.session_username = session_username
        self.session_password = session_password
        self.workflow_file = workflow_file
        self.llm_mapping = llm_mapping or DispatchInteractiveRepoAgentLLMMapping()

    @record_execution_time
    async def _dispatch_interactive_repo_agent(
        self, state: DispatchInteractiveRepoAgentSubgraphState
    ) -> dict:
        github_config = state["github_config"]
        github_actions_agent = state["github_actions_agent"]

        logger.info(
            f"Dispatching interactive repo agent on branch '{github_config.branch_name}'"
        )

        inputs = {
            "session_username": self.session_username,
            "session_password": self.session_password,
            "github_actions_agent": github_actions_agent,
            "model_name": self.llm_mapping.dispatch_interactive_repo_agent.llm_name,
        }

        workflow_run_id = await dispatch_workflow_and_get_run_id(
            self.github_client,
            github_config.github_owner,
            github_config.repository_name,
            github_config.branch_name,
            self.workflow_file,
            inputs,
        )

        if workflow_run_id is not None:
            logger.info(
                f"Interactive repo agent dispatch successful (workflow_run_id={workflow_run_id})"
            )
        else:
            logger.error("Interactive repo agent dispatch failed")

        return {
            "dispatched": workflow_run_id is not None,
            "workflow_run_id": workflow_run_id,
        }

    @record_execution_time
    async def _poll_for_session_url(
        self, state: DispatchInteractiveRepoAgentSubgraphState
    ) -> dict:
        github_config = state["github_config"]
        workflow_run_id = state.get("workflow_run_id")

        if workflow_run_id is None:
            logger.error("Cannot poll for session URL: workflow_run_id is None")
            return {"artifact_data": {}}

        logger.info(
            f"Polling for session URL artifact (workflow_run_id={workflow_run_id})"
        )

        for attempt in range(1, _ARTIFACT_MAX_ATTEMPTS + 1):
            artifacts_response = await self.github_client.alist_workflow_run_artifacts(
                github_owner=github_config.github_owner,
                repository_name=github_config.repository_name,
                workflow_run_id=workflow_run_id,
            )

            artifacts = (artifacts_response or {}).get("artifacts", [])
            target = next((a for a in artifacts if a["name"] == _ARTIFACT_NAME), None)
            if target is not None:
                artifact_id: int = target["id"]
                logger.info(
                    f"Artifact '{_ARTIFACT_NAME}' found (attempt {attempt}, id={artifact_id}), downloading..."
                )
                artifact_data = await download_and_parse_artifact_by_id(
                    github_client=self.github_client,
                    github_owner=github_config.github_owner,
                    repository_name=github_config.repository_name,
                    artifact_id=artifact_id,
                )
                logger.info(
                    "Session URL retrieved"
                )  # URL intentionally omitted to avoid leaking session access
                return {"artifact_data": artifact_data}

            logger.info(
                f"Artifact '{_ARTIFACT_NAME}' not yet available "
                f"(attempt {attempt}/{_ARTIFACT_MAX_ATTEMPTS})"
            )
            await asyncio.sleep(_ARTIFACT_POLL_INTERVAL_SECONDS)

        logger.error(
            f"Session URL artifact not found after {_ARTIFACT_MAX_ATTEMPTS} attempts"
        )
        return {"artifact_data": {}}

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchInteractiveRepoAgentSubgraphState,
            input_schema=DispatchInteractiveRepoAgentSubgraphInputState,
            output_schema=DispatchInteractiveRepoAgentSubgraphOutputState,
        )

        graph_builder.add_node(
            "dispatch_interactive_repo_agent", self._dispatch_interactive_repo_agent
        )
        graph_builder.add_node("poll_for_session_url", self._poll_for_session_url)

        graph_builder.add_edge(START, "dispatch_interactive_repo_agent")
        graph_builder.add_edge(
            "dispatch_interactive_repo_agent", "poll_for_session_url"
        )
        graph_builder.add_edge("poll_for_session_url", END)

        return graph_builder.compile()
