import logging
from typing import Any, cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import validate_call
from typing_extensions import TypedDict

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
from airas.types.latex import LATEX_TEMPLATE_NAME
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)
create_bibfile_timed = lambda f: time_node("create_bibfile_subgraph")(f)  # noqa: E731


class CreateBibfileSubgraphInputState(TypedDict):
    research_study_list: list[dict]
    reference_study_list: list[dict]
    research_hypothesis: dict
    github_repository: dict[str, str]


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
        llm_name: LLM_MODEL,
        latex_template: LATEX_TEMPLATE_NAME,
        max_filtered_references: int = 30,
    ):
        self.llm_name = llm_name
        self.latex_template = latex_template
        self.max_filtered_references = max_filtered_references
        check_api_key(llm_api_key_check=True)

    @create_bibfile_timed
    def _filter_references(
        self, state: CreateBibfileSubgraphState
    ) -> dict[str, list[dict]]:
        filtered_references = filter_references(
            llm_name=cast(LLM_MODEL, self.llm_name),
            prompt_template=filter_references_prompt,
            research_study_list=state["research_study_list"],
            reference_study_list=state["reference_study_list"],
            research_hypothesis=state["research_hypothesis"],
            max_results=self.max_filtered_references,
        )
        return {"reference_study_list": filtered_references}

    @create_bibfile_timed
    def _create_bibtex(self, state: CreateBibfileSubgraphState) -> dict[str, str]:
        references_bib = create_bibtex(
            research_study_list=state["research_study_list"],
            reference_study_list=state["reference_study_list"],
        )
        return {"references_bib": references_bib}

    @create_bibfile_timed
    def _update_repository_bibfile(
        self, state: CreateBibfileSubgraphState
    ) -> dict[str, Any]:
        success = update_repository_bibfile(
            github_repository=state["github_repository"],
            references_bib=state["references_bib"],
            latex_template=self.latex_template,
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
    llm_name = "gemini-2.0-flash-001"

    result = CreateBibfileSubgraph(
        llm_name=llm_name,
        latex_template="iclr2024",
        max_filtered_references=20,  # Example: limit to 20 references
    ).run(create_bibfile_subgraph_input_data)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateBibfileSubgraph: {e}")
        raise
