from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.generators.generate_code_subgraph.prompts.validate_experiment_code_prompt import (
    validate_experiment_code_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIParams,
)
from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_design import ExperimentalDesign
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.wandb import WandbConfig

logger = getLogger(__name__)


class ValidationOutput(BaseModel):
    is_code_ready: bool
    code_issue: str


async def validate_experiment_code(
    llm_name: OPENAI_MODEL,
    llm_client: LLMFacadeClient,
    research_hypothesis: ResearchHypothesis,
    experimental_design: ExperimentalDesign,
    experiment_code: ExperimentCode,
    wandb_config: WandbConfig,
    prompt_template: str = validate_experiment_code_prompt,
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

    params = OpenAIParams(reasoning_effort="high")
    output, _ = await llm_client.structured_outputs(
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

    return output["is_code_ready"], output["code_issue"]
