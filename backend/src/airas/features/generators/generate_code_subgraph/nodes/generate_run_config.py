import logging

from jinja2 import Environment
from pydantic import BaseModel, Field

from airas.features.generators.generate_code_subgraph.prompts.generate_run_config_prompt import (
    generate_run_config_prompt,
)
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIParams,
)
from airas.types.experimental_design import ExperimentalDesign
from airas.types.research_hypothesis import ResearchHypothesis

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
    llm_client: LangChainClient,
    research_hypothesis: ResearchHypothesis,
    experimental_design: ExperimentalDesign,
) -> dict[str, str]:
    env = Environment()
    template = env.from_string(generate_run_config_prompt)

    data = {
        "research_hypothesis": research_hypothesis,
        "experimental_design": experimental_design,
    }
    messages = template.render(data)

    logger.info("Generating run configs using LLM...")

    params = OpenAIParams(reasoning_effort="high")
    output, _ = await llm_client.structured_outputs(
        llm_name=llm_name,
        message=messages,
        data_model=RunConfigListOutput,
        params=params,
    )

    if output is None:
        raise ValueError("No response from LLM in generate_run_config.")
    run_configs_dict = {cfg.run_id: cfg.run_config_yaml for cfg in output.run_configs}

    logger.info(f"Successfully generated {len(run_configs_dict)} run configs")
    return run_configs_dict
