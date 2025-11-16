import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.create.create_code_subgraph.nodes.push_files_to_branch import (
    push_files_to_branch,
)
from airas.features.create.create_code_subgraph.nodes.set_github_actions_secrets import (
    set_github_actions_secrets,
)
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_session import ResearchSession
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("push_code_subgraph")(f)  # noqa: E731


class PushCodeSubgraphInputState(TypedDict, total=False):
    github_repository_info: GitHubRepositoryInfo
    research_session: ResearchSession


class PushCodeSubgraphHiddenState(TypedDict):
    pass


class PushCodeSubgraphOutputState(TypedDict):
    research_session: ResearchSession


class PushCodeSubgraphState(
    PushCodeSubgraphInputState,
    PushCodeSubgraphHiddenState,
    PushCodeSubgraphOutputState,
    total=False,
):
    pass


class PushCodeSubgraph(BaseSubgraph):
    InputState = PushCodeSubgraphInputState
    OutputState = PushCodeSubgraphOutputState

    def __init__(
        self,
        github_client: GithubClient,
        secret_names: list[str] | None = None,
        max_code_validations: int = 3,
    ):
        self.secret_names = secret_names or []
        self.max_code_validations = max_code_validations

        self.github_client = github_client
        check_api_key(
            github_personal_access_token_check=True,
        )

    def _initialize(
        self, state: PushCodeSubgraphState
    ) -> dict[str, int | tuple[bool, str]]:
        return {
            "code_validation": (False, ""),
            "code_validation_count": 0,
        }

    @record_execution_time
    def _push_files_to_branch(
        self, state: PushCodeSubgraphState
    ) -> dict[str, ResearchSession]:
        commit_message = "Add generated experiment files."

        research_session = state["research_session"]
        success = push_files_to_branch(
            github_repository_info=state["github_repository_info"],
            github_client=self.github_client,
            research_session=research_session,
            commit_message=commit_message,
        )

        if not success:
            logger.warning("Failed to push files to branch, but continuing...")

        return {"research_session": research_session}

    @record_execution_time
    def _set_github_actions_secrets(self, state: PushCodeSubgraphState) -> dict:
        if not self.secret_names:
            logger.info(
                "No secret names provided, skipping GitHub Actions secrets setup"
            )
            return {}

        set_github_actions_secrets(
            github_repository_info=state["github_repository_info"],
            github_client=self.github_client,
            secret_names=self.secret_names,
        )
        return {}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(PushCodeSubgraphState)
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node("push_files_to_branch", self._push_files_to_branch)
        graph_builder.add_node(
            "set_github_actions_secrets", self._set_github_actions_secrets
        )

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "push_files_to_branch")
        graph_builder.add_edge("push_files_to_branch", "set_github_actions_secrets")
        graph_builder.add_edge("set_github_actions_secrets", END)

        return graph_builder.compile()


def main():
    from airas.features.create.create_code_subgraph.input_data import (
        create_code_subgraph_input_data,
    )
    from airas.services.api_client.api_clients_container import sync_container
    from airas.types.wandb import WandbInfo

    sync_container.wire(modules=[__name__])

    secret_names = ["HF_TOKEN", "WANDB_API_KEY", "ANTHROPIC_API_KEY"]
    wandb_info = WandbInfo(entity="gengaru617-personal", project="251017-test")
    max_code_validations = 10
    result = PushCodeSubgraph(
        secret_names=secret_names,
        wandb_info=wandb_info,
        max_code_validations=max_code_validations,
    ).run(create_code_subgraph_input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateCodeSubgraph: {e}")
        raise
