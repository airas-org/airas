import argparse
import logging
import time
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
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
from airas.types.github import GitHubRepositoryInfo
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

prepare_repository_timed = lambda f: time_node("prepare_repository")(f)  # noqa: E731


class PrepareRepositoryInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo


class PrepareRepositoryHiddenState(TypedDict):
    target_branch_sha: str
    main_branch_sha: str
    is_repository_from_template: bool
    is_branch_already_exists: bool
    is_branch_created: bool
    is_repository_ready: bool
    is_branch_ready: bool


class PrepareRepositoryOutputState(TypedDict): ...


class PrepareRepositoryState(
    PrepareRepositoryInputState,
    PrepareRepositoryHiddenState,
    PrepareRepositoryOutputState,
    ExecutionTimeState,
):
    pass


class PrepareRepositorySubgraph(BaseSubgraph):
    InputState = PrepareRepositoryInputState
    OutputState = PrepareRepositoryOutputState

    def __init__(
        self,
        template_owner: str = "airas-org",
        template_repo: str = "airas-template",
    ):
        check_api_key(
            github_personal_access_token_check=True,
        )
        self.template_owner = template_owner
        self.template_repo = template_repo

    @prepare_repository_timed
    def _check_repository_from_template(
        self, state: PrepareRepositoryState
    ) -> dict[str, bool]:
        is_repository_from_template = check_repository_from_template(
            github_repository_info=state["github_repository_info"],
            template_owner=self.template_owner,
            template_repo=self.template_repo,
        )
        return {"is_repository_from_template": is_repository_from_template}

    @prepare_repository_timed
    def _create_repository_from_template(
        self, state: PrepareRepositoryState
    ) -> dict[str, Literal[True]]:
        is_repository_from_template = create_repository_from_template(
            github_repository_info=state["github_repository_info"],
            template_owner=self.template_owner,
            template_repo=self.template_repo,
        )
        return {"is_repository_from_template": is_repository_from_template}

    @prepare_repository_timed
    def _check_branch_existence(
        self, state: PrepareRepositoryState
    ) -> dict[str, str | bool]:
        time.sleep(5)
        target_branch_sha = check_branch_existence(
            github_repository_info=state["github_repository_info"],
        )
        return {
            "target_branch_sha": target_branch_sha,
            "is_branch_already_exists": bool(target_branch_sha),
        }

    @prepare_repository_timed
    def _retrieve_main_branch_sha(
        self, state: PrepareRepositoryState
    ) -> dict[str, str]:
        main_branch_sha = retrieve_main_branch_sha(
            github_repository_info=state["github_repository_info"],
        )
        return {"main_branch_sha": main_branch_sha}

    @prepare_repository_timed
    def _create_branch(self, state: PrepareRepositoryState) -> dict[str, bool]:
        is_branch_created = create_branch(
            github_repository_info=state["github_repository_info"],
            sha=state["main_branch_sha"],
        )
        return {"is_branch_created": is_branch_created}

    @prepare_repository_timed
    def _finalize_state(self, state: PrepareRepositoryState) -> dict[str, bool]:
        is_repository_ready = state.get("is_repository_from_template", False)
        is_branch_ready = state.get("is_branch_already_exists", False) or state.get(
            "is_branch_created", False
        )
        return {
            "is_repository_ready": is_repository_ready,
            "is_branch_ready": is_branch_ready,
        }

    def _should_create_from_template(self, state: PrepareRepositoryState) -> str:
        if not state["is_repository_from_template"]:
            return "Create"
        else:
            return "Skip"

    def _should_create_branch(self, state: PrepareRepositoryState) -> str:
        if not state["is_branch_already_exists"]:
            return "Create"
        else:
            return "Skip"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(PrepareRepositoryState)

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
        graph_builder.add_conditional_edges(
            "check_repository_from_template",
            self._should_create_from_template,
            {
                "Create": "create_repository_from_template",
                "Skip": "check_branch_existence",
            },
        )
        graph_builder.add_edge(
            "create_repository_from_template", "check_branch_existence"
        )
        graph_builder.add_conditional_edges(
            "check_branch_existence",
            self._should_create_branch,
            {
                "Create": "retrieve_main_branch_sha",
                "Skip": "finalize_state",
            },
        )
        graph_builder.add_edge("retrieve_main_branch_sha", "create_branch")
        graph_builder.add_edge("create_branch", "finalize_state")
        graph_builder.add_edge("finalize_state", END)
        return graph_builder.compile()


def main():
    parser = argparse.ArgumentParser(description="PrepareRepositorySubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("branch_name", help="Your Branch name")
    args = parser.parse_args()

    github_repository_info = GitHubRepositoryInfo(
        github_owner=args.github_repository.split("/")[0],
        repository_name=args.github_repository.split("/")[1],
        branch_name=args.branch_name,
    )
    state = {
        "github_repository_info": github_repository_info,
    }
    PrepareRepositorySubgraph().run(state)


if __name__ == "__main__":
    import sys

    try:
        main()
    except Exception as e:
        logger.error(f"Error running PrepareRepository: {e}")
        sys.exit(1)
