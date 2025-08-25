import json
import logging
from typing import cast

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.core.base import BaseSubgraph
from airas.features.create.create_method_subgraph.input_data import (
    create_method_subgraph_input_data,
)
from airas.features.create.create_method_subgraph_v2.nodes.evaluate_novelty_and_significance import (
    evaluate_novelty_and_significance,
    parse_new_idea_info,
)
from airas.features.create.create_method_subgraph_v2.nodes.generate_idea_and_research_summary import (
    generate_idea_and_research_summary,
)
from airas.features.create.create_method_subgraph_v2.nodes.refine_idea_and_research_summary import (
    refine_idea_and_research_summary,
)
from airas.features.create.create_method_subgraph_v2.types import (
    ResearchIdea,
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
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

create_method_timed = lambda f: time_node("create_method_subgraph")(f)  # noqa: E731


class CreateMethodV2LLMMapping(BaseModel):
    generate_idea_and_research_summary: LLM_MODEL = DEFAULT_NODE_LLMS[
        "generate_idea_and_research_summary"
    ]
    evaluate_novelty_and_significance: LLM_MODEL = DEFAULT_NODE_LLMS[
        "evaluate_novelty_and_significance"
    ]
    refine_idea_and_research_summary: LLM_MODEL = DEFAULT_NODE_LLMS[
        "refine_idea_and_research_summary"
    ]
    search_arxiv_id_from_title: LLM_MODEL = DEFAULT_NODE_LLMS[
        "search_arxiv_id_from_title"
    ]


class CreateMethodSubgraphV2InputState(TypedDict):
    research_topic: str
    research_study_list: list[ResearchStudy]


class CreateMethodSubgraphV2HiddenState(TypedDict):
    new_idea_info: ResearchIdea
    idea_info_history: list[ResearchIdea]
    related_research_study_list: list[ResearchStudy]
    refine_iterations: int


class CreateMethodSubgraphV2OutputState(TypedDict):
    new_method: ResearchHypothesis


class CreateMethodSubgraphV2State(
    CreateMethodSubgraphV2InputState,
    CreateMethodSubgraphV2HiddenState,
    CreateMethodSubgraphV2OutputState,
    ExecutionTimeState,
):
    pass


class CreateMethodSubgraphV2(BaseSubgraph):
    InputState = CreateMethodSubgraphV2InputState
    OutputState = CreateMethodSubgraphV2OutputState

    def __init__(
        self,
        llm_mapping: dict[str, str] | CreateMethodV2LLMMapping | None = None,
        refine_iterations: int = 2,
        paper_provider: str = "arxiv",
    ):
        if llm_mapping is None:
            self.llm_mapping = CreateMethodV2LLMMapping()
        elif isinstance(llm_mapping, dict):
            try:
                self.llm_mapping = CreateMethodV2LLMMapping.model_validate(llm_mapping)
            except Exception as e:
                raise TypeError(
                    f"Invalid llm_mapping values. Must contain valid LLM model names. Error: {e}"
                ) from e
        elif isinstance(llm_mapping, CreateMethodV2LLMMapping):
            self.llm_mapping = llm_mapping
        else:
            raise TypeError(
                f"llm_mapping must be None, dict[str, str], or CreateMethodV2LLMMapping, "
                f"but got {type(llm_mapping)}"
            )
        self.refine_iterations = refine_iterations
        self.paper_provider = paper_provider
        check_api_key(llm_api_key_check=True)

    @create_method_timed
    def _initialize(self, state: CreateMethodSubgraphV2State) -> dict:
        """Initialize the subgraph state with input data"""
        return {
            "idea_info_history": [],
            "refine_iterations": 0,
        }

    # アイデア生成
    @create_method_timed
    def _generate_ide_and_research_summary(
        self, state: CreateMethodSubgraphV2State
    ) -> dict:
        new_idea = generate_idea_and_research_summary(
            llm_name=self.llm_mapping.generate_idea_and_research_summary,
            research_topic=state["research_topic"],
            research_study_list=state["research_study_list"],
        )
        new_idea_info = {}
        new_idea_info["idea"] = new_idea
        return {"new_idea_info": new_idea_info}

    # 関連論文のタイトル
    @create_method_timed
    def _retrieve_related_papers(self, state: CreateMethodSubgraphV2State) -> dict:
        related_paper_title_list = get_paper_titles_from_qdrant(
            queries=[state["new_idea_info"]["idea"].methods],
            num_retrieve_paper=15,
        )
        related_research_study_list = [
            ResearchStudy(title=title) for title in (related_paper_title_list or [])
        ]
        # research_study_listに含まれているものは削除
        existing_titles = {study.title for study in state["research_study_list"]}
        related_research_study_list = [
            study
            for study in related_research_study_list
            if study.title not in existing_titles
        ]
        return {"related_research_study_list": related_research_study_list}

    @create_method_timed
    def _search_arxiv_id_from_title(
        self, state: CreateMethodSubgraphV2State
    ) -> dict[str, list[ResearchStudy]]:
        related_research_study_list = state["related_research_study_list"]

        related_research_study_list = search_arxiv_id_from_title(
            llm_name=self.llm_mapping.search_arxiv_id_from_title,
            prompt_template=openai_websearch_arxiv_ids_prompt,
            research_study_list=related_research_study_list,
        )
        return {"related_research_study_list": related_research_study_list}

    @create_method_timed
    def _search_arxiv_by_id(
        self, state: CreateMethodSubgraphV2State
    ) -> dict[str, list[ResearchStudy]]:
        related_research_study_list = state["related_research_study_list"]
        related_research_study_list = search_arxiv_by_id(related_research_study_list)
        return {"related_research_study_list": related_research_study_list}

    @create_method_timed
    def _search_ss_by_id(
        self, state: CreateMethodSubgraphV2State
    ) -> dict[str, list[ResearchStudy]]:
        related_research_study_list = state["related_research_study_list"]
        related_research_study_list = search_ss_by_id(related_research_study_list)
        return {"related_research_study_list": related_research_study_list}

    @create_method_timed
    def _retrieve_text_from_url(
        self, state: CreateMethodSubgraphV2State
    ) -> dict[str, list[ResearchStudy]]:
        related_research_study_list = state["related_research_study_list"]
        related_research_study_list = retrieve_text_from_url(
            research_study_list=related_research_study_list,
        )
        return {"related_research_study_list": related_research_study_list}

    def select_provider(self, state: CreateMethodSubgraphV2State) -> str:
        if self.paper_provider == "semantic_scholar":
            return "search_ss_by_id"
        else:
            return "search_arxiv_by_id"

    # 新規性と重要性の10段階評価
    def _evaluate_novelty_and_significance(
        self, state: CreateMethodSubgraphV2State
    ) -> dict:
        research_study_list = state["research_study_list"]
        related_research_study_list = state["related_research_study_list"]
        new_idea_info = state["new_idea_info"]
        evaluation_results = evaluate_novelty_and_significance(
            research_topic=state["research_topic"],
            research_study_list=research_study_list + related_research_study_list,
            new_idea=new_idea_info["idea"],
            llm_name=self.llm_mapping.evaluate_novelty_and_significance,
        )
        # related_research_study_listを空にする
        new_idea_info["evaluate"] = evaluation_results
        return {
            "new_idea_info": new_idea_info,
            "related_research_study_list": [],
        }

    # スコアを判定する関数
    def _evaluate_score(self, state: CreateMethodSubgraphV2State) -> str:
        if (
            cast(int, state["new_idea_info"]["evaluate"].novelty_score) >= 8
            and cast(int, state["new_idea_info"]["evaluate"].significance_score) >= 8
        ):
            return "end"
        elif state["refine_iterations"] < self.refine_iterations:
            state["refine_iterations"] += 1
            return "regenerate"
        else:
            logger.info("Refinement iterations exceeded, passing.")
            return "end"

    # アイデアの再生成
    @create_method_timed
    def _refine_idea_and_research_summary(
        self, state: CreateMethodSubgraphV2State
    ) -> dict:
        new_idea, idea_info_history = refine_idea_and_research_summary(
            llm_name=self.llm_mapping.refine_idea_and_research_summary,
            research_topic=state["research_topic"],
            evaluated_idea_info=state["new_idea_info"],
            research_study_list=state["research_study_list"],
            idea_info_history=state["idea_info_history"],
        )
        return {
            "new_idea": new_idea,
            "idea_info_history": idea_info_history,
        }

    def _format_method(self, state: CreateMethodSubgraphV2State) -> dict:
        new_method = ResearchHypothesis(
            method=parse_new_idea_info(state["new_idea_info"]["idea"]),
        )
        return {"new_method": new_method}

    def build_graph(self) -> CompiledGraph:
        graph_builder = StateGraph(CreateMethodSubgraphV2State)
        graph_builder.add_node("initialize", self._initialize)
        graph_builder.add_node(
            "generate_ide_and_research_summary", self._generate_ide_and_research_summary
        )
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
        graph_builder.add_node("refine_idea", self._refine_idea_and_research_summary)
        graph_builder.add_node("format_method", self._format_method)

        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "generate_ide_and_research_summary")
        graph_builder.add_edge(
            "generate_ide_and_research_summary", "retrieve_related_papers"
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
            self._evaluate_score,
            {
                "end": "format_method",
                "regenerate": "refine_idea",
            },
        )
        graph_builder.add_edge("refine_idea", "retrieve_related_papers")
        graph_builder.add_edge("format_method", END)
        return graph_builder.compile()


def main():
    input = create_method_subgraph_input_data
    result = CreateMethodSubgraphV2().run(input)
    print(f"result: {json.dumps(result, indent=2)}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error(f"Error running CreateMethodSubgraph: {e}")
        raise
