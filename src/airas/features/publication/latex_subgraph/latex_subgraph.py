import argparse
import logging
import os
import sys
import time
from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.github.nodes.upload_files import upload_files
from airas.features.publication.html_subgraph.nodes.dispatch_workflow import (
    dispatch_workflow,
)
from airas.features.publication.latex_subgraph.input_data import (
    latex_subgraph_input_data,
)
from airas.features.publication.latex_subgraph.nodes.assemble_latex import LatexNode
from airas.features.publication.latex_subgraph.nodes.convert_to_latex import (
    convert_to_latex,
)
from airas.features.publication.latex_subgraph.nodes.generate_bib import generate_bib
from airas.features.publication.latex_subgraph.prompt.convert_to_latex_prompt import (
    convert_to_latex_prompt,
)
from airas.features.publication.latex_subgraph.prompt.generate_bib_prompt import (
    generate_bib_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepository
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
latex_timed = lambda f: time_node("latex_subgraph")(f)  # noqa: E731


class LatexSubgraphInputState(TypedDict):
    github_repository: str
    branch_name: str
    paper_content_with_placeholders: dict[str, str]
    references: dict[str, dict[str, Any]]
    image_file_name_list: list[str]


class LatexSubgraphHiddenState(TypedDict):
    github_owner: str
    repository_name: str
    paper_tex_content: dict[str, str]
    references_bib: dict[str, str]
    paper_upload: bool
    dispatch_paper_workflow: bool


class LatexSubgraphOutputState(TypedDict):
    tex_text: str


class LatexSubgraphState(
    # LatexSubgraphInputState,
    # LatexSubgraphHiddenState,
    # LatexSubgraphOutputState,
    ExecutionTimeState,
):
    new_method: ResearchHypothesis
    generate_paper_data: ResearchStudy
    experiment_repository: GitHubRepository
    references_bib: dict[str, str]


class LatexSubgraph(BaseSubgraph):
    # InputState = LatexSubgraphInputState
    # OutputState = LatexSubgraphOutputState

    def __init__(
        self,
        llm_name: str,
        tmp_dir: str | None = None,
        paper_name: str = "generated_paper.pdf",
    ):
        self.llm_name = llm_name
        self.tmp_dir = (
            tmp_dir
            if tmp_dir is not None
            else "/content/tmp"
            if "google.colab" in sys.modules or os.path.exists("/content")
            else "/workspaces/airas/tmp"
        )
        self.paper_name = paper_name

        self.upload_dir = ".research"
        self.workflow_file = "compile_latex.yml"
        check_api_key(llm_api_key_check=True)

    @latex_timed
    def _generate_bib(self, state: LatexSubgraphState) -> dict:
        generated_paper_data = state["generate_paper_data"]
        references_bib = generate_bib(
            llm_name=cast(LLM_MODEL, self.llm_name),
            prompt_template=generate_bib_prompt,
            references=generated_paper_data.references,
        )
        return {"references_bib": references_bib}

    @latex_timed
    def _convert_to_latex(self, state: LatexSubgraphState) -> dict:
        generated_paper_data = state["generate_paper_data"]
        paper_tex_content = convert_to_latex(
            llm_name=cast(LLM_MODEL, self.llm_name),
            prompt_template=convert_to_latex_prompt,
            paper_content_with_placeholders=generated_paper_data.citation_paper_body,
            references_bib=state["references_bib"],
        )
        return {"paper_tex_content": paper_tex_content}

    @latex_timed
    def _assemble_latex(self, state: LatexSubgraphState) -> dict:
        new_method = state["new_method"]
        tex_text = LatexNode(
            llm_name=cast(LLM_MODEL, self.llm_name),
            save_dir=self.tmp_dir,
            pdf_file_name=self.paper_name,
        ).assemble_latex(
            paper_tex_content=state["paper_tex_content"],
            references_bib=state["references_bib"],
            figures_name=new_method.experiment_result.image_file_name_list,
        )
        generated_paper_data = state["generate_paper_data"]
        generated_paper_data.alternative_formats.tex_data = tex_text
        return {"generated_paper_data": generated_paper_data}

    @latex_timed
    def _upload_latex(self, state: LatexSubgraphState) -> dict[str, bool]:
        local_file_paths = [
            os.path.join(self.tmp_dir, f) for f in os.listdir(self.tmp_dir)
        ]
        upload_latex_dir = os.path.join(self.upload_dir, "latex")
        experiment_repository = state["experiment_repository"]
        ok_pdf = upload_files(
            github_owner=experiment_repository.github_owner,
            repository_name=experiment_repository.repository_name,
            branch_name=experiment_repository.branch_name,
            upload_dir=upload_latex_dir,
            local_file_paths=local_file_paths,
            commit_message=f"Upload PDF for {experiment_repository.branch_name}",
        )
        return {"paper_upload": ok_pdf}

    @latex_timed
    def _dispatch_workflow(self, state: LatexSubgraphState) -> dict[str, bool]:
        time.sleep(3)
        experiment_repository = state["experiment_repository"]
        ok = dispatch_workflow(
            github_owner=experiment_repository.github_owner,
            repository_name=experiment_repository.repository_name,
            branch_name=experiment_repository.branch_name,
            workflow_file=self.workflow_file,
        )
        if ok:
            relative_path = os.path.join(self.upload_dir, self.paper_name).replace(
                "\\", "/"
            )
            url = (
                f"https://github.com/"
                f"{experiment_repository.github_owner}/{experiment_repository.repository_name}/blob/"
                f"{experiment_repository.branch_name}/{relative_path}"
            )
            print(f"Uploaded Paper available at: {url}")

        return {"dispatch_paper_workflow": ok}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(LatexSubgraphState)
        # graph_builder.add_node("init_state", self._init_state)
        graph_builder.add_node("generate_bib", self._generate_bib)
        graph_builder.add_node("convert_to_latex", self._convert_to_latex)
        graph_builder.add_node("assemble_latex", self._assemble_latex)
        graph_builder.add_node("upload_latex", self._upload_latex)
        graph_builder.add_node("dispatch_workflow", self._dispatch_workflow)

        # graph_builder.add_edge(START, "init_state")
        graph_builder.add_edge(START, "generate_bib")
        graph_builder.add_edge("generate_bib", "convert_to_latex")
        graph_builder.add_edge("convert_to_latex", "assemble_latex")
        graph_builder.add_edge("assemble_latex", "upload_latex")
        graph_builder.add_edge("upload_latex", "dispatch_workflow")
        graph_builder.add_edge("dispatch_workflow", END)

        return graph_builder.compile()

    # def run(self, state: dict[str, Any], config: dict | None = None) -> dict[str, Any]:
    #     # input_state_keys = self.InputState.__annotations__.keys()
    #     # output_state_keys = self.OutputState.__annotations__.keys()
    #     input_state = {k: state[k] for k in input_state_keys if k in state}

    #     if os.path.exists(self.tmp_dir):
    #         shutil.rmtree(self.tmp_dir)
    #     os.makedirs(self.tmp_dir, exist_ok=True)

    #     try:
    #         result = self.build_graph().invoke(state, config=config or {})
    #         # output_state = {k: result[k] for k in output_state_keys if k in result}

    #         cleaned_state = {k: v for k, v in state.items() if k != "subgraph_name"}

    #         return {
    #             "subgraph_name": self.__class__.__name__,
    #             **cleaned_state,
    #             **result,
    #             # **output_state,
    #         }
    #     finally:
    #         if os.path.exists(self.tmp_dir):
    #             shutil.rmtree(self.tmp_dir)


def main():
    parser = argparse.ArgumentParser(description="LatexSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument(
        "branch_name", help="Your branch name in your GitHub repository"
    )
    args = parser.parse_args()

    llm_name = "o3-mini-2025-01-31"
    input = {
        **latex_subgraph_input_data,
        "github_repository": args.github_repository,
        "branch_name": args.branch_name,
    }

    _ = LatexSubgraph(
        llm_name=llm_name,
    ).run(input)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running LatexSubgraph: {e}")
        raise
