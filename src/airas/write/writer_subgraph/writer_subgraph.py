import argparse
import json
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging
from airas.write.writer_subgraph.input_data import (
    writer_subgraph_input_data,
)
from airas.write.writer_subgraph.nodes.cleanup_tmp_dir import cleanup_tmp_dir
from airas.write.writer_subgraph.nodes.fetch_figures_from_repository import (
    fetch_figures_from_repository,
)
from airas.write.writer_subgraph.nodes.generate_note import generate_note
from airas.write.writer_subgraph.nodes.paper_writing import WritingNode

setup_logging()
logger = logging.getLogger(__name__)
writer_timed = lambda f: time_node("writer_subgraph")(f)  # noqa: E731

class WriterSubgraphInputState(TypedDict):
    github_repository: str
    branch_name: str

    base_method_text: str
    new_method: str
    verification_policy: str
    experiment_details: str
    experiment_code: str
    output_text_data: str
    analysis_report: str


class WriterSubgraphHiddenState(TypedDict):
    github_owner: str
    repository_name: str
    figures_dir: str | None
    cleanup_tmp: bool
    note: str


class WriterSubgraphOutputState(TypedDict):
    paper_content: dict[str, str]


class WriterSubgraphState(
    WriterSubgraphInputState,
    WriterSubgraphHiddenState,
    WriterSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class WriterSubgraph:
    def __init__(
        self,
        llm_name: str,
        tmp_dir: str,
        refine_round: int = 2,
    ):
        # NOTE: tmp_dir is a temporary directory used during execution and will be cleaned up at the end.
        self.llm_name = llm_name
        self.tmp_dir = tmp_dir
        self.refine_round = refine_round
        check_api_key(llm_api_key_check=True)

    def _init(self, state: WriterSubgraphState) -> dict[str, str]:
        github_repository = state["github_repository"]
        if "/" in github_repository:
            github_owner, repository_name = github_repository.split("/", 1)
            return {
                "github_owner": github_owner,
                "repository_name": repository_name,
            }
        else:
            raise ValueError("Invalid repository name format.")

    @writer_timed
    def _prepare_figures(self, state: WriterSubgraphState) -> dict[str, str | None]:
        logger.info("---WriterSubgraph---")
        figures_dir = fetch_figures_from_repository(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"],
            branch_name=state["branch_name"],
            tmp_dir=self.tmp_dir,
        )
        return {"figures_dir": figures_dir}

    @writer_timed
    def _generate_note_node(self, state: WriterSubgraphState) -> dict:
        note = generate_note(state=dict(state), figures_dir=state["figures_dir"])
        return {"note": note}

    @writer_timed
    def _writeup_node(self, state: WriterSubgraphState) -> dict:
        paper_content = WritingNode(
            llm_name=self.llm_name,
            refine_round=self.refine_round,
        ).execute(
            note=state["note"],
        )
        return {"paper_content": paper_content}
    
    @writer_timed
    def _cleanup_tmp_dir(self, state: WriterSubgraphState) -> dict[str, bool]:
        cleanup_tmp = cleanup_tmp_dir(
            tmp_dir=self.tmp_dir
        )
        return {"cleanup_tmp": cleanup_tmp}


    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(WriterSubgraphState)
        # make nodes
        graph_builder.add_node("init", self._init)
        graph_builder.add_node("prepare_figures", self._prepare_figures)
        graph_builder.add_node("generate_note_node", self._generate_note_node)
        graph_builder.add_node("writeup_node", self._writeup_node)
        graph_builder.add_node("cleanup_tmp_dir", self._cleanup_tmp_dir)
        # make edges
        graph_builder.add_edge(START, "init")
        graph_builder.add_edge("init", "prepare_figures")
        graph_builder.add_edge("prepare_figures", "generate_note_node")
        graph_builder.add_edge("generate_note_node", "writeup_node")
        graph_builder.add_edge("writeup_node", "cleanup_tmp_dir")
        graph_builder.add_edge("cleanup_tmp_dir", END)

        return graph_builder.compile()


def main():
    llm_name = "o3-mini-2025-01-31"
    tmp_dir = "/workspaces/airas/tmp"
    refine_round = 1

    parser = argparse.ArgumentParser(
        description="WriterSubgraph"
    )
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    writer_subgraph = WriterSubgraph(
        llm_name=llm_name, 
        tmp_dir=tmp_dir, 
        refine_round=refine_round, 
    ).build_graph()
    result = writer_subgraph.invoke({
        **writer_subgraph_input_data, 
        "github_repository": args.github_repository, 
        "branch_name": args.branch_name, 
    })
    print(f"result: {json.dumps(result, indent=2)}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running WriterSubgraph: {e}")
        raise
