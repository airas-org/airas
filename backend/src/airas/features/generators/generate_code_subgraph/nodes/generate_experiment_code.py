import logging

from jinja2 import Environment

from airas.features.generators.generate_code_subgraph.prompts.generate_experiment_code_prompt import (
    generate_experiment_code_prompt,
)
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS, LLMParams
from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_design import ExperimentalDesign
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.wandb import WandbConfig

logger = logging.getLogger(__name__)


async def generate_experiment_code(
    llm_name: LLM_MODELS,
    llm_client: LangChainClient,
    research_hypothesis: ResearchHypothesis,
    experimental_design: ExperimentalDesign,
    experiment_code: ExperimentCode,
    wandb_config: WandbConfig,
    code_validation: tuple[bool, str] | None = None,
    params: LLMParams | None = None,
) -> ExperimentCode:
    env = Environment()
    template = env.from_string(generate_experiment_code_prompt)

    data = {
        "research_hypothesis": research_hypothesis,
        "experimental_design": experimental_design,
        "experiment_code": experiment_code,
        "code_validation": code_validation,
        "wandb_config": wandb_config.model_dump(),
    }
    messages = template.render(data)

    output = await llm_client.structured_outputs(
        llm_name=llm_name,
        message=messages,
        data_model=ExperimentCode,
        params=params,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_experiment_code.")

    return output
