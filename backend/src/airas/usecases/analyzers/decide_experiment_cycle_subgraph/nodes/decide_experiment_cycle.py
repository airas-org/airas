import logging

from jinja2 import Environment

from airas.core.llm_config import NodeLLMConfig
from airas.core.types.experiment_history import (
    ExperimentCycleDecision,
    ExperimentHistory,
)
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.infra.langchain_client import LangChainClient
from airas.usecases.analyzers.decide_experiment_cycle_subgraph.prompts.decide_experiment_cycle_prompt import (
    decide_experiment_cycle_prompt,
)

logger = logging.getLogger(__name__)


async def decide_experiment_cycle(
    llm_config: NodeLLMConfig,
    llm_client: LangChainClient,
    research_hypothesis: ResearchHypothesis,
    experiment_history: ExperimentHistory,
) -> ExperimentCycleDecision:
    env = Environment()

    template = env.from_string(decide_experiment_cycle_prompt)

    data = {
        "research_hypothesis": research_hypothesis,
        "experiment_history": experiment_history,
    }
    messages = template.render(data)
    output = await llm_client.structured_outputs(
        message=messages,
        data_model=ExperimentCycleDecision,
        llm_name=llm_config.llm_name,
        params=llm_config.params,
    )
    if output is None:
        raise ValueError("No response from LLM in decide_experiment_cycle.")

    return output
