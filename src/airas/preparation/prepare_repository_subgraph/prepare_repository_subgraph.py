import argparse
import logging
import time
from typing import Any, Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.preparation.prepare_repository_subgraph.nodes.check_branch_existence import (
    check_branch_existence,
)
from airas.preparation.prepare_repository_subgraph.nodes.check_repository_from_template import (
    check_repository_from_template,
)
from airas.preparation.prepare_repository_subgraph.nodes.create_branch import (
    create_branch,
)
from airas.preparation.prepare_repository_subgraph.nodes.create_repository_from_template import (
    create_repository_from_template,
)
from airas.preparation.prepare_repository_subgraph.nodes.retrieve_main_branch_sha import (
    retrieve_main_branch_sha,
)
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

prepare_repository_timed = lambda f: time_node("prepare_repository")(f)  # noqa: E731


class PrepareRepositoryInputState(TypedDict):
    github_repository: str
    branch_name: str

class PrepareRepositoryHiddenState(TypedDict):
    github_owner: str
    repository_name: str
    target_branch_sha: str
    main_sha: str
    repository_from_template: bool
    branch_already_exists: bool
    branch_created: bool

class PrepareRepositoryOutputState(TypedDict):
    repository_status: bool
    branch_status: bool


class PrepareRepositoryState(
    PrepareRepositoryInputState,
    PrepareRepositoryHiddenState,
    PrepareRepositoryOutputState, 
    ExecutionTimeState,
):
    pass


class PrepareRepository:
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

    def _init(self, state: PrepareRepositoryState) -> dict[str, str]:
        try:
            github_owner, repository_name = state["github_repository"].split("/", 1)
            return {
                "github_owner": github_owner,
                "repository_name": repository_name,
            }
        except ValueError:
            logger.error(f"Invalid github_repository format: {state['github_repository']}")
            raise
        
    @prepare_repository_timed
    def _check_repository_from_template(self, state: PrepareRepositoryState) -> dict[str, Literal[True]]:
        repository_from_template = check_repository_from_template(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            template_owner=self.template_owner,
            template_repo=self.template_repo,
        )
        return {"repository_from_template": repository_from_template}

    @prepare_repository_timed
    def _create_repository_from_template(self, state: PrepareRepositoryState) -> dict[str, bool]:
        repository_from_template = create_repository_from_template(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            template_owner=self.template_owner,
            template_repo=self.template_repo,
        )
        return {"repository_from_template": repository_from_template}
    
    @prepare_repository_timed
    def _check_branch_existence(self, state: PrepareRepositoryState) -> dict[str, str | bool]:
        time.sleep(5)
        target_branch_sha = check_branch_existence(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
        )
        return {
            "target_branch_sha": target_branch_sha, 
            "branch_already_exists": bool(target_branch_sha), 
        }

    @prepare_repository_timed
    def _retrieve_main_branch_sha(self, state: PrepareRepositoryState) -> dict[str, str]:
        main_sha = retrieve_main_branch_sha(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
        )
        return {"main_sha": main_sha}

    @prepare_repository_timed
    def _create_branch(self, state: PrepareRepositoryState) -> dict[str, bool]:
        branch_created = create_branch(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            main_sha=state["main_sha"],
        )
        return {"branch_created": branch_created}
    
    @prepare_repository_timed
    def _finalize_state(self, state: PrepareRepositoryState) -> dict[str, bool]:
        repository_status = state.get("repository_from_template", False)
        branch_status = state.get("branch_already_exists", False) or state.get("branch_created", False)
        return {
            "repository_status": repository_status,
            "branch_status": branch_status,
        }

    def _should_create_from_template(self, state: PrepareRepositoryState) -> str:
        if not state["repository_from_template"]:
            return "Create"
        else:
            return "Skip"

    def _should_create_branch(self, state: PrepareRepositoryState) -> str:
        if not state["branch_already_exists"]:
            return "Create"
        else:
            return "Skip"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(PrepareRepositoryState)

        graph_builder.add_node("init", self._init)
        graph_builder.add_node("check_repository_from_template", self._check_repository_from_template)
        graph_builder.add_node("create_repository_from_template", self._create_repository_from_template)
        graph_builder.add_node("check_branch_existence", self._check_branch_existence)
        graph_builder.add_node("retrieve_main_branch_sha", self._retrieve_main_branch_sha)
        graph_builder.add_node("create_branch", self._create_branch)
        graph_builder.add_node("finalize_state", self._finalize_state)

        graph_builder.add_edge(START, "init")
        graph_builder.add_edge("init", "check_repository_from_template")
        graph_builder.add_conditional_edges(
            "check_repository_from_template",
            self._should_create_from_template,
            {
                "Create": "create_repository_from_template",
                "Skip": "check_branch_existence",
            },
        )
        graph_builder.add_edge("create_repository_from_template", "check_branch_existence")
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

    def run(self, input: dict[str, Any], config: dict | None = None) -> PrepareRepositoryOutputState:
        result = self.build_graph().invoke(input, config=config or {})

        output_keys = PrepareRepositoryOutputState.__annotations__.keys()
        output = {k: result[k] for k in output_keys if k in result}
        return output


def main():
    parser = argparse.ArgumentParser(
        description="PreparaRepository"
    )
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("branch_name", help="Your branch name in your GitHub repository")

    args = parser.parse_args()

    state = {
        "github_repository": args.github_repository,
        "branch_name": args.branch_name
    }
    PrepareRepository().run(state)

if __name__ == "__main__":
    import sys
    try:
        main()
    except Exception as e:
        logger.error(
            f"Error running PrepareRepository: {e}"
        )
        sys.exit(1)
