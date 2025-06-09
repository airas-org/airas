import argparse
import glob
import logging
import os
import shutil
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import NotRequired, TypedDict

from airas.github.nodes.upload_files import upload_files
from airas.publication.html_subgraph.input_data import html_subgraph_input_data
from airas.publication.html_subgraph.nodes.convert_pdf_to_png import convert_pdf_to_png
from airas.publication.html_subgraph.nodes.convert_to_html import convert_to_html
from airas.publication.html_subgraph.nodes.render_html import render_html
from airas.publication.html_subgraph.prompt.convert_to_html_prompt import (
    convert_to_html_prompt,
)
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
html_timed = lambda f: time_node("html_subgraph")(f)  # noqa: E731


class HtmlSubgraphInputState(TypedDict):
    paper_content_with_placeholders: dict[str, str]
    references: dict[str, dict[str, Any]]
    figures_dir: NotRequired[str]


class HtmlSubgraphHiddenState(TypedDict):
    pdf_to_png: bool
    paper_html_content: str
    html_upload: bool


class HtmlSubgraphOutputState(TypedDict):
    full_html: str


class HtmlSubgraphState(
    HtmlSubgraphInputState,
    HtmlSubgraphHiddenState,
    HtmlSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class HtmlSubgraph:
    def __init__(
        self,
        llm_name: str,
        save_dir: str,
        github_repository: str, 
        branch_name: str, 
        upload_dir: str | None = None, 
        html_name: str = "index.html", 
    ):
        self.llm_name = llm_name
        self.save_dir = save_dir
        self.github_repository = github_repository
        self.branch_name = branch_name

        self.upload_branch = "gh-pages"
        self.upload_dir = upload_dir or f"branches/{self.branch_name}"
        self.html_name = html_name

        self.html_dir = os.path.join(save_dir, "html")
        if os.path.exists(self.html_dir):   # NOTE: Cleanup – remove existing contents in save_dir/html/
            shutil.rmtree(self.html_dir)
        os.makedirs(self.html_dir, exist_ok=True)
        
        if "/" in self.github_repository:
            self.github_owner, self.repository_name = self.github_repository.split("/", 1)
        else:
            raise ValueError("Invalid repository name format.")

        check_api_key(llm_api_key_check=True)

    @html_timed
    def _convert_pdf_to_png(self, state: HtmlSubgraphState) -> dict[str, bool]:
        pdf_dir = state.get("figures_dir")
        if pdf_dir is None:
            logger.info("No images available. Skipping PDF to PNG conversion.")
            return {"pdf_to_png": False}
        
        to_png_dir = os.path.join(self.html_dir, "images")
        pdf_to_png = convert_pdf_to_png(pdf_dir, to_png_dir)
        return {
            "pdf_to_png": pdf_to_png
        }

    @html_timed
    def _convert_to_html(self, state: HtmlSubgraphState) -> dict:
        paper_html_content = convert_to_html(
            llm_name=self.llm_name,
            paper_content_with_placeholders=state["paper_content_with_placeholders"],
            references=state["references"], 
            prompt_template=convert_to_html_prompt, 
        )
        return {"paper_html_content": paper_html_content}

    @html_timed
    def _render_html(self, state: HtmlSubgraphState) -> dict:
        full_html = render_html(
            paper_html_content=state["paper_html_content"], 
            save_dir=self.html_dir, 
            filename=self.html_name
        )
        return {"full_html": full_html}
    
    @html_timed
    def _upload_files(self, state: HtmlSubgraphState) -> dict[str, bool]:
        html_path = [os.path.join(self.html_dir, self.html_name)]
        png_path = glob.glob(os.path.join(self.html_dir, "images", "*.png"))

        ok_html = upload_files(
            github_owner=self.github_owner,
            repository_name=self.repository_name,
            branch_name=self.upload_branch,
            upload_dir=self.upload_dir,
            local_file_paths=html_path,
            commit_message=f"Upload HTML for {self.branch_name}",
        )

        ok_png = True
        if png_path:
            ok_png = upload_files(
                github_owner=self.github_owner,
                repository_name=self.repository_name,
                branch_name=self.upload_branch,
                upload_dir=os.path.join(self.upload_dir, "images"),
                local_file_paths=png_path,
                commit_message=f"Upload images for {self.branch_name}",
            )

        target_path = os.path.join(
            self.upload_dir,
            os.path.basename(html_path[0]),
        ).replace("\\", "/")
        relative_path = target_path.lstrip("/")
        print(
            f"Uploaded HTML available at: https://{self.github_owner}.github.io/"
            f"{self.repository_name}/{relative_path} "
            "(It may take a few minutes to reflect on GitHub Pages)"
        )

        return {"html_upload": ok_html and ok_png}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(HtmlSubgraphState)
        graph_builder.add_node("convert_pdf_to_png", self._convert_pdf_to_png)
        graph_builder.add_node("convert_to_html", self._convert_to_html)
        graph_builder.add_node("render_html", self._render_html)
        graph_builder.add_node("upload_files", self._upload_files)

        graph_builder.add_edge(START, "convert_pdf_to_png")
        graph_builder.add_edge("convert_pdf_to_png", "convert_to_html")
        graph_builder.add_edge("convert_to_html", "render_html")
        graph_builder.add_edge("render_html", "upload_files")
        graph_builder.add_edge("upload_files", END)

        return graph_builder.compile()
    
    def run(
        self, 
        input: HtmlSubgraphInputState, 
        config: dict | None = None
    ) -> HtmlSubgraphOutputState:
        graph = self.build_graph()
        result = graph.invoke(input, config=config or {})

        output_keys = HtmlSubgraphOutputState.__annotations__.keys()
        output = {k: result[k] for k in output_keys if k in result}
        return output


def main():
    parser = argparse.ArgumentParser()
    parser = argparse.ArgumentParser(description="HtmlSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("branch_name", help="Your branch name in your GitHub repository")
    args = parser.parse_args()

    llm_name = "o3-mini-2025-01-31"
    save_dir = "/workspaces/airas/data"
    input = html_subgraph_input_data

    result = HtmlSubgraph(
        llm_name=llm_name, 
        save_dir=save_dir, 
        github_repository=args.github_repository, 
        branch_name=args.branch_name, 
    ).run(input)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running HtmlSubgraph: {e}")
        raise
