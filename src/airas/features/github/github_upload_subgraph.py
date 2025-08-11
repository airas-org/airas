import argparse
import logging
from datetime import datetime
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.github.nodes.github_download import github_download
from airas.features.github.nodes.github_upload import github_upload
from airas.features.github.nodes.merge_history import merge_history
from airas.types.github import GitHubRepositoryInfo
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
gh_upload_timed = lambda f: time_node("github_upload_subgraph")(f)  # noqa: E731


class GithubUploadInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo
    subgraph_name: str


class GithubUploadHiddenState(TypedDict):
    research_history: dict[str, Any]
    cumulative_output: dict[str, Any]


class GithubUploadOutputState(TypedDict):
    github_upload_success: bool


class GithubUploadSubgraphState(
    GithubUploadInputState,
    GithubUploadHiddenState,
    GithubUploadOutputState,
    ExecutionTimeState,
):
    pass


class GithubUploadSubgraph(BaseSubgraph):
    InputState = GithubUploadInputState
    OutputState = GithubUploadOutputState

    def __init__(self):
        check_api_key(
            github_personal_access_token_check=True,
        )
        self.research_file_path = ".research/research_history.json"

    @gh_upload_timed
    def _github_download_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        research_history = github_download(
            github_repository_info=state["github_repository_info"],
            file_path=self.research_file_path,
        )
        return {"research_history": research_history}

    @time_node("github_upload_subgraph", "_merge_history_node")
    def _merge_history_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        merged_history = merge_history(
            old=state["research_history"],
            new=state["cumulative_output"],
        )
        return {"research_history": merged_history}

    @time_node("github_upload_subgraph", "_github_upload_node")
    def _github_upload_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        commit_message = (
            f"[subgraph: {state['subgraph_name']}] run at {datetime.now().isoformat()}"
        )

        is_github_upload_success = github_upload(
            github_repository_info=state["github_repository_info"],
            research_history=state["research_history"],
            file_path=self.research_file_path,
            commit_message=commit_message,
        )
        return {"github_upload_success": is_github_upload_success}

    def build_graph(self) -> CompiledGraph:
        sg = StateGraph(GithubUploadSubgraphState)
        sg.add_node("github_download", self._github_download_node)
        sg.add_node("merge_history", self._merge_history_node)
        sg.add_node("github_upload", self._github_upload_node)

        sg.add_edge(START, "github_download")
        sg.add_edge("github_download", "merge_history")
        sg.add_edge("merge_history", "github_upload")
        sg.add_edge("github_upload", END)
        return sg.compile()

    def run(self, state: dict[str, Any], config: dict | None = None) -> dict[str, Any]:
        input_state_keys = self.InputState.__annotations__.keys()
        output_state_keys = self.OutputState.__annotations__.keys()

        input_state = {k: state[k] for k in input_state_keys if k in state}

        # Use the entire state (except subgraph metadata and github_repository_info) as cumulative_output
        def serialize_for_json(obj):
            if hasattr(obj, "model_dump"):
                return obj.model_dump()
            elif isinstance(obj, list):
                return [serialize_for_json(item) for item in obj]
            elif isinstance(obj, dict):
                return {key: serialize_for_json(value) for key, value in obj.items()}
            else:
                return obj

        cumulative_output = {}
        for k, v in state.items():
            if k in ["subgraph_name", "github_repository_info"]:
                continue
            cumulative_output[k] = serialize_for_json(v)
        input_state["cumulative_output"] = cumulative_output

        config = config or {"recursion_limit": 200}
        result = self.build_graph().invoke(input_state, config=config)
        output_state = {k: result[k] for k in output_state_keys if k in result}

        cleaned_state = {k: v for k, v in state.items() if k != "subgraph_name"}
        return {
            "subgraph_name": self.__class__.__name__,
            **cleaned_state,
            **output_state,
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GithubUploadSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )

    args = parser.parse_args()

    queries = ["diffusion model"]
    subgraph_name = "RetrievePaperFromQuerySubgraph"
    github_repository_info = GitHubRepositoryInfo(
        github_owner=args.github_repository.split("/")[0],
        repository_name=args.github_repository.split("/")[1],
        branch_name=args.branch_name,
    )
    state = {
        "github_repository_info": github_repository_info,
        "subgraph_name": subgraph_name,
    }

    GithubUploadSubgraph().run(state)
