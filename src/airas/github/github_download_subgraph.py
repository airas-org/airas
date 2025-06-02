import argparse
import json
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.github.nodes.cleanup_tmp_dir import cleanup_tmp_dir
from airas.github.nodes.download_figures import download_figures
from airas.github.nodes.github_download import github_download
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node

gh_download_timed = lambda f: time_node("github_download_subgraph")(f)  # noqa: E731


class GithubDownloadInputState(TypedDict):
    github_repository: str
    branch_name: str

class GithubDownloadHiddenState(TypedDict):
    github_owner: str
    repository_name: str
    cleanup_tmp: bool


class GithubDownloadOutputState(TypedDict):
    research_history: dict[str, Any]
    figures_dir: str | None


class GithubDownloadSubgraphState(
    GithubDownloadInputState,
    GithubDownloadHiddenState,
    GithubDownloadOutputState,
    ExecutionTimeState,
): ...


class GithubDownloadSubgraph:
    def __init__(
        self,
        use_figures: bool = False, 
        from_remote_dir: str = ".research", 
        to_tmp_dir: str | None = None, 
        research_file_path: str = ".research/research_history.json", 
    ):
        check_api_key(llm_api_key_check=True)
        self.use_figures = use_figures
        self.from_remote_dir = from_remote_dir
        self.to_tmp_dir = to_tmp_dir
        self.research_file_path = research_file_path

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
        
    @gh_download_timed
    def _cleanup_tmp_dir(self, state: GithubDownloadSubgraphState) -> dict[str, bool]:
        cleanup_tmp = cleanup_tmp_dir(
            tmp_dir=self.to_tmp_dir
        )
        return {"cleanup_tmp": cleanup_tmp}

    @gh_download_timed
    def _github_download(self, state: GithubDownloadSubgraphState) -> dict[str, Any]:
        research_history = github_download(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            file_path=self.research_file_path,
        )
        return {
            "research_history": research_history, 
            "figures_dir": None,     
        }

    @gh_download_timed
    def _download_figures(self, state: GithubDownloadSubgraphState) -> dict[str, str]:
        figures_dir = download_figures(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            remote_dir=self.from_remote_dir, 
            save_dir=self.to_tmp_dir,
        )
        return {"figures_dir": figures_dir}

    def build_graph(self) -> CompiledGraph:
        sg = StateGraph(GithubDownloadSubgraphState)
        sg.add_node("init", self._init)
        sg.add_node("github_download", self._github_download)

        if self.use_figures:
            sg.add_node("cleanup_tmp_dir", self._cleanup_tmp_dir)
            sg.add_node("download_figures", self._download_figures)

            sg.add_edge(START, "init")
            sg.add_edge("init", "cleanup_tmp_dir")
            sg.add_edge("cleanup_tmp_dir", "github_download")
            sg.add_edge("github_download", "download_figures")
            sg.add_edge("download_figures", END)
        else:
            sg.add_edge(START, "init")
            sg.add_edge("init", "github_download")
            sg.add_edge("github_download", END)
        return sg.compile()
    
    def run(self, input: dict) -> dict:
        graph = self.build_graph()
        result = graph.invoke(input)
        return result


if __name__ == "__main__":
    from_remote_dir = ".research"
    to_tmp_dir = "/workspaces/airas/tmp"

    parser = argparse.ArgumentParser(
        description="Download GitHub research history and print as JSON."
    )
    parser = argparse.ArgumentParser(description="GithubDownloadSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("branch_name", help="Your branch name in your GitHub repository")

    args = parser.parse_args()

    state = {
        "github_repository":       args.github_repository,
        "branch_name":        args.branch_name,
    }

    result = GithubDownloadSubgraph().run(state)
    # result = GithubDownloadSubgraph(
    #     use_figures=True, 
    #     from_remote_dir=from_remote_dir, 
    #     to_tmp_dir=to_tmp_dir
    # ).run(state)

    print(json.dumps(result, indent=2))