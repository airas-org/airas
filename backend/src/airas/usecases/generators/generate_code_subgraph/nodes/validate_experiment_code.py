from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.wandb import WandbConfig
from airas.infra.langchain_client import LangChainClient
from airas.infra.llm_specs import LLM_MODELS, LLMParams
from airas.usecases.generators.generate_code_subgraph.prompts.validate_experiment_code_prompt import (
    validate_experiment_code_prompt,
)

logger = getLogger(__name__)


class ValidationOutput(BaseModel):
    is_code_ready: bool
    code_issue: str


async def validate_experiment_code(
    llm_name: LLM_MODELS,
    llm_client: LangChainClient,
    research_hypothesis: ResearchHypothesis,
    experimental_design: ExperimentalDesign,
    experiment_code: ExperimentCode,
    wandb_config: WandbConfig,
    prompt_template: str = validate_experiment_code_prompt,
    params: LLMParams | None = None,
) -> tuple[bool, str]:
    env = Environment()
    template = env.from_string(prompt_template)

    messages = template.render(
        {
            "research_hypothesis": research_hypothesis,
            "experimental_design": experimental_design,
            "experiment_code": experiment_code,
            "wandb_config": wandb_config.model_dump(),
        }
    )

    output = await llm_client.structured_outputs(
        llm_name=llm_name,
        message=messages,
        data_model=ValidationOutput,
        params=params,
    )

    if output is None:
        logger.error(
            "No response from LLM in validate_experiment_code. Defaulting to False."
        )
        return False, ""

    return output.is_code_ready, output.code_issue
