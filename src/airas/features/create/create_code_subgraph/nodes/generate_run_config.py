import json
import logging

from jinja2 import Environment
from pydantic import BaseModel, Field

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.prompt.generate_run_config_prompt import (
    generate_run_config_prompt,
)
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.utils.save_prompt import save_io_on_github

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


def generate_run_config(
    llm_name: OPENAI_MODEL,
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    github_repository_info: GitHubRepositoryInfo,
) -> ResearchHypothesis:
    client = OpenAIClient(reasoning_effort="high")
    env = Environment()

    template = env.from_string(generate_run_config_prompt)

    data = {
        "new_method": new_method.model_dump(),
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
    }
    messages = template.render(data)

    logger.info(
        f"Generating run configs for {len(new_method.experiment_runs)} experiment runs using LLM..."
    )

    output, _ = client.structured_outputs(
        model_name=llm_name,
        message=messages,
        data_model=RunConfigListOutput,
    )

    if output is None:
        raise ValueError("No response from LLM in generate_run_config.")

    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=2),
        subgraph_name="create_code_subgraph",
        node_name="generate_run_config",
    )

    output_model = RunConfigListOutput(**output)

    try:
        if len(output_model.run_configs) != len(new_method.experiment_runs):
            logger.error(
                f"Generated {len(output_model.run_configs)} configs but have {len(new_method.experiment_runs)} experiment runs"
            )
            raise ValueError(
                f"Mismatch: {len(output_model.run_configs)} configs vs {len(new_method.experiment_runs)} runs"
            )

        config_dict = {
            config.run_id: config.run_config_yaml for config in output_model.run_configs
        }

        for exp_run in new_method.experiment_runs:
            if exp_run.run_id not in config_dict:
                logger.error(f"No config found for run_id: {exp_run.run_id}")
                raise ValueError(f"Missing config for run_id: {exp_run.run_id}")

            exp_run.run_config = config_dict[exp_run.run_id]
            logger.info(f"Assigned run_config to {exp_run.run_id}")

    except Exception as e:
        logger.error(f"Failed to parse run configs: {e}")
        raise

    logger.info(
        f"Successfully generated run configs for all {len(new_method.experiment_runs)} experiments"
    )
    return new_method
