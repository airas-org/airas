import argparse
import logging
from datetime import datetime
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.github.nodes.github_download import github_download
from airas.core.github.nodes.github_upload import github_upload
from airas.core.github.nodes.merge_history import merge_history
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
gh_upload_timed = lambda f: time_node("github_upload_subgraph")(f)  # noqa: E731


class GithubUploadInputState(TypedDict):
    github_repository: str
    branch_name: str
    subgraph_name: str


class GithubUploadHiddenState(TypedDict): 
    github_owner: str
    repository_name: str
    research_history: dict[str, Any]
    cumulative_output: dict[str, Any]


class GithubUploadOutputState(TypedDict):
    github_upload_success: bool


class GithubUploadSubgraphState(
    GithubUploadInputState,
    GithubUploadHiddenState,
    GithubUploadOutputState,
    ExecutionTimeState,
): ...


class GithubUploadSubgraph:
    def __init__(self):
        check_api_key(llm_api_key_check=True)
        self.research_file_path = ".research/research_history.json"
    
    def _init_state(self, state: GithubUploadSubgraphState) -> dict[str, str]:
        try:
            github_owner, repository_name = state["github_repository"].split("/", 1)
            return {
                "github_owner": github_owner,
                "repository_name": repository_name,
            }
        except ValueError:
            logger.error(f"Invalid github_repository format: {state['github_repository']}")
            raise

    @gh_upload_timed
    def _github_download_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        research_history = github_download(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            file_path=self.research_file_path, 
        )
        return {"research_history": research_history}
    
    @time_node("github_upload_subgraph", "_merge_history_node")
    def _merge_history_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        merged_history = merge_history(
            old=state["research_history"],
            new=state["cumulative_output"], 
            subgraph_name=state["subgraph_name"]
        )
        return {"research_history": merged_history}

    @time_node("github_upload_subgraph", "_github_upload_node")
    def _github_upload_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        commit_message = f"[{state['subgraph_name']}] run at {datetime.now().isoformat()}"

        success = github_upload(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            research_history=state["research_history"],
            file_path=self.research_file_path,
            commit_message=commit_message
        )
        return {"github_upload_success": success}

    def build_graph(self) -> CompiledGraph:
        sg = StateGraph(GithubUploadSubgraphState)
        sg.add_node("init_state", self._init_state)
        sg.add_node("github_download",    self._github_download_node)
        sg.add_node("merge_history",      self._merge_history_node)
        sg.add_node("github_upload",      self._github_upload_node)

        sg.add_edge(START,             "init_state")
        sg.add_edge("init_state",      "github_download")
        sg.add_edge("github_download", "merge_history")
        sg.add_edge("merge_history",   "github_upload")
        sg.add_edge("github_upload",   END)
        return sg.compile()
    
    def run(self, input: dict) -> dict:
        input_keys = GithubUploadInputState.__annotations__.keys()
        state = {k: v for k, v in input.items() if k in input_keys}

        state["cumulative_output"] = {k: v for k, v in input.items() if k not in input_keys}
        result = self.build_graph().invoke(state)
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GithubUploadSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("branch_name", help="Your branch name in your GitHub repository")

    args = parser.parse_args()

    base_queries = "diffusion model"
    subgraph_name = "RetrievePaperFromQuerySubgraph"
    state = {
        "github_repository": args.github_repository,
        "branch_name": args.branch_name, 
        "base_queries": base_queries, 
        "subgraph_name": subgraph_name, 
    }

    GithubUploadSubgraph().run(state)
