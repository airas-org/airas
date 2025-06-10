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
    ...

class GithubDownloadHiddenState(TypedDict):
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
        github_repository: str, 
        branch_name: str, 
        use_figures: bool = False, 
        remote_dir: str = ".research", 
        tmp_dir: str | None = None,     # NOTE: This directory is cleaned up at the beginning of each execution
    ):
        check_api_key(llm_api_key_check=True)
        self.github_repository = github_repository
        self.branch_name = branch_name
        self.use_figures = use_figures
        self.remote_dir = remote_dir
        self.tmp_dir = tmp_dir
        self.research_file_path = ".research/research_history.json"

        if "/" in self.github_repository:
            self.github_owner, self.repository_name = self.github_repository.split("/", 1)
        else:
            raise ValueError("Invalid repository name format.")
        
    @gh_download_timed
    def _cleanup_tmp_dir(self, state: GithubDownloadSubgraphState) -> dict[str, bool]:
        cleanup_tmp = cleanup_tmp_dir(
            tmp_dir=self.tmp_dir
        )
        return {"cleanup_tmp": cleanup_tmp}

    @gh_download_timed
    def _github_download(self, state: GithubDownloadSubgraphState) -> dict[str, Any]:
        research_history = github_download(
            github_owner=self.github_owner,
            repository_name=self.repository_name,
            branch_name=self.branch_name,
        )
        return {
            "research_history": research_history, 
            "figures_dir": None,     
        }

    @gh_download_timed
    def _download_figures(self, state: GithubDownloadSubgraphState) -> dict[str, str]:
        figures_dir = download_figures(
            github_owner=self.github_owner,
            repository_name=self.repository_name,
            branch_name=self.branch_name,
            remote_dir=self.remote_dir, 
            save_dir=self.tmp_dir,
        )
        return {"figures_dir": figures_dir}

    def build_graph(self) -> CompiledGraph:
        sg = StateGraph(GithubDownloadSubgraphState)
        sg.add_node("github_download", self._github_download)

        if self.use_figures:
            sg.add_node("cleanup_tmp_dir", self._cleanup_tmp_dir)
            sg.add_node("download_figures", self._download_figures)

            sg.add_edge(START, "cleanup_tmp_dir")
            sg.add_edge("cleanup_tmp_dir", "github_download")
            sg.add_edge("github_download", "download_figures")
            sg.add_edge("download_figures", END)
        else:
            sg.add_edge(START, "github_download")
            sg.add_edge("github_download", END)
        return sg.compile()
    
    def run(self, config: dict | None = None) -> dict:
        graph = self.build_graph()

        init_state: dict[str, Any] = {"research_history": {}}
        result = graph.invoke(init_state, config=config or {})

        output_keys = GithubDownloadOutputState.__annotations__.keys()
        output = {k: result[k] for k in output_keys if k in result and k != "research_history"}
        research_history = result.get("research_history", {})
        
        merged = {}
        order = research_history.get("_order", [])
        for key in order:
            value = research_history.get(key)
            merged.update(value)

        return {
            **merged,
            **output,
        }


if __name__ == "__main__":
    remote_dir = ".research"
    tmp_dir = "/workspaces/airas/tmp"

    parser = argparse.ArgumentParser(
        description="Download GitHub research history and print as JSON."
    )
    parser = argparse.ArgumentParser(description="GithubDownloadSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("branch_name", help="Your branch name in your GitHub repository")

    args = parser.parse_args()

    result = GithubDownloadSubgraph(
        github_repository=args.github_repository, 
        branch_name=args.branch_name, 
    ).run()
    # result = GithubDownloadSubgraph(
    #     use_figures=True, 
    #     remote_dir=remote_dir, 
    #     tmp_dir=tmp_dir
    # ).run(state)

    print(json.dumps(result, indent=2))