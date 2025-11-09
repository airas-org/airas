import asyncio
import logging

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
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
from airas.features.retrieve.retrieve_code_subgraph.prompt.extract_github_url_prompt import (
    extract_github_url_from_text_prompt,
)
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_study import ResearchStudy
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

retrieve_code_timed = lambda f: time_node("retrieve_code_subgraph")(f)  # noqa: E731


class RetrieveCodeLLMMapping(BaseModel):
    extract_github_url_from_text: LLM_MODEL = DEFAULT_NODE_LLMS[
        "extract_github_url_from_text"
    ]
    extract_experimental_info: LLM_MODEL = DEFAULT_NODE_LLMS[
        "extract_experimental_info"
    ]


class RetrieveCodeInputState(TypedDict):
    research_study_list: list[ResearchStudy]


class RetrieveCodeHiddenState(TypedDict):
    code_str_list: list[str]


class RetrieveCodeOutputState(TypedDict):
    research_study_list: list[ResearchStudy]


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
        llm_client: LLMFacadeClient,
        github_client: GithubClient,
        llm_mapping: dict[str, str] | RetrieveCodeLLMMapping | None = None,
    ):
        if llm_mapping is None:
            self.llm_mapping = RetrieveCodeLLMMapping()
        elif isinstance(llm_mapping, dict):
            self.llm_mapping = RetrieveCodeLLMMapping(**llm_mapping)
        elif isinstance(llm_mapping, RetrieveCodeLLMMapping):
            # すでに型が正しい場合も受け入れる
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or RetrieveCodeLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.llm_client = llm_client
        self.github_client = github_client
        check_api_key(llm_api_key_check=True)

    @retrieve_code_timed
    async def _extract_github_url_from_text(
        self, state: RetrieveCodeState
    ) -> dict[str, list[ResearchStudy]]:
        research_study_list = await extract_github_url_from_text(
            llm_name=self.llm_mapping.extract_github_url_from_text,
            prompt_template=extract_github_url_from_text_prompt,
            research_study_list=state["research_study_list"],
            llm_client=self.llm_client,
            github_client=self.github_client,
        )
        return {
            "research_study_list": research_study_list,
        }

    @retrieve_code_timed
    def _retrieve_repository_contents(
        self, state: RetrieveCodeState
    ) -> dict[str, list[str]]:
        code_str_list = retrieve_repository_contents(
            research_study_list=state["research_study_list"]
        )
        return {
            "code_str_list": code_str_list,
        }

    @retrieve_code_timed
    async def _extract_experimental_info(
        self, state: RetrieveCodeState
    ) -> dict[str, list[ResearchStudy]]:
        research_study_list = await extract_experimental_info(
            llm_name=self.llm_mapping.extract_experimental_info,
            client=self.llm_client,
            research_study_list=state["research_study_list"],
            code_str_list=state["code_str_list"],
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


async def main():
    input = retrieve_code_subgraph_input_data
    result = await RetrieveCodeSubgraph().arun(input)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Error running RetrieveCodeSubgraph: {e}")
        raise
