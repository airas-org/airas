import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel, validate_call
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.write.create_bibfile_subgraph.input_data import (
    create_bibfile_subgraph_input_data,
)
from airas.features.write.create_bibfile_subgraph.nodes.create_bibtex import (
    create_bibtex,
)
from airas.features.write.create_bibfile_subgraph.nodes.filter_references import (
    filter_references,
)
from airas.features.write.create_bibfile_subgraph.nodes.update_repository_bibfile import (
    update_repository_bibfile,
)
from airas.features.write.create_bibfile_subgraph.prompt.filter_references_prompt import (
    filter_references_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.latex import LATEX_TEMPLATE_NAME
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
create_bibfile_timed = lambda f: time_node("create_bibfile_subgraph")(f)  # noqa: E731


class CreateBibfileLLMMapping(BaseModel):
    filter_references: LLM_MODEL = DEFAULT_NODE_LLMS["filter_references"]


class CreateBibfileSubgraphInputState(TypedDict):
    research_study_list: list[ResearchStudy]
    reference_research_study_list: list[ResearchStudy]
    new_method: ResearchHypothesis
    github_repository_info: GitHubRepositoryInfo


class CreateBibfileSubgraphHiddenState(TypedDict): ...


class CreateBibfileSubgraphOutputState(TypedDict):
    references_bib: str


class CreateBibfileSubgraphState(
    CreateBibfileSubgraphInputState,
    CreateBibfileSubgraphHiddenState,
    CreateBibfileSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class CreateBibfileSubgraph(BaseSubgraph):
    InputState = CreateBibfileSubgraphInputState
    OutputState = CreateBibfileSubgraphOutputState

    @validate_call
    def __init__(
        self,
        llm_mapping: dict[str, str] | CreateBibfileLLMMapping | None = None,
        latex_template_name: LATEX_TEMPLATE_NAME = "iclr2024",
        max_filtered_references: int = 30,
    ):
        if llm_mapping is None:
            self.llm_mapping = CreateBibfileLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = CreateBibfileLLMMapping.model_validate(llm_mapping)
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, CreateBibfileLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or CreateBibfileLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.latex_template_name = latex_template_name
        self.max_filtered_references = max_filtered_references
        check_api_key(llm_api_key_check=True)

    @create_bibfile_timed
    def _filter_references(
        self, state: CreateBibfileSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        filtered_references = filter_references(
            llm_name=self.llm_mapping.filter_references,
            prompt_template=filter_references_prompt,
            research_study_list=state["research_study_list"],
            reference_study_list=state["reference_research_study_list"],
            new_method=state["new_method"],
            github_repository_info=state["github_repository_info"],
            max_results=self.max_filtered_references,
        )
        return {"reference_research_study_list": filtered_references}

    @create_bibfile_timed
    def _create_bibtex(self, state: CreateBibfileSubgraphState) -> dict[str, str]:
        references_bib = create_bibtex(
            research_study_list=state["research_study_list"],
            reference_research_study_list=state["reference_research_study_list"],
        )
        return {"references_bib": references_bib}

    @create_bibfile_timed
    def _update_repository_bibfile(
        self, state: CreateBibfileSubgraphState
    ) -> dict[str, Any]:
        success = update_repository_bibfile(
            github_repository_info=state["github_repository_info"],
            references_bib=state["references_bib"],
            latex_template_name=self.latex_template_name,
        )
        return {"update_success": success}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateBibfileSubgraphState)
        graph_builder.add_node("filter_references", self._filter_references)
        graph_builder.add_node("create_bibtex", self._create_bibtex)
        graph_builder.add_node(
            "update_repository_bibfile", self._update_repository_bibfile
        )

        graph_builder.add_edge(START, "filter_references")
        graph_builder.add_edge("filter_references", "create_bibtex")
        graph_builder.add_edge("create_bibtex", "update_repository_bibfile")
        graph_builder.add_edge("update_repository_bibfile", END)

        return graph_builder.compile()


def main():
    result = CreateBibfileSubgraph(
        latex_template_name="iclr2024",
        max_filtered_references=20,
    ).run(create_bibfile_subgraph_input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateBibfileSubgraph: {e}")
        raise
