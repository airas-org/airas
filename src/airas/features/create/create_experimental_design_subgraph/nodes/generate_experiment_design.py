import json
import logging

from jinja2 import Environment
from pydantic import BaseModel, Field

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.data.dataset.language_model_fine_tuning_dataset import (
    LANGUAGE_MODEL_FINE_TUNING_DATASET_LIST,
)
from airas.data.model.language_model import (
    LANGUAGE_MODEL_LIST,
)
from airas.features.create.create_experimental_design_subgraph.prompt.generate_experiment_design_prompt import (
    generate_experiment_design_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_iteration import ExperimentalDesign
from airas.types.research_session import ResearchSession

logger = logging.getLogger(__name__)


class HyperParameter(BaseModel):
    name: str = Field(..., description="Name of the hyperparameter")
    range: str = Field(
        ..., description="Search range (e.g., '0.001-0.01' or '16,32,64')"
    )


class LLMOutput(BaseModel):
    experiment_summary: str
    evaluation_metrics: list[str]
    models_to_use: list[str]
    datasets_to_use: list[str]
    proposed_method: str
    comparative_methods: list[str]
    hyperparameters_to_search: list[HyperParameter]


def generate_experiment_design(
    llm_name: LLM_MODEL,
    llm_client: LLMFacadeClient,
    research_session: ResearchSession,
    runner_type: RunnerType,
    num_models_to_use: int,
    num_datasets_to_use: int,
    num_comparative_methods: int,
) -> ExperimentalDesign:
    env = Environment()

    template = env.from_string(generate_experiment_design_prompt)

    # TODO: Also pass the list of objective functions
    # TODO: Handling cases where selection from a list is mandatory
    data = {
        "research_session": research_session,
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "model_list": json.dumps(LANGUAGE_MODEL_LIST, indent=4, ensure_ascii=False),
        "dataset_list": json.dumps(
            LANGUAGE_MODEL_FINE_TUNING_DATASET_LIST, indent=4, ensure_ascii=False
        ),
        "num_models_to_use": num_models_to_use,
        "num_datasets_to_use": num_datasets_to_use,
        "num_comparative_methods": num_comparative_methods,
    }
    messages = template.render(data)
    output, _ = llm_client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_experiment_design.")

    hyperparameters_dict = {
        hp["name"]: hp["range"] for hp in output["hyperparameters_to_search"]
    }

    primary_metric = research_session.hypothesis.primary_metric
    evaluation_metrics = output["evaluation_metrics"]
    if primary_metric not in evaluation_metrics:
        logger.warning(
            f"Primary metric '{primary_metric}' not found in evaluation_metrics. "
            f"Adding it to the list."
        )
        evaluation_metrics.append(primary_metric)

    return ExperimentalDesign(
        experiment_summary=output["experiment_summary"],
        evaluation_metrics=evaluation_metrics,
        models_to_use=output["models_to_use"],
        datasets_to_use=output["datasets_to_use"],
        proposed_method=output["proposed_method"],
        comparative_methods=output["comparative_methods"],
        hyperparameters_to_search=hyperparameters_dict,
    )
