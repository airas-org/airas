from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.analyzers.analyze_experiment_subgraph.prompts.analyze_experiment_prompt import (
    analyze_experiment_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_design import ExperimentalDesign
from airas.types.experimental_results import ExperimentalResults
from airas.types.research_hypothesis import ResearchHypothesis

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    analysis_report: str


async def analyze_experiment(
    llm_name: LLM_MODEL,
    llm_client: LLMFacadeClient,
    research_hypothesis: ResearchHypothesis,
    experimental_design: ExperimentalDesign,
    experimental_code: ExperimentCode,
    experimental_results: ExperimentalResults,
) -> str:
    env = Environment()
    template = env.from_string(analyze_experiment_prompt)

    messages = template.render(
        {
            "research_hypothesis": research_hypothesis,
            "experimental_design": experimental_design,
            "experimental_code": experimental_code,
            "experimental_results": experimental_results,
        }
    )
    output, cost = await llm_client.structured_outputs(
        message=messages, data_model=LLMOutput, llm_name=llm_name
    )
    if output is None:
        raise ValueError("No response from LLM in analyze_experiment.")

    return output["analysis_report"]
