from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.infra.langchain_client import LangChainClient
from airas.infra.llm_specs import LLM_MODELS
from airas.usecases.analyzers.analyze_experiment_subgraph.prompts.analyze_experiment_prompt import (
    analyze_experiment_prompt,
)

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    analysis_report: str


async def analyze_experiment(
    llm_name: LLM_MODELS,
    langchain_client: LangChainClient,
    research_hypothesis: ResearchHypothesis,
    experimental_design: ExperimentalDesign,
    experiment_code: ExperimentCode,
    experimental_results: ExperimentalResults,
) -> str:
    env = Environment()
    template = env.from_string(analyze_experiment_prompt)

    messages = template.render(
        {
            "research_hypothesis": research_hypothesis,
            "experimental_design": experimental_design,
            "experiment_code": experiment_code,
            "experimental_results": experimental_results,
        }
    )
    output = await langchain_client.structured_outputs(
        message=messages, data_model=LLMOutput, llm_name=llm_name
    )
    if output is None:
        raise ValueError("No response from LLM in analyze_experiment.")

    return output.analysis_report
