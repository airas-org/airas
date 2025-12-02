import logging
import time
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from typing_extensions import TypedDict

from airas.features.github.nodes.create_branch import (
    create_branch,
)
from airas.features.github.prepare_repository_subgraph.nodes.check_branch_existence import (
    check_branch_existence,
)
from airas.features.github.prepare_repository_subgraph.nodes.check_repository_from_template import (
    check_repository_from_template,
)
from airas.features.github.prepare_repository_subgraph.nodes.create_repository_from_template import (
    create_repository_from_template,
)
from airas.features.github.prepare_repository_subgraph.nodes.retrieve_main_branch_sha import (
    retrieve_main_branch_sha,
)
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubConfig
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

recode_execution_time = lambda f: time_node("prepare_repository")(f)  # noqa: E731


class PrepareRepositoryInputState(TypedDict):
    github_config: GitHubConfig


class PrepareRepositoryOutputState(ExecutionTimeState):
    is_repository_ready: bool
    is_branch_ready: bool


class PrepareRepositoryState(PrepareRepositoryInputState, PrepareRepositoryOutputState):
    target_branch_sha: str
    main_branch_sha: str
    is_repository_from_template: bool
    is_branch_already_exists: bool
    is_branch_created: bool


class PrepareRepositorySubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        template_owner: str = "airas-org",
        template_repo: str = "airas-template",
        is_private: bool = False,
    ):
        check_api_key(
            github_personal_access_token_check=True,
        )
        self.github_client = github_client
        self.template_owner = template_owner
        self.template_repo = template_repo
        self.is_private = is_private

    @recode_execution_time
    def _check_repository_from_template(
        self, state: PrepareRepositoryState
    ) -> Command[Literal["create_repository_from_template", "check_branch_existence"]]:
        is_repository_from_template = check_repository_from_template(
            github_config=state["github_config"],
            github_client=self.github_client,
            template_owner=self.template_owner,
            template_repo=self.template_repo,
        )

        goto: Literal["create_repository_from_template", "check_branch_existence"] = (
            "create_repository_from_template"
            if not is_repository_from_template
            else "check_branch_existence"
        )

        return Command(
            update={"is_repository_from_template": is_repository_from_template},
            goto=goto,
        )

    @recode_execution_time
    def _create_repository_from_template(
        self, state: PrepareRepositoryState
    ) -> dict[str, Literal[True]]:
        is_repository_from_template = create_repository_from_template(
            github_config=state["github_config"],
            github_client=self.github_client,
            template_owner=self.template_owner,
            template_repo=self.template_repo,
            is_private=self.is_private,
        )
        return {"is_repository_from_template": is_repository_from_template}

    @recode_execution_time
    def _check_branch_existence(
        self, state: PrepareRepositoryState
    ) -> Command[Literal["retrieve_main_branch_sha", "finalize_state"]]:
        time.sleep(5)
        target_branch_sha = check_branch_existence(
            github_config=state["github_config"],
            github_client=self.github_client,
        )
        is_branch_already_exists = bool(target_branch_sha)

        goto: Literal["retrieve_main_branch_sha", "finalize_state"] = (
            "retrieve_main_branch_sha"
            if not is_branch_already_exists
            else "finalize_state"
        )

        return Command(
            update={
                "target_branch_sha": target_branch_sha,
                "is_branch_already_exists": is_branch_already_exists,
            },
            goto=goto,
        )

    @recode_execution_time
    def _retrieve_main_branch_sha(
        self, state: PrepareRepositoryState
    ) -> dict[str, str]:
        main_branch_sha = retrieve_main_branch_sha(
            github_config=state["github_config"],
            github_client=self.github_client,
        )
        return {"main_branch_sha": main_branch_sha}

    @recode_execution_time
    async def _create_branch(self, state: PrepareRepositoryState) -> dict[str, bool]:
        is_branch_created = await create_branch(
            github_client=self.github_client,
            github_owner=state["github_config"].github_owner,
            repository_name=state["github_config"].repository_name,
            new_branch_name=state["github_config"].branch_name,
            from_sha=state["main_branch_sha"],
        )
        return {"is_branch_created": is_branch_created}

    @recode_execution_time
    def _finalize_state(self, state: PrepareRepositoryState) -> dict[str, bool]:
        is_repository_ready = state.get("is_repository_from_template", False)
        is_branch_ready = state.get("is_branch_already_exists", False) or state.get(
            "is_branch_created", False
        )
        return {
            "is_repository_ready": is_repository_ready,
            "is_branch_ready": is_branch_ready,
        }

    def build_graph(self):
        graph_builder = StateGraph(
            PrepareRepositoryState,
            input_schema=PrepareRepositoryInputState,
            output_schema=PrepareRepositoryOutputState,
        )

        graph_builder.add_node(
            "check_repository_from_template", self._check_repository_from_template
        )
        graph_builder.add_node(
            "create_repository_from_template", self._create_repository_from_template
        )
        graph_builder.add_node("check_branch_existence", self._check_branch_existence)
        graph_builder.add_node(
            "retrieve_main_branch_sha", self._retrieve_main_branch_sha
        )
        graph_builder.add_node("create_branch", self._create_branch)
        graph_builder.add_node("finalize_state", self._finalize_state)

        graph_builder.add_edge(START, "check_repository_from_template")
        graph_builder.add_edge(
            "create_repository_from_template", "check_branch_existence"
        )
        graph_builder.add_edge("retrieve_main_branch_sha", "create_branch")
        graph_builder.add_edge("create_branch", "finalize_state")
        graph_builder.add_edge("finalize_state", END)
        return graph_builder.compile()
