import argparse
import json
import logging
import time
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.preparation.prepare_repository_subgraph.nodes.check_branch_existence import (
    check_branch_existence,
)
from airas.preparation.prepare_repository_subgraph.nodes.check_github_repository import (
    check_github_repository,
)
from airas.preparation.prepare_repository_subgraph.nodes.create_branch import (
    create_branch,
)
from airas.preparation.prepare_repository_subgraph.nodes.create_repository_from_template import (
    create_repository_from_template,
)
from airas.preparation.prepare_repository_subgraph.nodes.is_repository_created_from_template import (
    is_repository_created_from_template,
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
    repository_exists: bool
    template_result: bool
    target_branch_sha: str
    create_result: bool
    main_sha: str


class PrepareRepositoryState(
    ExecutionTimeState,
    PrepareRepositoryInputState,
    PrepareRepositoryHiddenState,
):
    pass


class PrepareRepository:
    def __init__(
        self,
        template_owner: str = "airas-org",
        template_repo: str = "airas-template",
    ):
        self.template_owner = template_owner
        self.template_repo = template_repo
        check_api_key(
            github_personal_access_token_check=True,
        )

    def _init(self, state: PrepareRepositoryState) -> dict:
        github_repository = state["github_repository"]
        if "/" in github_repository:
            github_owner, repository_name = github_repository.split("/", 1)
            return {
                "github_owner": github_owner,
                "repository_name": repository_name,
            }
        else:
            raise ValueError("Invalid repository name format.")

    @prepare_repository_timed
    def _check_github_repository(self, state: PrepareRepositoryState) -> dict[str, bool]:
        repository_exists = check_github_repository(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
        )
        return {"repository_exists": repository_exists}

    @prepare_repository_timed
    def _create_repository_from_template(self, state: PrepareRepositoryState) -> dict[str, bool]:
        template_result = create_repository_from_template(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            template_owner=self.template_owner,
            template_repo=self.template_repo,
        )
        return {"template_result": template_result}
    
    @prepare_repository_timed
    def _is_repository_created_from_template(self, state: PrepareRepositoryState) -> dict[str, Literal[True]]:
        template_result = is_repository_created_from_template(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            template_owner=self.template_owner,
            template_repo=self.template_repo,
        )
        if not template_result:
            raise RuntimeError(
                f"The repository `{state['github_owner']}/{state['repository_name']}` already exists "
                f"but was not created from the specified template `{self.template_owner}/{self.template_repo}`."
            )
        return {"template_result": template_result}

    @prepare_repository_timed
    def _check_branch_existence(self, state: PrepareRepositoryState) -> dict:
        time.sleep(5)
        target_branch_sha = check_branch_existence(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
        )
        return {"target_branch_sha": target_branch_sha}

    @prepare_repository_timed
    def _retrieve_main_branch_sha(self, state: PrepareRepositoryState) -> dict:
        main_sha = retrieve_main_branch_sha(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
        )
        return {"main_sha": main_sha}

    @prepare_repository_timed
    def _create_branch(self, state: PrepareRepositoryState) -> dict:
        create_result = create_branch(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            main_sha=state["main_sha"],
        )
        return {"create_result": create_result}

    def _should_create_from_template(self, state: PrepareRepositoryState) -> str:
        if not state["repository_exists"]:
            return "create_repository_from_template"
        else:
            return "is_repository_created_from_template"

    def _should_create_branch(self, state: PrepareRepositoryState) -> str:
        if not state["target_branch_sha"]:
            return "retrieve_main_branch_sha"
        else:
            return "end"

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(PrepareRepositoryState)
        # make nodes
        graph_builder.add_node("init", self._init)
        graph_builder.add_node("check_github_repository", self._check_github_repository)
        graph_builder.add_node("create_repository_from_template", self._create_repository_from_template)
        graph_builder.add_node("is_repository_created_from_template", self._is_repository_created_from_template)
        graph_builder.add_node("check_branch_existence", self._check_branch_existence)
        graph_builder.add_node("retrieve_main_branch_sha", self._retrieve_main_branch_sha)
        graph_builder.add_node("create_branch", self._create_branch)

        # make edges
        graph_builder.add_edge(START, "init")
        graph_builder.add_edge("init", "check_github_repository")
        graph_builder.add_conditional_edges(
            "check_github_repository",
            self._should_create_from_template,
            {
                "create_repository_from_template": "create_repository_from_template",
                "is_repository_created_from_template": "is_repository_created_from_template",
            },
        )
        graph_builder.add_edge("create_repository_from_template", "check_branch_existence")
        graph_builder.add_edge("is_repository_created_from_template", "check_branch_existence")
        graph_builder.add_conditional_edges(
            "check_branch_existence",
            self._should_create_branch,
            {
                "retrieve_main_branch_sha": "retrieve_main_branch_sha",
                "end": END,
            },
        )
        graph_builder.add_edge("retrieve_main_branch_sha", "create_branch")
        graph_builder.add_edge("create_branch", END)

        return graph_builder.compile()

    def run(self, input: dict) -> dict:
        graph = self.build_graph()
        result = graph.invoke(input)
        return result


def main():
    parser = argparse.ArgumentParser(
        description="Execute PreparaRepository"
    )
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("branch_name", help="Your branch name in your GitHub repository")

    args = parser.parse_args()

    subgraph = PrepareRepository()

    input = {
        "github_repository": args.github_repository,
        "branch_name":     args.branch_name,
    }

    result = subgraph.run(input)
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    import sys
    try:
        main()
    except Exception as e:
        logger.error(
            f"Error running PrepareRepository: {e}"
        )
        sys.exit(1)
