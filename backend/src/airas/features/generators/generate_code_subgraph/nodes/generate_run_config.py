import logging
import re

from jinja2 import Environment
from pydantic import BaseModel, Field

from airas.features.generators.generate_code_subgraph.prompts.generate_run_config_prompt import (
    generate_run_config_prompt,
)
from airas.services.api_client.langchain_client import LangChainClient
from airas.services.api_client.llm_specs import LLM_MODELS, LLMParams
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
    llm_name: LLM_MODELS,
    llm_client: LangChainClient,
    research_hypothesis: ResearchHypothesis,
    experimental_design: ExperimentalDesign,
    params: LLMParams | None = None,
) -> dict[str, str]:
    env = Environment()
    template = env.from_string(generate_run_config_prompt)

    data = {
        "research_hypothesis": research_hypothesis,
        "experimental_design": experimental_design,
    }
    messages = template.render(data)

    logger.info("Generating run configs using LLM...")

    output, _ = await llm_client.structured_outputs(
        llm_name=llm_name,
        message=messages,
        data_model=RunConfigListOutput,
        params=params,
    )

    if output is None:
        raise ValueError("No response from LLM in generate_run_config.")

    num_comparative = len(experimental_design.comparative_methods)
    required_methods = {"proposed"} | {
        f"comparative-{i + 1}" for i in range(num_comparative)
    }
    sorted_methods = sorted(required_methods, key=len, reverse=True)

    # Create regex pattern: (method1|method2|method3)(?:-([^-]+(?:-[^-]+)?))?
    # The suffix (model-dataset) part is optional for cases where models/datasets are empty.
    # It is restricted to one or two hyphen-separated components to avoid greedy matching.
    pattern = re.compile(
        f"({'|'.join(re.escape(m) for m in sorted_methods)})(?:-([^-]+(?:-[^-]+)?))?"
    )

    # Group by (model-dataset) suffix
    groups: dict[str, dict[str, RunConfigOutput]] = {}
    for config in output.run_configs:
        if match := pattern.match(config.run_id):
            method = match.group(1)
            suffix = match.group(2) or ""  # Empty string if no suffix
            groups.setdefault(suffix, {})[method] = config
        else:
            logger.warning(f"Skipping unrecognized run_id: {config.run_id}")

    valid_configs: list = []
    for suffix, methods_map in groups.items():
        if set(methods_map.keys()) == required_methods:
            valid_configs.extend(methods_map.values())
        else:
            missing = required_methods - set(methods_map.keys())
            logger.warning(f"Skipping incomplete set '{suffix}': missing {missing}")

    num_models = len(experimental_design.models_to_use) or 1
    num_datasets = len(experimental_design.datasets_to_use) or 1
    expected = num_models * num_datasets * len(required_methods)
    logger.info(f"Kept {len(valid_configs)} configs (expected: {expected})")

    return {cfg.run_id: cfg.run_config_yaml for cfg in valid_configs}
