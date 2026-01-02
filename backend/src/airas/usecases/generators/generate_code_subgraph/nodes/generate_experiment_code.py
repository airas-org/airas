import logging

from jinja2 import Environment

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.wandb import WandbConfig
from airas.infra.langchain_client import LangChainClient
from airas.infra.llm_specs import LLM_MODELS, LLMParams
from airas.usecases.generators.generate_code_subgraph.prompts.generate_experiment_code_prompt import (
    generate_experiment_code_prompt,
)

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
