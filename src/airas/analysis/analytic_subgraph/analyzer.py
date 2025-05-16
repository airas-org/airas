import argparse
import json
import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph

from airas.analysis.analytic_subgraph.analytic_subgraph import (
    AnalyticSubgraph,
    AnalyticSubgraphInputState,
    AnalyticSubgraphOutputState,
)
from airas.github.github_download_subgraph import (
    GithubDownloadSubgraph,
    GithubDownloadSubgraphState,
)
from airas.github.github_upload_subgraph import (
    GithubUploadSubgraph,
    GithubUploadSubgraphState,
)
from airas.utils.api_client.llm_facade_client import LLM_MODEL
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class AnalyzerState(
    GithubDownloadSubgraphState,
    GithubUploadSubgraphState, 
    ExecutionTimeState,
):
    research_history: AnalyticSubgraphInputState
    new_output: AnalyticSubgraphOutputState


class Analyzer:
    def __init__(
        self,
        llm_name: LLM_MODEL,
        download_subgraph: GithubDownloadSubgraph | None = None,
        analytic_subgraph: AnalyticSubgraph | None = None,
        upload_subgraph:   GithubUploadSubgraph | None = None,
    ) -> None:
        check_api_key(
            llm_api_key_check=True,
            devin_api_key_check=True,
            github_personal_access_token_check=True,
        )
        self.llm_name = llm_name

        download_subgraph = download_subgraph or GithubDownloadSubgraph()
        analytic_subgraph = analytic_subgraph or AnalyticSubgraph(
            llm_name=self.llm_name,
        )
        
        self.subgraph_name = analytic_subgraph.__class__.__name__
        upload_subgraph = upload_subgraph or GithubUploadSubgraph(
            subgraph_name=self.subgraph_name,
        )

        
        self.download_subgraph = download_subgraph.build_graph()
        self.analytic_subgraph = analytic_subgraph.build_graph()
        self.upload_subgraph = upload_subgraph.build_graph()


    @time_node("analyzer", "_github_download")
    def _github_download(self, state: AnalyzerState) -> dict[str, Any]:
        result = self.download_subgraph.invoke(
            {
                "github_owner": state["github_owner"],
                "repository_name": state["repository_name"],
                "branch_name": state["branch_name"],
                "research_file_path": state["research_file_path"],
            }
        )
        return {
            "research_history": result["research_history"]
        }

    @time_node("analyzer", "_analytic_subgraph")
    def _analytic_subgraph(self, state: AnalyzerState) -> dict[str, Any]:
        research_history = {
            k: state["research_history"][k] 
            for k in AnalyticSubgraphInputState.__annotations__.keys()
        }
        
        result = self.analytic_subgraph.invoke(research_history)
        new_output = {
            k: result[k] 
            for k in AnalyticSubgraphOutputState.__annotations__.keys()
        }
        return {
            "research_history": research_history, 
            "new_output": new_output, 
        }

    @time_node("analyzer", "_github_upload")
    def _github_upload(self, state: AnalyzerState) -> dict[str, Any]:
        result = self.upload_subgraph.invoke(
            {
                "github_owner": state["github_owner"],
                "repository_name": state["repository_name"],
                "branch_name": state["branch_name"],
                "research_file_path": state["research_file_path"],
                "new_output": state["new_output"],
                "extra_files": state.get("extra_files"),
            }
        )
        return {
            "github_upload_success": result["github_upload_success"]
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(AnalyzerState)
        graph_builder.add_node("github_download", self._github_download)
        graph_builder.add_node("analytic_subgraph", self._analytic_subgraph)
        graph_builder.add_node("github_upload", self._github_upload)

        graph_builder.add_edge(START, "github_download")
        graph_builder.add_edge("github_download", "analytic_subgraph")
        graph_builder.add_edge("analytic_subgraph", "github_upload")
        graph_builder.add_edge("github_upload", END)

        return graph_builder.compile()


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Analyzer")
   
    parser.add_argument("github_owner", help="Your GitHub Owner")
    parser.add_argument("repository_name", help="Your repository name")
    parser.add_argument("branch_name", help="Your branch name in your GitHub repository")
    parser.add_argument(
        "--research_file_path",
        default=".research/research_history.json",
        help="Path to research_history.json inside the repo",
    )

    parser.add_argument("--llm_name", default="o3-mini-2025-01-31")

    args = parser.parse_args()

    analyzer = Analyzer(
        llm_name=args.llm_name,
    )
    compiled = analyzer.build_graph()

    initial_state = {
        "github_owner": args.github_owner,
        "repository_name": args.repository_name,
        "branch_name": args.branch_name,
        "research_file_path": args.research_file_path,
    }

    result = compiled.invoke(initial_state)
    print(json.dumps(result, indent=2, ensure_ascii=False))