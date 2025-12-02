import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.config.llm_config import DEFAULT_NODE_LLMS
from airas.features.generators.generate_experimental_design_subgraph.nodes.generate_experimental_design import (
    generate_experimental_design,
)
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
)
from airas.types.experimental_design import ExperimentalDesign, RunnerConfig
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.check_api_key import check_api_key
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("generate_experimental_design_subgraph")(f)  # noqa: E731


class GenerateExperimentalDesignLLMMapping(BaseModel):
    generate_experimental_design: LLM_MODEL = DEFAULT_NODE_LLMS[
        "generate_experimental_design"
    ]


class GenerateExperimentalDesignSubgraphInputState(TypedDict):
    research_hypothesis: ResearchHypothesis


class GenerateExperimentalDesignSubgraphOutputState(ExecutionTimeState):
    experimental_design: ExperimentalDesign


class GenerateExperimentalDesignState(
    GenerateExperimentalDesignSubgraphInputState,
    GenerateExperimentalDesignSubgraphOutputState,
):
    pass


class GenerateExperimentalDesignSubgraph:
    def __init__(
        self,
        langchain_client: LangChainClient,
        runner_config: RunnerConfig,
        llm_mapping: GenerateExperimentalDesignLLMMapping | None = None,
        num_models_to_use: int = 2,
        num_datasets_to_use: int = 2,
        num_comparative_methods: int = 2,
    ):
        self.langchain_client = langchain_client
        self.llm_mapping = llm_mapping or GenerateExperimentalDesignLLMMapping()
        self.runner_config = runner_config
        self.num_models_to_use = num_models_to_use
        self.num_datasets_to_use = num_datasets_to_use
        self.num_comparative_methods = num_comparative_methods
        check_api_key(llm_api_key_check=True)

    @record_execution_time
    async def _generate_experiment_design(
        self, state: GenerateExperimentalDesignState
    ) -> dict[str, ExperimentalDesign]:
        experimental_design = await generate_experimental_design(
            llm_name=self.llm_mapping.generate_experimental_design,
            llm_client=self.langchain_client,
            research_hypothesis=state["research_hypothesis"],
            runner_config=self.runner_config,
            num_models_to_use=self.num_models_to_use,
            num_datasets_to_use=self.num_datasets_to_use,
            num_comparative_methods=self.num_comparative_methods,
        )

        return {"experimental_design": experimental_design}

    def build_graph(self):
        graph_builder = StateGraph(
            GenerateExperimentalDesignState,
            input_schema=GenerateExperimentalDesignSubgraphInputState,
            output_schema=GenerateExperimentalDesignSubgraphOutputState,
        )
        graph_builder.add_node(
            "generate_experiment_design", self._generate_experiment_design
        )

        graph_builder.add_edge(START, "generate_experiment_design")
        graph_builder.add_edge("generate_experiment_design", END)

        return graph_builder.compile()
