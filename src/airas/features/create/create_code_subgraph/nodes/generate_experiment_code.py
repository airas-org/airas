import logging

from jinja2 import Environment

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.prompt.generate_experiment_code_prompt import (
    generate_experiment_code_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIParams,
)
from airas.types.research_iteration import ExperimentCode
from airas.types.research_session import ResearchSession
from airas.types.wandb import WandbInfo

logger = logging.getLogger(__name__)


async def generate_experiment_code(
    llm_name: OPENAI_MODEL,
    llm_client: LLMFacadeClient,
    research_session: ResearchSession,
    runner_type: RunnerType,
    wandb_info: WandbInfo | None = None,
    code_validation: tuple[bool, str] | None = None,
) -> ExperimentCode:
    env = Environment()
    template = env.from_string(generate_experiment_code_prompt)

    data = {
        "research_session": research_session,
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "code_validation": code_validation,
        "wandb_info": wandb_info.model_dump() if wandb_info else None,
    }
    messages = template.render(data)

    params = OpenAIParams(reasoning_effort="high")
    output, _ = await llm_client.structured_outputs(
        model_name=llm_name,
        message=messages,
        data_model=ExperimentCode,
        params=params,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_experiment_code.")

    return ExperimentCode(**output)
