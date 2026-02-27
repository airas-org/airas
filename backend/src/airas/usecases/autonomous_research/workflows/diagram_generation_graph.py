import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import (
    GitHubActionsAgent,
    GitHubActionsConclusion,
    GitHubActionsStatus,
    GitHubConfig,
)
from airas.infra.github_client import GithubClient
from airas.usecases.generators.dispatch_diagram_generation_subgraph.dispatch_diagram_generation_subgraph import (
    DispatchDiagramGenerationLLMMapping,
    DispatchDiagramGenerationSubgraph,
)
from airas.usecases.github.poll_github_actions_subgraph.poll_github_actions_subgraph import (
    PollGithubActionsSubgraph,
)

# TODO: Determine after operational use whether a validation loop
# (dispatch_experiment_validation_subgraph) is needed for diagram generation.

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("diagram_generation_graph")(f)  # noqa: E731

_STANDARD_WORKFLOW_RECURSION_LIMIT = 50000


class DiagramGenerationInputState(TypedDict):
    github_config: GitHubConfig


class DiagramGenerationState(DiagramGenerationInputState, total=False):
    diagram_workflow_run_id: int | None


class DiagramGenerationGraph:
    def __init__(
        self,
        github_client: GithubClient,
        github_actions_agent: GitHubActionsAgent,
        diagram_description: str | None = None,
        prompt_path: str | None = None,
        llm_mapping: DispatchDiagramGenerationLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.github_actions_agent = github_actions_agent
        self.diagram_description = diagram_description
        self.prompt_path = prompt_path
        self.llm_mapping = llm_mapping or DispatchDiagramGenerationLLMMapping()

    @record_execution_time
    async def _dispatch_diagram_generation(
        self, state: DiagramGenerationState
    ) -> dict[str, Any]:
        logger.info("=== Dispatch Diagram Generation ===")

        dispatch_result = (
            await DispatchDiagramGenerationSubgraph(
                github_client=self.github_client,
                diagram_description=self.diagram_description,
                prompt_path=self.prompt_path,
                llm_mapping=self.llm_mapping,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "github_actions_agent": self.github_actions_agent,
                }
            )
        )

        if not dispatch_result.get("dispatched", False):
            error_msg = "Failed to dispatch diagram generation workflow"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        logger.info("Diagram generation workflow dispatched successfully")
        return {}

    @record_execution_time
    async def _poll_diagram_generation(
        self, state: DiagramGenerationState
    ) -> dict[str, Any]:
        logger.info("Polling diagram generation workflow...")

        poll_result = (
            await PollGithubActionsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {"github_config": state["github_config"]},
                {"recursion_limit": _STANDARD_WORKFLOW_RECURSION_LIMIT},
            )
        )

        workflow_run_id = poll_result.get("workflow_run_id")
        status: GitHubActionsStatus | None = poll_result.get("status")
        conclusion: GitHubActionsConclusion | None = poll_result.get("conclusion")
        logger.info(
            f"Diagram generation workflow completed: status={status}, conclusion={conclusion}"
        )

        if status is None:
            error_msg = (
                "Diagram generation workflow polling timed out or no status available"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        if status == GitHubActionsStatus.COMPLETED and conclusion in {
            GitHubActionsConclusion.SUCCESS,
            GitHubActionsConclusion.NEUTRAL,
            GitHubActionsConclusion.SKIPPED,
        }:
            logger.info(
                f"Diagram generation workflow completed successfully with conclusion: {conclusion}"
            )
        else:
            error_msg = (
                f"Diagram generation workflow did not complete successfully. "
                f"Status: {status}, conclusion: {conclusion}"
            )
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return {"diagram_workflow_run_id": workflow_run_id}

    def build_graph(self):
        graph_builder = StateGraph(
            DiagramGenerationState,
            input_schema=DiagramGenerationInputState,
        )

        graph_builder.add_node(
            "dispatch_diagram_generation", self._dispatch_diagram_generation
        )
        graph_builder.add_node("poll_diagram_generation", self._poll_diagram_generation)

        graph_builder.add_edge(START, "dispatch_diagram_generation")
        graph_builder.add_edge("dispatch_diagram_generation", "poll_diagram_generation")
        graph_builder.add_edge("poll_diagram_generation", END)

        return graph_builder.compile()
