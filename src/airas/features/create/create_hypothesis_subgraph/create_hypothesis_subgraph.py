import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.create.create_hypothesis_subgraph.input_data import (
    create_hypothesis_subgraph_input_data,
)
from airas.features.create.create_hypothesis_subgraph.nodes.evaluate_novelty_and_significance import (
    evaluate_novelty_and_significance,
)
from airas.features.create.create_hypothesis_subgraph.nodes.generate_hypothesis import (
    generate_hypothesis,
)
from airas.features.create.create_hypothesis_subgraph.nodes.refine_hypothesis import (
    refine_hypothesis,
)
from airas.features.retrieve.get_paper_titles_subgraph.nodes.get_paper_title_from_qdrant import (
    get_paper_titles_from_qdrant,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.nodes.retrieve_text_from_url import (
    retrieve_text_from_url,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.nodes.search_arxiv_by_id import (
    search_arxiv_by_id,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.nodes.search_arxiv_id_from_title import (
    search_arxiv_id_from_title,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.nodes.search_ss_by_id import (
    search_ss_by_id,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.prompt.openai_websearch_arxiv_ids_prompt import (
    openai_websearch_arxiv_ids_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_idea import (
    ResearchIdea,
)
from airas.types.research_study import ResearchStudy
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_hypothesis_timed = lambda f: time_node("create_hypothesis_subgraph")(f)  # noqa: E731


class CreateHypothesisSubgraphLLMMapping(BaseModel):
    generate_hypothesis: LLM_MODEL = DEFAULT_NODE_LLMS[
        "generate_idea_and_research_summary"
    ]
    evaluate_novelty_and_significance: LLM_MODEL = DEFAULT_NODE_LLMS[
        "evaluate_novelty_and_significance"
    ]
    refine_hypothesis: LLM_MODEL = DEFAULT_NODE_LLMS["refine_idea_and_research_summary"]
    search_arxiv_id_from_title: LLM_MODEL = DEFAULT_NODE_LLMS[
        "search_arxiv_id_from_title"
    ]


class CreateHypothesisSubgraphInputState(TypedDict):
    research_topic: str
    research_study_list: list[ResearchStudy]
    github_repository_info: GitHubRepositoryInfo


class CreateHypothesisSubgraphHiddenState(TypedDict):
    new_idea_info: ResearchIdea
    related_research_study_list: list[ResearchStudy]
    refine_iterations: int


class CreateHypothesisSubgraphOutputState(TypedDict):
    new_method: ResearchHypothesis
    idea_info_history: list[ResearchIdea]


class CreateHypothesisSubgraphState(
    CreateHypothesisSubgraphInputState,
    CreateHypothesisSubgraphHiddenState,
    CreateHypothesisSubgraphOutputState,
    ExecutionTimeState,
):
    pass


class CreateHypothesisSubgraph(BaseSubgraph):
    InputState = CreateHypothesisSubgraphInputState
    OutputState = CreateHypothesisSubgraphOutputState

    def __init__(
        self,
        llm_mapping: dict[str, str] | CreateHypothesisSubgraphLLMMapping | None = None,
        refinement_rounds: int = 2,
        paper_provider: str = "arxiv",
        num_retrieve_related_papers: int = 10,
    ):
        if llm_mapping is None:
            self.llm_mapping = CreateHypothesisSubgraphLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = CreateHypothesisSubgraphLLMMapping.model_validate(
                    llm_mapping
                )
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, CreateHypothesisSubgraphLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or CreateHypothesisSubgraphLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.refinement_rounds = refinement_rounds
        self.paper_provider = paper_provider
        self.num_retrieve_related_papers = num_retrieve_related_papers
        check_api_key(llm_api_key_check=True)

    @create_hypothesis_timed
    def _initialize(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, list[ResearchIdea] | int]:
        return {
            "idea_info_history": [],
            "refine_iterations": 0,
        }

    @create_hypothesis_timed
    def _generate_hypothesis(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, ResearchIdea]:
        new_idea_info = generate_hypothesis(
            llm_name=self.llm_mapping.generate_hypothesis,
            research_topic=state["research_topic"],
            research_study_list=state["research_study_list"],
            github_repository_info=state["github_repository_info"],
        )
        return {"new_idea_info": new_idea_info}

    @create_hypothesis_timed
    def _retrieve_related_papers(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        retrieved_titles = get_paper_titles_from_qdrant(
            queries=[state["new_idea_info"].idea.method],
            num_retrieve_paper=self.num_retrieve_related_papers,
        )
        retrieved_studies = [
            ResearchStudy(title=title) for title in (retrieved_titles or [])
        ]

        existing_titles = {study.title for study in state["research_study_list"]}
        unique_research_studies = [
            study for study in retrieved_studies if study.title not in existing_titles
        ]
        return {"related_research_study_list": unique_research_studies}

    @create_hypothesis_timed
    def _search_arxiv_id_from_title(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        related_research_study_list = search_arxiv_id_from_title(
            llm_name=self.llm_mapping.search_arxiv_id_from_title,
            prompt_template=openai_websearch_arxiv_ids_prompt,
            research_study_list=state["related_research_study_list"],
        )
        return {"related_research_study_list": related_research_study_list}

    @create_hypothesis_timed
    def _search_arxiv_by_id(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        related_research_study_list = search_arxiv_by_id(
            research_study_list=state["related_research_study_list"]
        )
        return {"related_research_study_list": related_research_study_list}

    @create_hypothesis_timed
    def _search_ss_by_id(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        related_research_study_list = search_ss_by_id(
            research_study_list=state["related_research_study_list"]
        )
        return {"related_research_study_list": related_research_study_list}

    @create_hypothesis_timed
    def _retrieve_text_from_url(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        related_research_study_list = retrieve_text_from_url(
            research_study_list=state["related_research_study_list"],
        )
        return {"related_research_study_list": related_research_study_list}

    def select_provider(self, state: CreateHypothesisSubgraphState) -> str:
        if self.paper_provider == "semantic_scholar":
            return "search_ss_by_id"
        else:
            return "search_arxiv_by_id"

    def should_skip_paper_retrieval(self, state: CreateHypothesisSubgraphState) -> str:
        if self.num_retrieve_related_papers <= 0:
            return "evaluate_novelty_and_significance"
        else:
            return "retrieve_related_papers"

    def _evaluate_novelty_and_significance(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, ResearchIdea | list[ResearchStudy]]:
        new_idea_info = state["new_idea_info"]
        evaluation_results = evaluate_novelty_and_significance(
            research_topic=state["research_topic"],
            research_study_list=state["research_study_list"]
            + state.get("related_research_study_list", []),
            new_idea=new_idea_info.idea,
            llm_name=self.llm_mapping.evaluate_novelty_and_significance,
            github_repository_info=state["github_repository_info"],
        )
        new_idea_info.evaluation = evaluation_results
        return {
            "new_idea_info": new_idea_info,
            "related_research_study_list": [],  # Reset the list of related studies.
        }

    def _should_refine_iteration(self, state: CreateHypothesisSubgraphState) -> str:
        if (
            cast(int, state["new_idea_info"].evaluation.novelty_score) >= 9
            and cast(int, state["new_idea_info"].evaluation.significance_score) >= 9
        ):
            return "end"
        elif state["refine_iterations"] < self.refinement_rounds:
            return "regenerate"
        else:
            logger.info("Refinement iterations exceeded, passing.")
            return "end"

    @create_hypothesis_timed
    def _refine_hypothesis(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, ResearchIdea | list[ResearchIdea] | int]:
        refined_idea = refine_hypothesis(
            llm_name=self.llm_mapping.refine_hypothesis,
            research_topic=state["research_topic"],
            evaluated_idea_info=state["new_idea_info"],
            idea_info_history=state["idea_info_history"],
            research_study_list=state["research_study_list"],
            refine_iterations=state["refine_iterations"],
            github_repository_info=state["github_repository_info"],
        )
        idea_info_history = state["idea_info_history"] + [state["new_idea_info"]]
        return {
            "new_idea_info": refined_idea,
            "idea_info_history": idea_info_history,
            "refine_iterations": state["refine_iterations"] + 1,
        }

    def _format_hypothesis(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, ResearchHypothesis | list[ResearchIdea]]:
        idea_info_history = state["idea_info_history"] + [state["new_idea_info"]]
        new_method = ResearchHypothesis(
            method=state["new_idea_info"].idea.to_formatted_json(),
        )
        return {
            "new_method": new_method,
            "idea_info_history": idea_info_history,
        }

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateHypothesisSubgraphState)
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node("generate_hypothesis", self._generate_hypothesis)
        graph_builder.add_node("retrieve_related_papers", self._retrieve_related_papers)
        graph_builder.add_node(
            "search_arxiv_id_from_title", self._search_arxiv_id_from_title
        )
        graph_builder.add_node("search_arxiv_by_id", self._search_arxiv_by_id)
        graph_builder.add_node("search_ss_by_id", self._search_ss_by_id)
        graph_builder.add_node("retrieve_text_from_url", self._retrieve_text_from_url)

        graph_builder.add_node(
            "evaluate_novelty_and_significance", self._evaluate_novelty_and_significance
        )
        graph_builder.add_node("refine_hypothesis", self._refine_hypothesis)
        graph_builder.add_node("format_hypothesis", self._format_hypothesis)

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "generate_hypothesis")
        graph_builder.add_conditional_edges(
            "generate_hypothesis",
            self.should_skip_paper_retrieval,
            {
                "retrieve_related_papers": "retrieve_related_papers",
                "evaluate_novelty_and_significance": "evaluate_novelty_and_significance",
            },
        )
        graph_builder.add_edge("retrieve_related_papers", "search_arxiv_id_from_title")
        graph_builder.add_conditional_edges(
            "search_arxiv_id_from_title",
            self.select_provider,
            {
                "search_arxiv_by_id": "search_arxiv_by_id",
                "search_ss_by_id": "search_ss_by_id",
            },
        )
        graph_builder.add_edge("search_arxiv_by_id", "retrieve_text_from_url")
        graph_builder.add_edge("search_ss_by_id", "retrieve_text_from_url")
        graph_builder.add_edge(
            "retrieve_text_from_url", "evaluate_novelty_and_significance"
        )
        graph_builder.add_conditional_edges(
            "evaluate_novelty_and_significance",
            self._should_refine_iteration,
            {
                "end": "format_hypothesis",
                "regenerate": "refine_hypothesis",
            },
        )
        graph_builder.add_edge("refine_hypothesis", "retrieve_related_papers")
        graph_builder.add_edge("format_hypothesis", END)
        return graph_builder.compile()


def main():
    from airas.services.api_client.api_clients_container import sync_container

    sync_container.wire(modules=[__name__])
    input = create_hypothesis_subgraph_input_data
    result = CreateHypothesisSubgraph(
        refinement_rounds=0,
        num_retrieve_related_papers=0,
    ).run(input)
    print(f"result: {result}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateHypothesisSubgraph: {e}")
        raise
