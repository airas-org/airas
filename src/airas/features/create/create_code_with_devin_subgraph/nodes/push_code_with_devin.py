from logging import getLogger

from jinja2 import Environment

from airas.features.create.create_code_with_devin_subgraph.prompts.create_session_prompt import (
    create_session_prompt,
)
from airas.services.api_client.devin_client import DevinClient
from airas.types.devin import DevinInfo
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis

logger = getLogger(__name__)


def _request_create_session(
    repository_url: str,
    branch_name: str,
    new_method: str,
    experiment_code: str,
    experiment_iteration: int,
):
    client = DevinClient()

    env = Environment()
    template = env.from_string(create_session_prompt)
    prompt = template.render(
        repository_url=repository_url,
        branch_name=branch_name,
        new_method=new_method,
        experiment_code=experiment_code,
        experiment_iteration=experiment_iteration,
    )

    return client.create_session(prompt_template=prompt)


def push_code_with_devin(
    github_repository_info: GitHubRepositoryInfo,
    new_method: ResearchHypothesis,
    experiment_iteration: int,
) -> DevinInfo:
    repository_url = f"https://github.com/{github_repository_info.github_owner}/{github_repository_info.repository_name}"

    method_description = new_method.method
    if new_method.experimental_design:
        if new_method.experimental_design.experiment_details:
            method_description += (
                "\n\nExperimental Details:\n"
                + new_method.experimental_design.experiment_details
            )

    experiment_code = ""
    if (
        new_method.experimental_design
        and new_method.experimental_design.experiment_code
    ):
        experiment_code = new_method.experimental_design.experiment_code

    response = _request_create_session(
        repository_url=repository_url,
        branch_name=github_repository_info.branch_name,
        new_method=method_description,
        experiment_code=experiment_code,
        experiment_iteration=experiment_iteration,
    )

    logger.info("Successfully created Devin session.")
    experiment_session_id = response["session_id"]
    experiment_devin_url = response["url"]
    print(f"Devin URL: {experiment_devin_url}")
    return DevinInfo(session_id=experiment_session_id, devin_url=experiment_devin_url)
