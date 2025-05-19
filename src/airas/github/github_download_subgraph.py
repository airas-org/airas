import argparse
import json
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.github.nodes.github_download import github_download
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node


class GithubDownloadInputState(TypedDict):
    github_repository: str
    branch_name: str
    research_file_path: str | None

class GithubDownloadHiddenState(TypedDict):
    github_owner: str
    repository_name: str

class GithubDownloadOutputState(TypedDict):
    research_history: dict[str, Any]


class GithubDownloadSubgraphState(
    GithubDownloadInputState,
    GithubDownloadHiddenState,
    GithubDownloadOutputState,
    ExecutionTimeState,
): ...


class GithubDownloadSubgraph:
    def __init__(
        self,
    ):
        check_api_key(llm_api_key_check=True)

    def _init(self, state: GithubDownloadSubgraphState) -> dict[str, Any]:
        github_repository = state["github_repository"]
        if "/" in github_repository:
            github_owner, repository_name = github_repository.split("/", 1)
            return {
                "github_owner": github_owner,
                "repository_name": repository_name,
            }
        else:
            raise ValueError("Invalid repository name format.")

    @time_node("github_download_subgraph", "_github_download_node")
    def _github_download_node(self, state: GithubDownloadSubgraphState) -> dict[str, Any]:
        research_history = github_download(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            file_path=state.get("research_file_path") or ".research/research_history.json",
        )
        return {"research_history": research_history}

    def build_graph(self) -> CompiledGraph:
        sg = StateGraph(GithubDownloadSubgraphState)
        sg.add_node("init", self._init)
        sg.add_node("github_download", self._github_download_node)

        sg.add_edge(START, "init")
        sg.add_edge("init", "github_download")
        sg.add_edge("github_download", END)
        return sg.compile()
    
    def run(self, input: dict) -> dict:
        graph = self.build_graph()
        result = graph.invoke(input)
        return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Download GitHub research history and print as JSON."
    )
    parser = argparse.ArgumentParser(description="GithubDownloadSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("branch_name", help="Your branch name in your GitHub repository")
    parser.add_argument(
        "--research_file_path", 
        help="Your branch name in your GitHub repository", 
        default=".research/research_history.json"
    )
    args = parser.parse_args()

    subgraph = GithubDownloadSubgraph()

    initial_state = {
        "github_repository":       args.github_repository,
        "branch_name":        args.branch_name,
        "research_file_path": args.research_file_path,
    }

    result = subgraph.run(initial_state)
    print(json.dumps(result, indent=2))
