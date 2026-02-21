import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.github import (
    GitHubActionsAgent,
    GitHubActionsConclusion,
    GitHubActionsStatus,
    GitHubConfig,
)
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.wandb import WandbConfig
from airas.infra.github_client import GithubClient
from airas.usecases.generators.dispatch_code_generation_subgraph.dispatch_code_generation_subgraph import (
    DispatchCodeGenerationLLMMapping,
    DispatchCodeGenerationSubgraph,
)
from airas.usecases.github.poll_github_actions_subgraph.poll_github_actions_subgraph import (
    PollGithubActionsSubgraph,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("code_generation_graph")(f)  # noqa: E731

_STANDARD_WORKFLOW_RECURSION_LIMIT = 50000


class WorkflowExecutionError(Exception):
    pass


class GitHubActionsWorkflowError(WorkflowExecutionError):
    def __init__(
        self,
        message: str,
        workflow_name: str,
        status: str | None = None,
        conclusion: str | None = None,
    ):
        super().__init__(message)
        self.workflow_name = workflow_name
        self.status = status
        self.conclusion = conclusion


class CodeGenerationGraphLLMMapping(BaseModel):
    dispatch_code_generation: DispatchCodeGenerationLLMMapping = (
        DispatchCodeGenerationLLMMapping()
    )


class CodeGenerationGraphInputState(TypedDict):
    github_config: GitHubConfig
    research_topic: str
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign


class CodeGenerationGraphState(CodeGenerationGraphInputState, total=False):
    pass


class CodeGenerationGraph:
    def __init__(
        self,
        github_client: GithubClient,
        wandb_config: WandbConfig,
        github_actions_agent: GitHubActionsAgent,
        llm_mapping: CodeGenerationGraphLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.wandb_config = wandb_config
        self.github_actions_agent = github_actions_agent
        self.llm_mapping = llm_mapping or CodeGenerationGraphLLMMapping()

    def _validate_github_actions_completion(
        self,
        workflow_name: str,
        status: GitHubActionsStatus | None,
        conclusion: GitHubActionsConclusion | None,
    ) -> None:
        if status is None:
            error_msg = (
                f"{workflow_name} workflow polling timed out or no status available"
            )
            logger.error(error_msg)
            raise GitHubActionsWorkflowError(
                error_msg, workflow_name=workflow_name, status=None, conclusion=None
            )

        if status == GitHubActionsStatus.COMPLETED:
            if conclusion not in {
                GitHubActionsConclusion.SUCCESS,
                GitHubActionsConclusion.NEUTRAL,
                GitHubActionsConclusion.SKIPPED,
            }:
                error_msg = (
                    f"{workflow_name} workflow failed with conclusion: {conclusion}"
                )
                logger.error(error_msg)
                raise GitHubActionsWorkflowError(
                    error_msg,
                    workflow_name=workflow_name,
                    status=str(status),
                    conclusion=str(conclusion),
                )
            logger.info(
                f"{workflow_name} workflow completed successfully with conclusion: {conclusion}"
            )
            return

        if status in {GitHubActionsStatus.FAILURE, GitHubActionsStatus.STARTUP_FAILURE}:
            error_msg = (
                f"{workflow_name} workflow did not complete successfully. "
                f"Status: {status}, conclusion: {conclusion}"
            )
            logger.error(error_msg)
            raise GitHubActionsWorkflowError(
                error_msg,
                workflow_name=workflow_name,
                status=str(status),
                conclusion=str(conclusion),
            )

        error_msg = (
            f"{workflow_name} workflow ended in unexpected state. "
            f"Status: {status}, conclusion: {conclusion}"
        )
        logger.error(error_msg)
        raise GitHubActionsWorkflowError(
            error_msg,
            workflow_name=workflow_name,
            status=str(status),
            conclusion=str(conclusion),
        )

    @record_execution_time
    async def _dispatch_code_generation(
        self, state: CodeGenerationGraphState
    ) -> dict[str, Any]:
        logger.info("=== Dispatch Code Generation ===")
        result = (
            await DispatchCodeGenerationSubgraph(
                github_client=self.github_client,
                llm_mapping=self.llm_mapping.dispatch_code_generation,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "research_topic": state["research_topic"],
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                    "wandb_config": self.wandb_config,
                    "github_actions_agent": self.github_actions_agent,
                }
            )
        )

        if not result.get("dispatched", False):
            error_msg = "Failed to dispatch code generation workflow"
            logger.error(error_msg)
            raise WorkflowExecutionError(error_msg)

        logger.info("Code generation workflow dispatched successfully")
        return {}

    @record_execution_time
    async def _poll_code_generation(
        self, state: CodeGenerationGraphState
    ) -> dict[str, Any]:
        logger.info("Polling code generation workflow...")
        result = (
            await PollGithubActionsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {"github_config": state["github_config"]},
                {"recursion_limit": _STANDARD_WORKFLOW_RECURSION_LIMIT},
            )
        )

        status = result.get("status")
        conclusion = result.get("conclusion")
        logger.info(
            f"Code generation workflow completed: status={status}, conclusion={conclusion}"
        )
        self._validate_github_actions_completion("Code Generation", status, conclusion)
        return {}

    def build_graph(self):
        graph_builder = StateGraph(
            CodeGenerationGraphState,
            input_schema=CodeGenerationGraphInputState,
        )

        graph_builder.add_node(
            "dispatch_code_generation", self._dispatch_code_generation
        )
        graph_builder.add_node("poll_code_generation", self._poll_code_generation)

        graph_builder.add_edge(START, "dispatch_code_generation")
        graph_builder.add_edge("dispatch_code_generation", "poll_code_generation")
        graph_builder.add_edge("poll_code_generation", END)

        return graph_builder.compile()
