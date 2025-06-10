import argparse
import logging
import os
import shutil
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import NotRequired, TypedDict

from airas.github.nodes.upload_files import upload_files
from airas.publication.latex_subgraph.input_data import latex_subgraph_input_data
from airas.publication.latex_subgraph.nodes.compile_to_pdf import LatexNode
from airas.publication.latex_subgraph.nodes.convert_to_latex import (
    convert_to_latex,
)
from airas.publication.latex_subgraph.nodes.generate_bib import generate_bib
from airas.publication.latex_subgraph.prompt.convert_to_latex_prompt import (
    convert_to_latex_prompt,
)
from airas.publication.latex_subgraph.prompt.generate_bib_prompt import (
    generate_bib_prompt,
)
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
latex_timed = lambda f: time_node("latex_subgraph")(f)  # noqa: E731


class LatexSubgraphInputState(TypedDict):
    paper_content_with_placeholders: dict[str, str]
    references: dict[str, dict[str, Any]]
    figures_dir: NotRequired[str]


class LatexSubgraphHiddenState(TypedDict):
    paper_tex_content: dict[str, str]
    references_bib: dict[str, str]
    paper_upload: bool


class LatexSubgraphOutputState(TypedDict):
    tex_text: str


class LatexSubgraphState(
    LatexSubgraphInputState,
    LatexSubgraphHiddenState,
    LatexSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class LatexSubgraph:
    def __init__(
        self,
        llm_name: str,
        save_dir: str,
        github_repository: str,
        branch_name: str,
        upload_dir: str | None = None,
        pdf_name: str = "generated_paper.pdf", 
    ):
        self.llm_name = llm_name
        self.save_dir = save_dir
        self.github_repository = github_repository
        self.branch_name = branch_name
        
        self.upload_dir = upload_dir or ".research"
        self.pdf_name = pdf_name

        self.latex_dir = os.path.join(save_dir, "latex")
        if os.path.exists(self.latex_dir):  # NOTE: Cleanup – remove existing contents in save_dir/latex/
            shutil.rmtree(self.latex_dir)
        os.makedirs(self.latex_dir, exist_ok=True)

        if "/" in self.github_repository:
            self.github_owner, self.repository_name = self.github_repository.split("/", 1)
        else:
            raise ValueError("Invalid repository name format.")

        check_api_key(llm_api_key_check=True)

    @latex_timed
    def _generate_bib(self, state: LatexSubgraphState) -> dict:
        references_bib = generate_bib(
            llm_name=self.llm_name, 
            prompt_template=generate_bib_prompt, 
            references=state["references"]
        )
        return {"references_bib": references_bib}

    @latex_timed
    def _convert_to_latex(self, state: LatexSubgraphState) -> dict:
        paper_tex_content = convert_to_latex(
            llm_name=self.llm_name,
            prompt_template=convert_to_latex_prompt,
            paper_content_with_placeholders=state["paper_content_with_placeholders"],
            references_bib=state["references_bib"], 
        )
        return {"paper_tex_content": paper_tex_content}

    @latex_timed
    def _compile_to_pdf(self, state: LatexSubgraphState) -> dict:
        tex_text = LatexNode(
            llm_name=self.llm_name,
            save_dir=self.latex_dir,
            figures_dir=state["figures_dir"],
            pdf_file_name=self.pdf_name, 
        ).compile_to_pdf(
            paper_tex_content=state["paper_tex_content"],
            references_bib=state["references_bib"], 
        )
        return {"tex_text": tex_text}
    
    @latex_timed
    def _upload_files(self, state: LatexSubgraphState) -> dict[str, bool]:
        pdf_path = [os.path.join(self.latex_dir, self.pdf_name)]

        ok_pdf = upload_files(
            github_owner=self.github_owner,
            repository_name=self.repository_name,
            branch_name=self.branch_name,
            upload_dir=self.upload_dir,
            local_file_paths=pdf_path,
            commit_message=f"Upload PDF for {self.branch_name}",
        )

        target_path = os.path.join(
            self.upload_dir,
            os.path.basename(pdf_path[0]),
        ).replace("\\", "/")
        relative_path = target_path.lstrip("/")

        print(
            f"Uploaded Paper available at: https://github.com/"
            f"{self.github_owner}/{self.repository_name}/blob/"
            f"{self.branch_name}/{relative_path}"
        )
        return {"paper_upload": ok_pdf}
        
    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(LatexSubgraphState)
        graph_builder.add_node("generate_bib", self._generate_bib)
        graph_builder.add_node("convert_to_latex", self._convert_to_latex)
        graph_builder.add_node("compile_to_pdf", self._compile_to_pdf)
        graph_builder.add_node("upload_files", self._upload_files)

        graph_builder.add_edge(START, "generate_bib")
        graph_builder.add_edge("generate_bib", "convert_to_latex")
        graph_builder.add_edge("convert_to_latex", "compile_to_pdf")
        graph_builder.add_edge("compile_to_pdf", "upload_files")
        graph_builder.add_edge("upload_files", END)

        return graph_builder.compile()

    def run(
        self, 
        state: dict[str, Any], 
        config: dict | None = None
    ) -> dict[str, Any]:
        input_state_keys = LatexSubgraphInputState.__annotations__.keys()
        output_state_keys = LatexSubgraphOutputState.__annotations__.keys()

        input_state = {k: state[k] for k in input_state_keys if k in state}
        result = self.build_graph().invoke(input_state, config=config or {})
        output_state = {k: result[k] for k in output_state_keys if k in result}

        return {
            "subgraph_name": self.__class__.__name__,
            **state,
            **output_state, 
        }


def main():
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description="HtmlSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("branch_name", help="Your branch name in your GitHub repository")
    args = parser.parse_args()

    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/airas/data"
    input = latex_subgraph_input_data

    result = LatexSubgraph(
        llm_name=llm_name, 
        save_dir=save_dir, 
        github_repository=args.github_repository, 
        branch_name=args.branch_name
    ).run(input)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running LatexSubgraph: {e}")
        raise
