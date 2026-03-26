import json
import logging
from typing import Any

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

setup_logging()
logger = logging.getLogger(__name__)


def record_execution_time(f):
    return time_node("generate_verification_code_subgraph")(f)  # noqa: E731


class GenerateVerificationCodeLLMMapping(BaseModel):
    dispatch_verification_code_generation: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "dispatch_experiment_code_generation"
    ]


class GenerateVerificationCodeSubgraphInputState(TypedDict):
    user_query: str
    what_to_verify: str
    experiment_settings: dict[str, dict[str, Any]]
    steps: list[str]
    modification_notes: str
    repository_name: str
    github_config: GitHubConfig
    github_actions_agent: GitHubActionsAgent


class GenerateVerificationCodeSubgraphOutputState(ExecutionTimeState):
    dispatched: bool
    workflow_run_id: int | None


class GenerateVerificationCodeSubgraphState(
    GenerateVerificationCodeSubgraphInputState,
    GenerateVerificationCodeSubgraphOutputState,
    total=False,
):
    pass


class GenerateVerificationCodeSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        workflow_file: str = "run_verification_code_generator.yml",
        llm_mapping: GenerateVerificationCodeLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.workflow_file = workflow_file
        self.llm_mapping = llm_mapping or GenerateVerificationCodeLLMMapping()

    @record_execution_time
    async def _dispatch_verification_code_generation(
        self, state: GenerateVerificationCodeSubgraphState
    ) -> dict:
        github_config = state["github_config"]
        github_actions_agent = state["github_actions_agent"]
        user_query = state["user_query"]
        what_to_verify = state["what_to_verify"]
        experiment_settings = state["experiment_settings"]
        steps = state["steps"]
        modification_notes = state["modification_notes"]

        logger.info(
            f"Dispatching verification code generation on branch '{github_config.branch_name}'"
        )

        inputs = {
            "branch_name": github_config.branch_name,
            "user_query": user_query,
            "what_to_verify": what_to_verify,
            "experiment_settings": json.dumps(experiment_settings),
            "steps": json.dumps(steps),
            "modification_notes": modification_notes,
            "github_actions_agent": github_actions_agent,
            "model_name": self.llm_mapping.dispatch_verification_code_generation.llm_name,
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
                f"Verification code generation dispatch successful (workflow_run_id={workflow_run_id})"
            )
        else:
            logger.error("Verification code generation dispatch failed")

        return {
            "dispatched": workflow_run_id is not None,
            "workflow_run_id": workflow_run_id,
        }

    def build_graph(self):
        graph_builder = StateGraph(
            GenerateVerificationCodeSubgraphState,
            input_schema=GenerateVerificationCodeSubgraphInputState,
            output_schema=GenerateVerificationCodeSubgraphOutputState,
        )

        graph_builder.add_node(
            "dispatch_verification_code_generation",
            self._dispatch_verification_code_generation,
        )

        graph_builder.add_edge(START, "dispatch_verification_code_generation")
        graph_builder.add_edge("dispatch_verification_code_generation", END)

        return graph_builder.compile()
