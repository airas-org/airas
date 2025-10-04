import json

from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_experimental_design_subgraph.prompt.generate_experiments_prompt import (
    generate_experiments_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import Experiment, ResearchHypothesis
from airas.utils.save_prompt import save_io_on_github


class ExperimentOutput(BaseModel):
    experiment_id: str
    run_variations: list[str]
    description: str


class LLMOutput(BaseModel):
    experiments: list[ExperimentOutput]
    expected_models: list[str]
    expected_datasets: list[str]


def generate_experiments(
    llm_name: LLM_MODEL,
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    github_repository_info: GitHubRepositoryInfo,
    num_experiments: int = 3,
    feedback_text: str | None = None,
) -> ResearchHypothesis:
    client = LLMFacadeClient(llm_name=llm_name)
    env = Environment()

    template = env.from_string(generate_experiments_prompt)

    data = {
        "new_method": new_method.model_dump(),
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "num_experiments": num_experiments,
        "consistency_feedback": feedback_text,
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(
        message=messages,
        data_model=LLMOutput,
    )
    if output is None:
        raise ValueError("No response from LLM in generate_experiments.")
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="create_experimental_design_subgraph",
        node_name="generate_experiments",
    )

    # Convert LLM output to Experiment objects
    experiments = []
    for exp_output in output["experiments"]:
        experiment = Experiment(
            experiment_id=exp_output["experiment_id"],
            run_variations=exp_output["run_variations"],
            description=exp_output["description"],
        )
        experiments.append(experiment)

    new_method.experimental_design.experiments = experiments
    new_method.experimental_design.expected_models = output["expected_models"]
    new_method.experimental_design.expected_datasets = output["expected_datasets"]
    return new_method
