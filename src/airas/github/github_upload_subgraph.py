import argparse
import json
from datetime import datetime
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.github.nodes.github_download import github_download
from airas.github.nodes.github_upload import ExtraFileConfig, github_upload
from airas.github.nodes.merge_history import merge_history
from airas.github.nodes.prepare_branch import prepare_branch
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node


class GithubUploadInputState(TypedDict):
    github_repository: str
    branch_name: str


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
        subgraph_name: str, 
        create_branch: bool = True, 
        research_file_path: str = ".research/research_history.json", 
        extra_files: list[ExtraFileConfig] | None = None,    
    ):
        check_api_key(llm_api_key_check=True)
        self.subgraph_name = subgraph_name
        self.create_branch = create_branch
        self.research_file_path = research_file_path
        self.extra_files = extra_files

    def _init(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        github_repository = state["github_repository"]
        if "/" in github_repository:
            github_owner, repository_name = github_repository.split("/", 1)
            return {
                "github_owner": github_owner,
                "repository_name": repository_name,
                "subgraph_name": self.subgraph_name,
                "create_branch": self.create_branch,
            }
        else:
            raise ValueError("Invalid repository name format.")

    @time_node("github_upload_subgraph", "_github_download_node")
    def _github_download_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        research_history = github_download(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            file_path=self.research_file_path, 
        )
        return {"research_history": research_history}
    
    @time_node("github_upload_subgraph", "_prepare_branch_node")
    def _prepare_branch_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        new_branch = prepare_branch(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            subgraph_name=self.subgraph_name, 
        )
        return {"branch_name": new_branch}

    @time_node("github_upload_subgraph", "_merge_history_node")
    def _merge_history_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        merged_history = merge_history(
            old=state["research_history"],
            new=state["new_output"], 
        )
        return {"research_history": merged_history}

    @time_node("github_upload_subgraph", "_github_upload_node")
    def _github_upload_node(self, state: GithubUploadSubgraphState) -> dict[str, Any]:
        commit_message = f"[{self.subgraph_name}] run at {datetime.now().isoformat()}"

        success = github_upload(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            research_history=state["research_history"],
            extra_files=self.extra_files,
            file_path=self.research_file_path,
            commit_message=commit_message
        )
        return {"github_upload_success": success}

    def build_graph(self) -> CompiledGraph:
        sg = StateGraph(GithubUploadSubgraphState)
        sg.add_node("init",               self._init)
        sg.add_node("github_download",    self._github_download_node)
        sg.add_node("prepare_branch",     self._prepare_branch_node)
        sg.add_node("merge_history",      self._merge_history_node)
        sg.add_node("github_upload",      self._github_upload_node)

        sg.add_edge(START,             "init")
        sg.add_edge("init",            "github_download")
        sg.add_conditional_edges(
            "github_download",
            lambda st: "prepare_branch" if self.create_branch else "merge_history",
            {
                "prepare_branch": "prepare_branch", 
                "merge_history": "merge_history"
            },
        )
        sg.add_edge("prepare_branch",  "merge_history")
        sg.add_edge("merge_history",   "github_upload")
        sg.add_edge("github_upload",   END)
        return sg.compile()
    
    def run(self, input: dict) -> dict:
        graph = self.build_graph()

        input_keys = GithubUploadInputState.__annotations__.keys()
        state = {k: v for k, v in input.items() if k in input_keys}
        state["new_output"] = {k: v for k, v in input.items() if k not in input_keys}
        result = graph.invoke(state)
        
        new_output = result.get("new_output", {})
        return {
            **new_output, 
            "github_repository": result["github_repository"],
            "branch_name":       result["branch_name"]
        }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload GitHub research history and print as JSON."
    )
    parser = argparse.ArgumentParser(description="GithubUploadSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("branch_name", help="Your branch name in your GitHub repository")

    args = parser.parse_args()

    base_queries = "llm"
    state = {
        "github_repository": args.github_repository, 
        "branch_name": args.branch_name,
        "base_queries": base_queries, 
    }

    result = GithubUploadSubgraph(
        subgraph_name="retrieve_paper_from_query",
        create_branch=True,
    ).run(state)
    print(json.dumps(result, indent=2))