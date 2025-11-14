import logging

from jinja2 import Environment
from pydantic import BaseModel, Field

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.prompt.generate_run_config_prompt import (
    generate_run_config_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIParams,
)
from airas.types.research_session import ResearchSession

logger = logging.getLogger(__name__)


class RunConfigOutput(BaseModel):
    run_id: str = Field(..., description="Unique identifier for this run")
    run_config_yaml: str = Field(
        ...,
        description="Complete YAML configuration for this specific experiment run, including model, dataset, training hyperparameters, and optuna search space if applicable",
    )


class RunConfigListOutput(BaseModel):
    run_configs: list[RunConfigOutput] = Field(
        ...,
        description="List of run configurations, one for each experiment run",
    )


async def generate_run_config(
    llm_name: OPENAI_MODEL,
    llm_client: LLMFacadeClient,
    research_session: ResearchSession,
    runner_type: RunnerType,
) -> list[RunConfigOutput]:
    env = Environment()

    template = env.from_string(generate_run_config_prompt)

    data = {
        "research_session": research_session,
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
    }
    messages = template.render(data)

    experiment_runs = research_session.current_iteration.experiment_runs
    logger.info(
        f"Generating run configs for {len(experiment_runs)} experiment runs using LLM..."
    )

    params = OpenAIParams(reasoning_effort="high")
    output, _ = await llm_client.structured_outputs(
        model_name=llm_name,
        message=messages,
        data_model=RunConfigListOutput,
        params=params,
    )

    if output is None:
        raise ValueError("No response from LLM in generate_run_config.")
    output_model = RunConfigListOutput(**output)

    experiment_runs = research_session.current_iteration.experiment_runs

    if len(output_model.run_configs) != len(experiment_runs):
        logger.error(
            f"Generated {len(output_model.run_configs)} configs but have {len(experiment_runs)} experiment runs"
        )
        raise ValueError(
            f"Mismatch: {len(output_model.run_configs)} configs vs {len(experiment_runs)} runs"
        )

    logger.info(f"Successfully generated {len(output_model.run_configs)} run configs")
    return output_model.run_configs
