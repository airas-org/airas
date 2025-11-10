from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.create.create_code_subgraph.prompt.validate_experiment_code_prompt import (
    validate_experiment_code_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_session import ResearchSession
from airas.types.wandb import WandbInfo

logger = getLogger(__name__)


class ValidationOutput(BaseModel):
    is_code_ready: bool
    code_issue: str


def validate_experiment_code(
    llm_name: LLM_MODEL,
    research_session: ResearchSession,
    llm_client: LLMFacadeClient,
    wandb_info: WandbInfo | None = None,
    prompt_template: str = validate_experiment_code_prompt,
) -> tuple[bool, str]:
    env = Environment()
    template = env.from_string(prompt_template)

    messages = template.render(
        {
            "research_session": research_session,
            "wandb_info": wandb_info.model_dump() if wandb_info else None,
        }
    )
    output, _ = llm_client.structured_outputs(
        message=messages, data_model=ValidationOutput, llm_name=llm_name
    )

    if output is None:
        logger.error(
            "No response from LLM in validate_experiment_code. Defaulting to False."
        )
        return False, ""

    return output["is_code_ready"], output["code_issue"]
