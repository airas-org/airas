import json

from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_experimental_design_subgraph.dataset_list import (
    DATASET_LIST,
)
from airas.features.create.create_experimental_design_subgraph.model_list import (
    MODEL_LIST,
)
from airas.features.create.create_experimental_design_subgraph.prompt.generate_experiment_details_prompt import (
    generate_experiment_details_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ExperimentalDesign, ResearchHypothesis
from airas.utils.save_prompt import save_io_on_github


class LLMOutput(BaseModel):
    experiment_summary: str
    evaluation_metrics: list[str]
    models_to_use: list[str]
    datasets_to_use: list[str]
    new_method: str
    comparative_methods: list[str]
    hyperparameters_to_search: list[str]


def generate_experiment_details(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    num_models_to_use: int,
    num_datasets_to_use: int,
    num_comparative_methods: int,
    github_repository_info: GitHubRepositoryInfo,
) -> ResearchHypothesis:
    client = LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(generate_experiment_details_prompt)

    data = {
        "new_method": new_method.model_dump(),
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "model_list": json.dumps(MODEL_LIST, indent=4, ensure_ascii=False),
        "dataset_list": json.dumps(DATASET_LIST, indent=4, ensure_ascii=False),
        "num_models_to_use": num_models_to_use,
        "num_datasets_to_use": num_datasets_to_use,
        "num_comparative_methods": num_comparative_methods,
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
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
    )

    # Convert LLM output to Experiment objects
    new_method.experimental_design = ExperimentalDesign(
        experiment_summary=output["experiment_summary"],
        evaluation_metrics=output["evaluation_metrics"],
        models_to_use=output["models_to_use"],
        datasets_to_use=output["datasets_to_use"],
        new_method=output["new_method"],
        comparative_methods=output["comparative_methods"],
        hyperparameters_to_search=output["hyperparameters_to_search"],
    )
    return new_method
