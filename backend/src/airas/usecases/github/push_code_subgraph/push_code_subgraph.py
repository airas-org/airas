import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.push_code_subgraph.nodes.push_files_to_branch import (
    push_files_to_branch,
)
from airas.usecases.github.push_code_subgraph.nodes.set_github_actions_secrets import (
    set_github_actions_secrets,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("push_code_subgraph")(f)  # noqa: E731


class PushCodeSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    experiment_code: ExperimentCode


class PushCodeSubgraphOutputState(ExecutionTimeState):
    code_pushed: bool


class PushCodeSubgraphState(
    PushCodeSubgraphInputState,
    PushCodeSubgraphOutputState,
):
    secrets_set: bool


class PushCodeSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        secret_names: list[str] | None = None,
    ):
        self.secret_names = secret_names or [
            "OPENAI_API_KEY",
            "GEMINI_API_KEY",
            "ANTHROPIC_API_KEY",
            "OPENROUTER_API_KEY",
            "AWS_BEARER_TOKEN_BEDROCK",
            "WANDB_API_KEY",
            "HF_TOKEN",
            "LANGFUSE_SECRET_KEY",
            "LANGFUSE_PUBLIC_KEY",
            "LANGFUSE_BASE_URL",
        ]
        self.github_client = github_client

    @record_execution_time
    def _set_github_actions_secrets(
        self, state: PushCodeSubgraphState
    ) -> dict[str, bool]:
        if not self.secret_names:
            logger.info(
                "No secret names provided, skipping GitHub Actions secrets setup"
            )
            return {"secrets_set": False}

        success = set_github_actions_secrets(
            github_config=state["github_config"],
            github_client=self.github_client,
            secret_names=self.secret_names,
        )
        return {"secrets_set": success}

    @record_execution_time
    def _push_files_to_branch(self, state: PushCodeSubgraphState) -> dict[str, bool]:
        commit_message = "Add generated experiment files"

        success = push_files_to_branch(
            github_config=state["github_config"],
            github_client=self.github_client,
            experiment_code=state["experiment_code"],
            commit_message=commit_message,
        )

        if not success:
            logger.error("Failed to push files to branch")
            raise RuntimeError("Failed to push code to GitHub branch")

        return {"code_pushed": success}

    def build_graph(self):
        graph_builder = StateGraph(
            PushCodeSubgraphState,
            input_schema=PushCodeSubgraphInputState,
            output_schema=PushCodeSubgraphOutputState,
        )
        graph_builder.add_node(
            "set_github_actions_secrets", self._set_github_actions_secrets
        )
        graph_builder.add_node("push_files_to_branch", self._push_files_to_branch)

        graph_builder.add_edge(START, "set_github_actions_secrets")
        graph_builder.add_edge("set_github_actions_secrets", "push_files_to_branch")
        graph_builder.add_edge("push_files_to_branch", END)

        return graph_builder.compile()
