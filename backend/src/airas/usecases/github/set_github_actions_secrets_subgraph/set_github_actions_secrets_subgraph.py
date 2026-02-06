import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.set_github_actions_secrets_subgraph.nodes.set_github_actions_secrets import (
    set_github_actions_secrets,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("set_github_actions_secrets")(f)  # noqa: E731


class SetGithubActionsSecretsInputState(TypedDict):
    github_config: GitHubConfig


class SetGithubActionsSecretsOutputState(ExecutionTimeState):
    secrets_set: bool


class SetGithubActionsSecretsState(
    SetGithubActionsSecretsInputState,
    SetGithubActionsSecretsOutputState,
):
    pass


class SetGithubActionsSecretsSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        secret_names: list[str]
        | None = None,  # TODO: no caller passes a custom list; consider removing
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
        self, state: SetGithubActionsSecretsState
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

    def build_graph(self):
        graph_builder = StateGraph(
            SetGithubActionsSecretsState,
            input_schema=SetGithubActionsSecretsInputState,
            output_schema=SetGithubActionsSecretsOutputState,
        )
        graph_builder.add_node(
            "set_github_actions_secrets", self._set_github_actions_secrets
        )

        graph_builder.add_edge(START, "set_github_actions_secrets")
        graph_builder.add_edge("set_github_actions_secrets", END)

        return graph_builder.compile()
