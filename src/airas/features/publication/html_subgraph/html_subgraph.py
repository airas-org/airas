import logging
import time

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.publication.html_subgraph.input_data import html_subgraph_input_data
from airas.features.publication.html_subgraph.nodes.convert_to_html import (
    convert_to_html,
)
from airas.features.publication.html_subgraph.nodes.prepare_images_for_html import (
    prepare_images_for_html,
)
from airas.features.publication.html_subgraph.nodes.render_html import render_html
from airas.features.publication.html_subgraph.nodes.replace_citation_keys_with_links import (
    replace_citation_keys_with_links,
)
from airas.features.publication.html_subgraph.nodes.upload_html import upload_html
from airas.features.publication.html_subgraph.prompt.convert_to_html_prompt import (
    convert_to_html_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.paper import PaperContent
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
html_timed = lambda f: time_node("html_subgraph")(f)  # noqa: E731


class HtmlLLMMapping(BaseModel):
    convert_to_html: LLM_MODEL = DEFAULT_NODE_LLMS["convert_to_html"]


class HtmlSubgraphInputState(TypedDict):
    github_repository_info: GitHubRepositoryInfo
    paper_content: PaperContent
    references_bib: str
    new_method: ResearchHypothesis


class HtmlSubgraphHiddenState(TypedDict):
    paper_content_html: str
    html_upload: bool


class HtmlSubgraphOutputState(TypedDict):
    full_html: str
    github_pages_url: str | None


class HtmlSubgraphState(
    HtmlSubgraphInputState,
    HtmlSubgraphHiddenState,
    HtmlSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class HtmlSubgraph(BaseSubgraph):
    InputState = HtmlSubgraphInputState
    OutputState = HtmlSubgraphOutputState

    def __init__(
        self,
        llm_mapping: dict[str, str] | HtmlLLMMapping | None = None,
    ):
        if llm_mapping is None:
            self.llm_mapping = HtmlLLMMapping()
        elif isinstance(llm_mapping, dict):
            self.llm_mapping = HtmlLLMMapping(**llm_mapping)
        elif isinstance(llm_mapping, HtmlLLMMapping):
            # すでに型が正しい場合も受け入れる
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or HtmlLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        check_api_key(llm_api_key_check=True)

    @html_timed
    def _convert_to_html(self, state: HtmlSubgraphState) -> dict[str, str]:
        image_file_name_list = (
            getattr(
                state["new_method"].experimental_results, "image_file_name_list", None
            )
            or []
        )
        paper_content_html = convert_to_html(
            llm_name=self.llm_mapping.convert_to_html,
            paper_content=state["paper_content"],
            image_file_name_list=image_file_name_list,
            prompt_template=convert_to_html_prompt,
        )
        return {"paper_content_html": paper_content_html}

    @html_timed
    def _replace_citation_keys_with_links(
        self, state: HtmlSubgraphState
    ) -> dict[str, str]:
        paper_content_html = replace_citation_keys_with_links(
            html_text=state["paper_content_html"],
            references_bib=state["references_bib"],
        )
        return {"paper_content_html": paper_content_html}

    @html_timed
    def _render_html(self, state: HtmlSubgraphState) -> dict[str, str]:
        full_html = render_html(
            paper_content_html=state["paper_content_html"],
        )
        return {"full_html": full_html}

    @html_timed
    def _upload_html(self, state: HtmlSubgraphState) -> dict[str, bool]:
        full_html = state["full_html"]

        ok = upload_html(
            github_repository=state["github_repository_info"],
            full_html=full_html,
        )
        return {"html_upload": ok}

    @html_timed
    def _prepare_images_for_html(
        self, state: HtmlSubgraphState
    ) -> dict[str, str | bool]:
        time.sleep(3)

        github_pages_url = prepare_images_for_html(
            github_repository=state["github_repository_info"],
        )

        return {
            "github_pages_url": github_pages_url,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(HtmlSubgraphState)
        graph_builder.add_node("convert_to_html", self._convert_to_html)
        graph_builder.add_node(
            "replace_citation_keys_with_links", self._replace_citation_keys_with_links
        )
        graph_builder.add_node("render_html", self._render_html)
        graph_builder.add_node("upload_html", self._upload_html)
        graph_builder.add_node("prepare_images_for_html", self._prepare_images_for_html)

        graph_builder.add_edge(START, "convert_to_html")
        graph_builder.add_edge("convert_to_html", "replace_citation_keys_with_links")
        graph_builder.add_edge("replace_citation_keys_with_links", "render_html")
        graph_builder.add_edge("render_html", "upload_html")
        graph_builder.add_edge("upload_html", "prepare_images_for_html")
        graph_builder.add_edge("prepare_images_for_html", END)

        return graph_builder.compile()


def main():
    input = html_subgraph_input_data

    result = HtmlSubgraph().run(input)
    print(f"Result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running HtmlSubgraph: {e}")
        raise
