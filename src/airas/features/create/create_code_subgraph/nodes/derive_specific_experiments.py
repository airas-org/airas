import json

from jinja2 import Environment

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.prompt.derive_specific_experiments_prompt import (
    derive_specific_experiments_prompt,
)
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
)
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ExperimentCode, ResearchHypothesis
from airas.utils.save_prompt import save_io_on_github

# TODO: Future enhancement - handle multiple experiments independently
# Currently processing all experimental variations in a single call
# Each experimental variation could ideally be processed separately
# This would enable:
# 1. Processing each dataset/model combination independently
# 2. Parallel execution of multiple experimental configurations
# 3. Incremental experiment addition without regenerating all code
# 4. Better resource utilization and more flexible experiment generation


def derive_specific_experiments(
    llm_name: OPENAI_MODEL,
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    secret_names: list[str],
    github_repository_info: GitHubRepositoryInfo,
) -> ResearchHypothesis:
    client = OpenAIClient(reasoning_effort="high")
    env = Environment()

    template = env.from_string(derive_specific_experiments_prompt)

    data = {
        "new_method": new_method.model_dump(),
        "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
        "secret_names": secret_names,
    }
    messages = template.render(data)

    output, cost = client.structured_outputs(
        model_name=llm_name,
        message=messages,
        data_model=ExperimentCode,
    )

    if output is None:
        raise ValueError("No response from LLM in derive_specific_experiments.")
    save_io_on_github(
        github_repository_info=github_repository_info,
        input=messages,
        output=json.dumps(output, ensure_ascii=False, indent=4),
        subgraph_name="create_code_subgraph",
        node_name="derive_specific_experiments",
    )
    new_method.experimental_design.experiment_code = ExperimentCode(**output)
    return new_method
