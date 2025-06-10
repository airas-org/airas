import argparse
from datetime import datetime
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.github.nodes.github_download import github_download
from airas.github.nodes.github_upload import github_upload
from airas.github.nodes.merge_history import merge_history
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node

gh_upload_timed = lambda f: time_node("github_upload_subgraph")(f)  # noqa: E731


class GithubUploadInputState(TypedDict):
    github_repository: str
    branch_name: str
    subgraph_name: str


class GithubUploadHiddenState(TypedDict): 
    github_owner: str
    repository_name: str
    research_history: dict[str, Any]
    new_output: dict[str, Any]


class GithubUploadOutputState(TypedDict):
    github_upload_success: bool


class GithubUploadSubgraphState(
    GithubUploadInputState,
    GithubUploadHiddenState,
    GithubUploadOutputState,
    ExecutionTimeState,
): ...


class GithubUploadSubgraph:
    def __init__(
        self, 
        github_repository: str, 
        branch_name: str, 
    ):
        check_api_key(llm_api_key_check=True)
        self.github_repository = github_repository
        self.branch_name = branch_name
        self.research_file_path = ".research/research_history.json"
    
        if "/" in self.github_repository:
            self.github_owner, self.repository_name = self.github_repository.split("/", 1)
        else:
            raise ValueError("Invalid repository name format.")

    @gh_upload_timed
    def _github_download_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        research_history = github_download(
            github_owner=self.github_owner,
            repository_name=self.repository_name,
            branch_name=self.branch_name,
            file_path=self.research_file_path, 
        )
        return {"research_history": research_history}
    
    @time_node("github_upload_subgraph", "_merge_history_node")
    def _merge_history_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        merged_history = merge_history(
            old=state["research_history"],
            new=state["new_output"], 
            subgraph_name=state["subgraph_name"]
        )
        return {"research_history": merged_history}

    @time_node("github_upload_subgraph", "_github_upload_node")
    def _github_upload_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        commit_message = f"[{state['subgraph_name']}] run at {datetime.now().isoformat()}"

        success = github_upload(
            github_owner=self.github_owner,
            repository_name=self.repository_name,
            branch_name=self.branch_name,
            research_history=state["research_history"],
            file_path=self.research_file_path,
            commit_message=commit_message
        )
        return {"github_upload_success": success}

    def build_graph(self) -> CompiledGraph:
        sg = StateGraph(GithubUploadSubgraphState)
        sg.add_node("github_download",    self._github_download_node)
        sg.add_node("merge_history",      self._merge_history_node)
        sg.add_node("github_upload",      self._github_upload_node)

        sg.add_edge(START,             "github_download")
        sg.add_edge("github_download", "merge_history")
        sg.add_edge("merge_history",   "github_upload")
        sg.add_edge("github_upload",   END)
        return sg.compile()
    
    def run(self, input: dict) -> dict:
        input_keys = GithubUploadInputState.__annotations__.keys()
        state = {k: v for k, v in input.items() if k in input_keys}

        state["new_output"] = {k: v for k, v in input.items() if k not in input_keys}
        result = self.build_graph().invoke(state)
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GithubUploadSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("branch_name", help="Your branch name in your GitHub repository")

    args = parser.parse_args()

    base_queries = {"vision": {"test": "nest"}}
    subgraph_name = "retrieve_related_paper"
    state = {
        "add_queries": base_queries, 
        "subgraph_name": subgraph_name, 
    }

    GithubUploadSubgraph(
        github_repository=args.github_repository, 
        branch_name=args.branch_name, 
    ).run(state)