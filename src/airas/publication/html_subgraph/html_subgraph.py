import argparse
import logging
import os
import shutil
import sys
import time
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.github.nodes.upload_files import upload_files
from airas.publication.html_subgraph.input_data import html_subgraph_input_data
from airas.publication.html_subgraph.nodes.convert_to_html import convert_to_html
from airas.publication.html_subgraph.nodes.dispatch_workflow import dispatch_workflow
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
    github_repository: str
    branch_name: str
    paper_content_with_placeholders: dict[str, str]
    references: dict[str, dict[str, Any]]


class HtmlSubgraphHiddenState(TypedDict):
    github_owner: str
    repository_name: str
    paper_html_content: str
    html_upload: bool
    dispatch_html_workflow: bool


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
        tmp_dir: str | None = None,
        html_name: str = "index.html", 
    ):
        self.llm_name = llm_name
        self.tmp_dir = (
            tmp_dir if tmp_dir is not None else
            "/content/tmp" if 'google.colab' in sys.modules or os.path.exists("/content")
            else "/workspaces/airas/tmp"
        )
        self.html_name = html_name
        self.html_path = [os.path.join(self.tmp_dir, self.html_name)]

        self.upload_branch = "gh-pages"
        self.workflow_file = "publish_html.yml"
        check_api_key(llm_api_key_check=True)

    def _init_state(self, state: HtmlSubgraphState) -> dict[str, str]:
        try:
            github_owner, repository_name = state["github_repository"].split("/", 1)
            return {
                "github_owner": github_owner,
                "repository_name": repository_name,
            }
        except ValueError:
            logger.error(f"Invalid github_repository format: {state['github_repository']}")
            raise

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
            save_dir=self.tmp_dir, 
            filename=self.html_name
        )
        return {"full_html": full_html}
    
    @html_timed
    def _upload_html(self, state: HtmlSubgraphState) -> dict[str, bool]:
        upload_dir = f"branches/{state['branch_name']}"

        ok_html = upload_files(
            github_owner=state["github_owner"],
            repository_name=state["repository_name"], 
            branch_name=self.upload_branch,
            upload_dir=upload_dir,
            local_file_paths=self.html_path,
            commit_message=f"Upload HTML for {self.upload_branch}",
        )
        return {"html_upload": ok_html}
    
    @html_timed
    def _dispatch_workflow(self, state: HtmlSubgraphState) -> dict[str, bool]:
        time.sleep(3) 
        ok = dispatch_workflow(
            github_owner=state["github_owner"], 
            repository_name=state["repository_name"], 
            branch_name=state["branch_name"], 
            workflow_file=self.workflow_file, 
        )
        if ok:
            file_name = os.path.basename(self.html_path[0])
            relative_path = os.path.join("branches", state["branch_name"], file_name).replace("\\", "/")
            url = (
                f"https://{state['github_owner']}.github.io/"
                f"{state['repository_name']}/{relative_path}"
            )
            print(
                f"Uploaded HTML available at: {url} "
                "(It may take a few minutes to reflect on GitHub Pages)"
            )

        return {"dispatch_html_workflow": ok}


    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(HtmlSubgraphState)
        graph_builder.add_node("init_state", self._init_state)
        graph_builder.add_node("convert_to_html", self._convert_to_html)
        graph_builder.add_node("render_html", self._render_html)
        graph_builder.add_node("upload_html", self._upload_html)
        graph_builder.add_node("dispatch_workflow", self._dispatch_workflow)


        graph_builder.add_edge(START, "init_state")
        graph_builder.add_edge("init_state", "convert_to_html")
        graph_builder.add_edge("convert_to_html", "render_html")
        graph_builder.add_edge("render_html", "upload_html")
        graph_builder.add_edge("upload_html", "dispatch_workflow")
        graph_builder.add_edge("dispatch_workflow", END)

        return graph_builder.compile()
    
    def run(
        self, 
        state: dict[str, Any], 
        config: dict | None = None
    ) -> dict[str, Any]:
        input_state_keys = HtmlSubgraphInputState.__annotations__.keys()
        output_state_keys = HtmlSubgraphOutputState.__annotations__.keys()
        input_state = {k: state[k] for k in input_state_keys if k in state}

        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)
        os.makedirs(self.tmp_dir, exist_ok=True)

        try:
            result = self.build_graph().invoke(input_state, config=config or {})
            output_state = {k: result[k] for k in output_state_keys if k in result}

            cleaned_state = {k: v for k, v in state.items() if k != "subgraph_name"}

            return {
                "subgraph_name": self.__class__.__name__,
                **cleaned_state,
                **output_state,
            }
        finally:
            if os.path.exists(self.tmp_dir):
                shutil.rmtree(self.tmp_dir)


def main():
    parser = argparse.ArgumentParser(description="HtmlSubgraph")
    parser.add_argument("github_repository", help="Your GitHub repository")
    parser.add_argument("branch_name", help="Your branch name in your GitHub repository")
    args = parser.parse_args()

    llm_name = "o3-mini-2025-01-31"
    input = html_subgraph_input_data
    input = {
        **input, 
        "github_repository": args.github_repository, 
        "branch_name": args.branch_name, 
    }

    result = HtmlSubgraph(
        llm_name=llm_name, 
    ).run(input)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running HtmlSubgraph: {e}")
        raise
