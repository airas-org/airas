import logging
from typing import Literal, cast

from langgraph.graph import END, START, StateGraph
from langgraph.types import Command
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.features.generators.generate_hypothesis_subgraph.nodes.evaluate_novelty_and_significance import (
    evaluate_novelty_and_significance,
)
from airas.features.generators.generate_hypothesis_subgraph.nodes.generate_hypothesis import (
    generate_hypothesis,
)
from airas.features.generators.generate_hypothesis_subgraph.nodes.refine_hypothesis import (
    refine_hypothesis,
)
from airas.features.retrieve.retrieve_paper_subgraph.nodes.get_paper_title_from_qdrant import (
    get_paper_titles_from_qdrant,
)
from airas.features.retrieve.retrieve_paper_subgraph.nodes.retrieve_text_from_url import (
    retrieve_text_from_url,
)
from airas.features.retrieve.retrieve_paper_subgraph.nodes.search_arxiv_id_from_title import (
    search_arxiv_id_from_title,
)
from airas.features.retrieve.retrieve_paper_subgraph.nodes.search_arxiv_info_by_id import (
    search_arxiv_info_by_id,
)
from airas.features.retrieve.retrieve_paper_subgraph.nodes.search_ss_by_id import (
    search_ss_by_id,
)
from airas.features.retrieve.retrieve_paper_subgraph.prompt.openai_websearch_arxiv_ids_prompt import (
    openai_websearch_arxiv_ids_prompt,
)
from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
)
from airas.services.api_client.qdrant_client import QdrantClient
from airas.services.api_client.semantic_scholar_client import SemanticScholarClient
from airas.types.research_hypothesis import EvaluatedHypothesis, ResearchHypothesis
from airas.types.research_study import ResearchStudy
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

recode_execution_time = lambda f: time_node("generate_hypothesis_subgraph")(f)  # noqa: E731


class GenerateHypothesisSubgraphLLMMapping(BaseModel):
    generate_hypothesis: LLM_MODEL = DEFAULT_NODE_LLMS["generate_hypothesis"]
    evaluate_novelty_and_significance: LLM_MODEL = DEFAULT_NODE_LLMS[
        "evaluate_novelty_and_significance"
    ]
    refine_hypothesis: LLM_MODEL = DEFAULT_NODE_LLMS["refine_hypothesis"]
    search_arxiv_id_from_title: LLM_MODEL = DEFAULT_NODE_LLMS[
        "search_arxiv_id_from_title"
    ]
    embedding_model: LLM_MODEL = "gemini-embedding-001"


class GenerateHypothesisSubgraphInputState(TypedDict):
    research_objective: str
    research_study_list: list[ResearchStudy]


class GenerateHypothesisSubgraphOutputState(ExecutionTimeState):
    research_hypothesis: ResearchHypothesis


class GenerateHypothesisSubgraphState(
    GenerateHypothesisSubgraphInputState,
    GenerateHypothesisSubgraphOutputState,
    total=False,
):
    related_research_study_list: list[ResearchStudy]
    refine_iterations: int
    evaluated_hypothesis_history: list[EvaluatedHypothesis]


class GenerateHypothesisSubgraph:
    def __init__(
        self,
        langchain_client: LangChainClient,
        qdrant_client: QdrantClient | None = None,
        arxiv_client: ArxivClient | None = None,
        ss_client: SemanticScholarClient | None = None,
        llm_mapping: dict[str, str]
        | GenerateHypothesisSubgraphLLMMapping
        | None = None,
        refinement_rounds: int = 2,
        paper_provider: str = "arxiv",
        num_retrieve_related_papers: int = 10,
    ):
        self.langchain_client = langchain_client
        self.qdrant_client = qdrant_client
        self.arxiv_client = arxiv_client
        self.ss_client = ss_client
        if llm_mapping is None:
            self.llm_mapping = GenerateHypothesisSubgraphLLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = GenerateHypothesisSubgraphLLMMapping.model_validate(
                    llm_mapping
                )
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, GenerateHypothesisSubgraphLLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or GenerateHypothesisSubgraphLLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.refinement_rounds = refinement_rounds
        self.paper_provider = paper_provider
        self.num_retrieve_related_papers = num_retrieve_related_papers
        check_api_key(llm_api_key_check=True)

    @recode_execution_time
    def _initialize(
        self, state: GenerateHypothesisSubgraphState
    ) -> dict[str, list[EvaluatedHypothesis] | int]:
        return {
            "evaluated_hypothesis_history": [],
            "refine_iterations": 0,
        }

    # TODO: Include the scope of models and datasets within the hypotheses generated.
    @recode_execution_time
    async def _generate_hypothesis(
        self, state: GenerateHypothesisSubgraphState
    ) -> Command[
        Literal["retrieve_related_papers", "evaluate_novelty_and_significance"]
    ]:
        research_hypothesis = await generate_hypothesis(
            llm_name=self.llm_mapping.generate_hypothesis,
            llm_client=self.langchain_client,
            research_objective=state["research_objective"],
            research_study_list=state["research_study_list"],
        )

        goto: Literal["retrieve_related_papers", "evaluate_novelty_and_significance"]
        if self.num_retrieve_related_papers <= 0:
            goto = "evaluate_novelty_and_significance"
        else:
            goto = "retrieve_related_papers"

        return Command(update={"research_hypothesis": research_hypothesis}, goto=goto)

    @recode_execution_time
    async def _retrieve_related_papers(
        self, state: GenerateHypothesisSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        if self.qdrant_client is None:
            raise ValueError("qdrant_client is required for retrieving related papers")
        related_research_study_list = []  # Reset the list of related studies for re-execution.
        retrieved_titles = await get_paper_titles_from_qdrant(
            queries=[state["research_hypothesis"].method],  # type: ignore[typeddict-item]
            num_retrieve_paper=self.num_retrieve_related_papers,
            qdrant_client=self.qdrant_client,
            llm_client=self.langchain_client,
        )
        retrieved_studies = [
            ResearchStudy(title=title) for title in (retrieved_titles or [])
        ]

        existing_titles = {study.title for study in state["research_study_list"]}
        related_research_study_list = [
            study for study in retrieved_studies if study.title not in existing_titles
        ]
        return {"related_research_study_list": related_research_study_list}

    @recode_execution_time
    async def _search_arxiv_id_from_title(
        self, state: GenerateHypothesisSubgraphState
    ) -> Command[Literal["search_arxiv_by_id", "search_ss_by_id"]]:
        related_research_study_list = await search_arxiv_id_from_title(
            llm_name=self.llm_mapping.search_arxiv_id_from_title,
            llm_client=self.langchain_client,
            prompt_template=openai_websearch_arxiv_ids_prompt,
            research_study_list=state["related_research_study_list"],
        )

        goto: Literal["search_arxiv_by_id", "search_ss_by_id"]
        if self.paper_provider == "semantic_scholar":
            goto = "search_ss_by_id"
        else:
            goto = "search_arxiv_by_id"

        return Command(
            update={"related_research_study_list": related_research_study_list},
            goto=goto,
        )

    @recode_execution_time
    def _search_arxiv_by_id(
        self, state: GenerateHypothesisSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        if self.arxiv_client is None:
            raise ValueError("arxiv_client is required for searching arxiv by ID")
        related_research_study_list = search_arxiv_info_by_id(
            arxiv_client=self.arxiv_client,
            research_study_list=state["related_research_study_list"],
        )
        return {"related_research_study_list": related_research_study_list}

    @recode_execution_time
    def _search_ss_by_id(
        self, state: GenerateHypothesisSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        if self.ss_client is None:
            raise ValueError(
                "ss_client is required for searching semantic scholar by ID"
            )
        related_research_study_list = search_ss_by_id(
            ss_client=self.ss_client,
            research_study_list=state["related_research_study_list"],
        )
        return {"related_research_study_list": related_research_study_list}

    @recode_execution_time
    def _retrieve_text_from_url(
        self, state: GenerateHypothesisSubgraphState
    ) -> dict[str, list[ResearchStudy]]:
        related_research_study_list = retrieve_text_from_url(
            research_study_list=state["related_research_study_list"],
        )
        return {"related_research_study_list": related_research_study_list}

    async def _evaluate_novelty_and_significance(
        self, state: GenerateHypothesisSubgraphState
    ) -> Command[Literal["finalize_hypothesis", "refine_hypothesis"]]:
        evaluated_hypothesis = await evaluate_novelty_and_significance(
            research_objective=state["research_objective"],
            research_study_list=state["research_study_list"]
            + state.get("related_research_study_list", []),
            research_hypothesis=state["research_hypothesis"],  # type: ignore[typeddict-item]
            llm_name=self.llm_mapping.evaluate_novelty_and_significance,
            llm_client=self.langchain_client,
        )

        goto: Literal["finalize_hypothesis", "refine_hypothesis"]
        if (
            cast(int, evaluated_hypothesis.evaluation.novelty_score) >= 9
            and cast(int, evaluated_hypothesis.evaluation.significance_score) >= 9
        ):
            goto = "finalize_hypothesis"
        elif state["refine_iterations"] < self.refinement_rounds:
            goto = "refine_hypothesis"
        else:
            logger.info("Refinement iterations exceeded, passing.")
            goto = "finalize_hypothesis"

        return Command(
            update={
                "evaluated_hypothesis_history": state["evaluated_hypothesis_history"]
                + [evaluated_hypothesis],
            },
            goto=goto,
        )

    @recode_execution_time
    async def _refine_hypothesis(
        self, state: GenerateHypothesisSubgraphState
    ) -> Command[
        Literal["retrieve_related_papers", "evaluate_novelty_and_significance"]
    ]:
        refined_hypothesis = await refine_hypothesis(
            llm_name=self.llm_mapping.refine_hypothesis,
            llm_client=self.langchain_client,
            research_objective=state["research_objective"],
            evaluated_hypothesis_history=state["evaluated_hypothesis_history"],
            research_study_list=state["research_study_list"],
        )

        goto: Literal["retrieve_related_papers", "evaluate_novelty_and_significance"]
        if self.num_retrieve_related_papers <= 0:
            goto = "evaluate_novelty_and_significance"
        else:
            goto = "retrieve_related_papers"

        return Command(
            update={
                "research_hypothesis": refined_hypothesis,
                "refine_iterations": state["refine_iterations"] + 1,
            },
            goto=goto,
        )

    def _finalize_hypothesis(
        self, state: GenerateHypothesisSubgraphState
    ) -> dict[str, ResearchHypothesis]:
        return {
            "research_hypothesis": state["evaluated_hypothesis_history"][-1].hypothesis,
        }

    def build_graph(self):
        graph_builder = StateGraph(
            GenerateHypothesisSubgraphState,
            input_schema=GenerateHypothesisSubgraphInputState,
            output_schema=GenerateHypothesisSubgraphOutputState,
        )
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
        graph_builder.add_node("finalize_hypothesis", self._finalize_hypothesis)

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "generate_hypothesis")
        graph_builder.add_edge("retrieve_related_papers", "search_arxiv_id_from_title")
        graph_builder.add_edge("search_arxiv_by_id", "retrieve_text_from_url")
        graph_builder.add_edge("search_ss_by_id", "retrieve_text_from_url")
        graph_builder.add_edge(
            "retrieve_text_from_url", "evaluate_novelty_and_significance"
        )
        graph_builder.add_edge("finalize_hypothesis", END)

        return graph_builder.compile()
