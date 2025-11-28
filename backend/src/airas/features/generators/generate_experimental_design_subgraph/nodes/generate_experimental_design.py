import json
import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.data.dataset.language_model_fine_tuning_dataset import (
    LANGUAGE_MODEL_FINE_TUNING_DATASET_LIST,
)
from airas.data.model.language_model import (
    LANGUAGE_MODEL_LIST,
)
from airas.features.generators.generate_experimental_design_subgraph.prompts.generate_experimental_design_prompt import (
    generate_experimental_design_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.services.api_client.llm_client.openai_client import OpenAIParams
from airas.types.experimental_design import (
    EvaluationMetric,
    ExperimentalDesign,
    MethodConfig,
    RunnerConfig,
)
from airas.types.research_hypothesis import ResearchHypothesis

logger = logging.getLogger(__name__)


class LLMOutput(BaseModel):
    experiment_summary: str
    evaluation_metrics: list[EvaluationMetric]
    models_to_use: list[str]
    datasets_to_use: list[str]
    proposed_method: MethodConfig
    comparative_methods: list[MethodConfig]


async def generate_experimental_design(
    llm_name: LLM_MODEL,
    llm_client: LLMFacadeClient,
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
        "model_list": json.dumps(LANGUAGE_MODEL_LIST, indent=4, ensure_ascii=False),
        "dataset_list": json.dumps(
            LANGUAGE_MODEL_FINE_TUNING_DATASET_LIST, indent=4, ensure_ascii=False
        ),
        "num_models_to_use": num_models_to_use,
        "num_datasets_to_use": num_datasets_to_use,
        "num_comparative_methods": num_comparative_methods,
    }
    messages = template.render(data)
    params = OpenAIParams(reasoning_effort="high")
    output, _ = await llm_client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
        llm_name=llm_name,
        params=params,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_experiment_design.")

    primary_metric = research_hypothesis.primary_metric
    evaluation_metrics = [
        EvaluationMetric(**metric) for metric in output["evaluation_metrics"]
    ]

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

    return ExperimentalDesign(
        experiment_summary=output["experiment_summary"],
        runner_config=runner_config,
        evaluation_metrics=evaluation_metrics,
        models_to_use=output["models_to_use"],
        datasets_to_use=output["datasets_to_use"],
        proposed_method=MethodConfig(**output["proposed_method"]),
        comparative_methods=[
            MethodConfig(**method) for method in output["comparative_methods"]
        ],
    )
