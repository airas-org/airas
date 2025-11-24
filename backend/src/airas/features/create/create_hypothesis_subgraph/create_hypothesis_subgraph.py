import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
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
from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.services.api_client.qdrant_client import QdrantClient
from airas.services.api_client.semantic_scholar_client import SemanticScholarClient
from airas.types.research_hypothesis import EvaluatedHypothesis, ResearchHypothesis
from airas.types.research_session import ResearchSession
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
    embedding_model: LLM_MODEL = "gemini-embedding-001"


class CreateHypothesisSubgraphInputState(TypedDict):
    research_topic: str
    research_study_list: list[ResearchStudy]


class CreateHypothesisSubgraphHiddenState(TypedDict):
    research_hypothesis: ResearchHypothesis
    related_research_study_list: list[ResearchStudy]
    refine_iterations: int


class CreateHypothesisSubgraphOutputState(TypedDict):
    research_session: ResearchSession
    evaluated_hypothesis_history: list[EvaluatedHypothesis]


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
        qdrant_client: QdrantClient,
        arxiv_client: ArxivClient,
        ss_client: SemanticScholarClient,
        llm_client: LLMFacadeClient,
        llm_mapping: dict[str, str] | CreateHypothesisSubgraphLLMMapping | None = None,
        refinement_rounds: int = 2,
        paper_provider: str = "arxiv",
        num_retrieve_related_papers: int = 10,
    ):
        self.qdrant_client = qdrant_client
        self.arxiv_client = arxiv_client
        self.ss_client = ss_client
        self.llm_client = llm_client
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
    ) -> dict[str, list[EvaluatedHypothesis] | int]:
        return {
            "evaluated_hypothesis_history": [],
            "refine_iterations": 0,
        }

    # TODO: Include the scope of models and datasets within the hypotheses generated.
    @create_hypothesis_timed
    async def _generate_hypothesis(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, ResearchHypothesis]:
        research_hypothesis = await generate_hypothesis(
            llm_name=self.llm_mapping.generate_hypothesis,
            llm_client=self.llm_client,
            research_topic=state["research_topic"],
            research_study_list=state["research_study_list"],
        )
        return {"research_hypothesis": research_hypothesis}

    # TODO: If QDrant doesn't work, consider skipping the paper search or using airas_db.
    @create_hypothesis_timed
    async def _retrieve_related_papers(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        related_research_study_list = []  # Reset the list of related studies for re-execution.
        retrieved_titles = await get_paper_titles_from_qdrant(
            queries=[state["research_hypothesis"].method],
            num_retrieve_paper=self.num_retrieve_related_papers,
            qdrant_client=self.qdrant_client,
            llm_client=self.llm_client,
        )
        retrieved_studies = [
            ResearchStudy(title=title) for title in (retrieved_titles or [])
        ]

        existing_titles = {study.title for study in state["research_study_list"]}
        related_research_study_list = [
            study for study in retrieved_studies if study.title not in existing_titles
        ]
        return {"related_research_study_list": related_research_study_list}

    @create_hypothesis_timed
    async def _search_arxiv_id_from_title(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        related_research_study_list = await search_arxiv_id_from_title(
            llm_name=self.llm_mapping.search_arxiv_id_from_title,
            llm_client=self.llm_client,
            prompt_template=openai_websearch_arxiv_ids_prompt,
            research_study_list=state["related_research_study_list"],
        )
        return {"related_research_study_list": related_research_study_list}

    @create_hypothesis_timed
    def _search_arxiv_by_id(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        related_research_study_list = search_arxiv_by_id(
            arxiv_client=self.arxiv_client,
            research_study_list=state["related_research_study_list"],
        )
        return {"related_research_study_list": related_research_study_list}

    @create_hypothesis_timed
    def _search_ss_by_id(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        related_research_study_list = search_ss_by_id(
            ss_client=self.ss_client,
            research_study_list=state["related_research_study_list"],
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

    async def _evaluate_novelty_and_significance(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, list[EvaluatedHypothesis]]:
        evaluated_hypothesis = await evaluate_novelty_and_significance(
            research_topic=state["research_topic"],
            research_study_list=state["research_study_list"]
            + state.get("related_research_study_list", []),
            research_hypothesis=state["research_hypothesis"],
            llm_name=self.llm_mapping.evaluate_novelty_and_significance,
            llm_client=self.llm_client,
        )
        return {
            "evaluated_hypothesis_history": state["evaluated_hypothesis_history"]
            + [evaluated_hypothesis],
        }

    def _should_refine_iteration(self, state: CreateHypothesisSubgraphState) -> str:
        latest_hypothesis = state["evaluated_hypothesis_history"][-1]
        if (
            cast(int, latest_hypothesis.evaluation.novelty_score) >= 9
            and cast(int, latest_hypothesis.evaluation.significance_score) >= 9
        ):
            return "end"
        elif state["refine_iterations"] < self.refinement_rounds:
            return "regenerate"
        else:
            logger.info("Refinement iterations exceeded, passing.")
            return "end"

    @create_hypothesis_timed
    async def _refine_hypothesis(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, ResearchHypothesis | int]:
        refined_hypothesis = await refine_hypothesis(
            llm_name=self.llm_mapping.refine_hypothesis,
            llm_client=self.llm_client,
            research_topic=state["research_topic"],
            evaluated_hypothesis_history=state["evaluated_hypothesis_history"],
            research_study_list=state["research_study_list"],
        )
        return {
            "research_hypothesis": refined_hypothesis,
            "refine_iterations": state["refine_iterations"] + 1,
        }

    def _format_hypothesis(
        self, state: CreateHypothesisSubgraphState
    ) -> dict[str, ResearchSession]:
        return {
            "research_session": ResearchSession(
                hypothesis=state["evaluated_hypothesis_history"][-1].hypothesis,
            )
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
    from airas.features.create.create_hypothesis_subgraph.input_data import (
        create_hypothesis_subgraph_input_data,
    )
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
