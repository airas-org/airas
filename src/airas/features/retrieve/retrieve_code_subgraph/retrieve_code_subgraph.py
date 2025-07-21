import json
import logging
from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.core.base import BaseSubgraph
from airas.features.retrieve.retrieve_code_subgraph.input_data import (
    retrieve_code_subgraph_input_data,
)
from airas.features.retrieve.retrieve_code_subgraph.node.extract_experimental_info import (
    extract_experimental_info,
)
from airas.features.retrieve.retrieve_code_subgraph.node.extract_github_url_from_text import (
    extract_github_url_from_text,
)
from airas.features.retrieve.retrieve_code_subgraph.node.retrieve_repository_contents import (
    retrieve_repository_contents,
)
from airas.features.retrieve.retrieve_code_subgraph.prompt.extract_experimental_info_prompt import (
    extract_experimental_info_prompt,
)
from airas.features.retrieve.retrieve_code_subgraph.prompt.extract_github_url_prompt import (
    extract_github_url_from_text_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

retrieve_code_timed = lambda f: time_node("retrieve_code_subgraph")(f)  # noqa: E731


class RetrieveCodeInputState(TypedDict):
    research_study_list: list[dict[str, Any]]


class RetrieveCodeHiddenState(TypedDict):
    code_str_list: list[str]


class RetrieveCodeOutputState(TypedDict):
    research_study_list: list[dict[str, Any]]


class RetrieveCodeState(
    RetrieveCodeInputState,
    RetrieveCodeHiddenState,
    RetrieveCodeOutputState,
    ExecutionTimeState,
):
    pass


class RetrieveCodeSubgraph(BaseSubgraph):
    InputState = RetrieveCodeInputState
    OutputState = RetrieveCodeOutputState

    def __init__(
        self,
        llm_name: LLM_MODEL = "gemini-2.0-flash-001",
    ):
        check_api_key(llm_api_key_check=True)
        self.llm_name = llm_name

    def _extract_github_url_from_text(self, state: RetrieveCodeState) -> dict:
        research_study_list = state["research_study_list"]
        for research_study in research_study_list:
            github_url = extract_github_url_from_text(
                paper_full_text=research_study["full_text"],
                paper_summary=research_study["llm_extracted_info"]["methodology"],
                llm_name=cast(LLM_MODEL, self.llm_name),
                prompt_template=extract_github_url_from_text_prompt,
            )
            research_study["meta_data"] = {}
            research_study["meta_data"]["github_url"] = github_url
        return {
            "research_study_list": research_study_list,
        }

    @retrieve_code_timed
    def _retrieve_repository_contents(self, state: RetrieveCodeState) -> dict:
        research_study_list = state["research_study_list"]
        code_str_list = []
        for research_study in research_study_list:
            code_str = retrieve_repository_contents(
                github_url=research_study["meta_data"]["github_url"]
            )
            code_str_list.append(code_str)
        return {
            "code_str_list": code_str_list,
        }

    @retrieve_code_timed
    def _extract_experimental_info(self, state: RetrieveCodeState) -> dict:
        code_str_list = state["code_str_list"]
        research_study_list = state["research_study_list"]
        for code_str, research_study in zip(
            code_str_list, research_study_list, strict=True
        ):
            if code_str == "":
                research_study["experimental_code"] = ""
                research_study["experimental_info"] = ""
            else:
                extract_code, experimental_info = extract_experimental_info(
                    llm_name=cast(LLM_MODEL, self.llm_name),
                    method_text=research_study["llm_extracted_info"]["methodology"],
                    repository_content_str=code_str,
                    prompt_template=extract_experimental_info_prompt,
                )
                research_study["llm_extracted_info"]["experimental_code"] = extract_code
                research_study["llm_extracted_info"]["experimental_info"] = (
                    experimental_info
                )

        return {"research_study_list": research_study_list}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(RetrieveCodeState)
        graph_builder.add_node(
            "extract_github_url_from_text", self._extract_github_url_from_text
        )
        graph_builder.add_node(
            "retrieve_repository_contents", self._retrieve_repository_contents
        )
        graph_builder.add_node(
            "extract_experimental_info", self._extract_experimental_info
        )

        graph_builder.add_edge(START, "extract_github_url_from_text")
        graph_builder.add_edge(
            "extract_github_url_from_text", "retrieve_repository_contents"
        )
        graph_builder.add_edge(
            "retrieve_repository_contents", "extract_experimental_info"
        )
        graph_builder.add_edge("extract_experimental_info", END)
        return graph_builder.compile()


def main():
    input = retrieve_code_subgraph_input_data
    result = RetrieveCodeSubgraph().run(input)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running RetrieveCodeSubgraph: {e}")
        raise
