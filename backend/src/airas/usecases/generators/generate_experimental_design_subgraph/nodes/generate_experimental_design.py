import json
import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.core.llm_config import NodeLLMConfig
from airas.core.types.experimental_design import (
    EvaluationMetric,
    ExperimentalDesign,
    MethodConfig,
    RunnerConfig,
)
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.infra.langchain_client import LangChainClient
from airas.resources.datasets.prompt_engineering_datasets import (
    PROMPT_ENGINEERING_DATASETS,
)
from airas.resources.models.lm_api_models import LM_API_MODELS
from airas.usecases.generators.generate_experimental_design_subgraph.prompts.generate_experimental_design_prompt import (
    generate_experimental_design_prompt,
)

logger = logging.getLogger(__name__)


class LLMOutput(BaseModel):
    experiment_summary: str
    evaluation_metrics: list[EvaluationMetric]
    models_to_use: list[str]
    datasets_to_use: list[str]
    proposed_method: MethodConfig
    comparative_methods: list[MethodConfig]


async def generate_experimental_design(
    llm_config: NodeLLMConfig,
    llm_client: LangChainClient,
    research_hypothesis: ResearchHypothesis,
    runner_config: RunnerConfig,
    num_models_to_use: int,
    num_datasets_to_use: int,
    num_comparative_methods: int,
) -> ExperimentalDesign:
    env = Environment()

    template = env.from_string(generate_experimental_design_prompt)

    # TODO: Also pass the list of objective functions
    # TODO: Handling cases where selection from a list is mandatory
    data = {
        "research_hypothesis": research_hypothesis,
        "runner_config": runner_config,
        "model_list": json.dumps(LM_API_MODELS, indent=4, ensure_ascii=False),
        "dataset_list": json.dumps(
            PROMPT_ENGINEERING_DATASETS, indent=4, ensure_ascii=False
        ),
        "num_models_to_use": num_models_to_use,
        "num_datasets_to_use": num_datasets_to_use,
        "num_comparative_methods": num_comparative_methods,
    }
    messages = template.render(data)
    output = await llm_client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
        llm_name=llm_config.llm_name,
        params=llm_config.params,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_experiment_design.")

    primary_metric = research_hypothesis.primary_metric
    evaluation_metrics = output.evaluation_metrics

    if primary_metric not in {metric.name for metric in evaluation_metrics}:
        logger.warning(
            f"Primary metric '{primary_metric}' not found in evaluation_metrics. "
            f"Adding it to the list."
        )
        evaluation_metrics.append(
            EvaluationMetric(
                name=primary_metric,
                description=f"Primary metric as specified in hypothesis: {primary_metric}",
            )
        )

    models_to_use = output.models_to_use
    datasets_to_use = output.datasets_to_use
    comparative_methods = output.comparative_methods

    if len(models_to_use) > num_models_to_use:
        discarded_models = models_to_use[num_models_to_use:]
        logger.warning(
            f"LLM generated {len(models_to_use)} models but {num_models_to_use} were requested. "
            f"Truncating to first {num_models_to_use}. "
            f"Discarded models: {discarded_models}"
        )
        models_to_use = models_to_use[:num_models_to_use]

    if len(datasets_to_use) > num_datasets_to_use:
        discarded_datasets = datasets_to_use[num_datasets_to_use:]
        logger.warning(
            f"LLM generated {len(datasets_to_use)} datasets but {num_datasets_to_use} were requested. "
            f"Truncating to first {num_datasets_to_use}. "
            f"Discarded datasets: {discarded_datasets}"
        )
        datasets_to_use = datasets_to_use[:num_datasets_to_use]

    if len(comparative_methods) > num_comparative_methods:
        discarded_comparative_methods = comparative_methods[num_comparative_methods:]
        logger.warning(
            f"LLM generated {len(comparative_methods)} comparative methods but {num_comparative_methods} were requested. "
            f"Truncating to first {num_comparative_methods}. "
            f"Discarded comparative methods: {discarded_comparative_methods}"
        )
        comparative_methods = comparative_methods[:num_comparative_methods]

    return ExperimentalDesign(
        experiment_summary=output.experiment_summary,
        runner_config=runner_config,
        evaluation_metrics=evaluation_metrics,
        models_to_use=models_to_use,
        datasets_to_use=datasets_to_use,
        proposed_method=output.proposed_method,
        comparative_methods=comparative_methods,
    )
