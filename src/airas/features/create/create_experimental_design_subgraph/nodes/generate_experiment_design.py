import json

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
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ExperimentalDesign, ResearchHypothesis
from airas.utils.save_prompt import save_io_on_github


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
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    num_models_to_use: int,
    num_datasets_to_use: int,
    num_comparative_methods: int,
    github_repository_info: GitHubRepositoryInfo,
    hypothesis_versions: list[ResearchHypothesis] | None = None,
) -> ResearchHypothesis:
    client = LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(generate_experiment_design_prompt)

    data = {
        "new_method": new_method.model_dump(),
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "model_list": json.dumps(LANGUAGE_MODEL_LIST, indent=4, ensure_ascii=False),
        "dataset_list": json.dumps(
            LANGUAGE_MODEL_FINE_TUNING_DATASET_LIST, indent=4, ensure_ascii=False
        ),
        "num_models_to_use": num_models_to_use,
        "num_datasets_to_use": num_datasets_to_use,
        "num_comparative_methods": num_comparative_methods,
        "hypothesis_versions": [h.model_dump() for h in (hypothesis_versions or [])],
    }
    messages = template.render(data)
    output, _ = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_experiment_details.")
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="create_experimental_design_subgraph",
        node_name="generate_experiment_details",
        llm_name=llm_name,
    )

    hyperparameters_dict = {
        hp["name"]: hp["range"] for hp in output["hyperparameters_to_search"]
    }

    new_method.experimental_design = ExperimentalDesign(
        experiment_summary=output["experiment_summary"],
        evaluation_metrics=output["evaluation_metrics"],
        models_to_use=output["models_to_use"],
        datasets_to_use=output["datasets_to_use"],
        proposed_method=output["proposed_method"],
        comparative_methods=output["comparative_methods"],
        hyperparameters_to_search=hyperparameters_dict,
    )
    return new_method
