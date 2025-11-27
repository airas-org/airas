import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.github.push_code_subgraph.nodes.push_files_to_branch import (
    push_files_to_branch,
)
from airas.features.github.push_code_subgraph.nodes.set_github_actions_secrets import (
    set_github_actions_secrets,
)
from airas.services.api_client.github_client import GithubClient
from airas.types.experiment_code import ExperimentCode
from airas.types.github import GitHubConfig
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("push_code_subgraph")(f)  # noqa: E731


class PushCodeSubgraphInputState(TypedDict):
    github_config: GitHubConfig
    experiment_code: ExperimentCode


class PushCodeSubgraphHiddenState(TypedDict):
    secrets_set: bool


class PushCodeSubgraphOutputState(TypedDict):
    files_pushed: bool


class PushCodeSubgraphState(
    PushCodeSubgraphInputState,
    PushCodeSubgraphHiddenState,
    PushCodeSubgraphOutputState,
):
    pass


class PushCodeSubgraph(BaseSubgraph):
    InputState = PushCodeSubgraphInputState
    OutputState = PushCodeSubgraphOutputState

    def __init__(
        self,
        github_client: GithubClient,
        secret_names: list[str] | None = None,
    ):
        self.secret_names = secret_names or [
            "HF_TOKEN",
            "WANDB_API_KEY",
            "ANTHROPIC_API_KEY",
        ]
        self.github_client = github_client
        check_api_key(
            github_personal_access_token_check=True,
        )

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

        return {"files_pushed": success}

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


async def main():
    from airas.core.container import container
    from airas.features.github.push_code_subgraph.input_data import (
        push_code_subgraph_input_data,
    )

    container.wire(modules=[__name__])

    try:
        result = await PushCodeSubgraph(
            github_client=container.github_client,
        ).arun(push_code_subgraph_input_data)
        print(f"result: {result}")
    finally:
        await container.shutdown_resources()


if __name__ == "__main__":
    import asyncio

    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running PushCodeSubgraph: {e}")
        raise
