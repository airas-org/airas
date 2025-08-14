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
    client: DevinClient | None = None,
):
    client = client or DevinClient()

    if not new_method or not new_method.strip():
        raise ValueError("new_method cannot be empty")
    if not experiment_code or not experiment_code.strip():
        logger.warning("experiment_code is empty, using placeholder")
        experiment_code = "# No experimental code provided"

    # NOTE: The official prompt length limit is undocumented. Setting arbitrary limits to be safe.
    MAX_METHOD_LENGTH = 10000
    MAX_CODE_LENGTH = 15000

    if len(new_method) > MAX_METHOD_LENGTH:
        new_method = (
            new_method[:MAX_METHOD_LENGTH]
            + "...\n[Content truncated due to length limit]"
        )
        logger.warning(f"new_method truncated to {MAX_METHOD_LENGTH} characters")

    if len(experiment_code) > MAX_CODE_LENGTH:
        experiment_code = (
            experiment_code[:MAX_CODE_LENGTH]
            + "...\n[Content truncated due to length limit]"
        )
        logger.warning(f"experiment_code truncated to {MAX_CODE_LENGTH} characters")

    env = Environment()
    template = env.from_string(create_session_prompt)
    prompt = template.render(
        repository_url=repository_url,
        branch_name=branch_name,
        new_method=new_method.strip(),
        experiment_code=experiment_code.strip(),
        experiment_iteration=experiment_iteration,
    )

    logger.info(f"Generated prompt length: {len(prompt)} characters")
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

    try:
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
        return DevinInfo(
            session_id=experiment_session_id, devin_url=experiment_devin_url
        )

    except Exception as e:
        logger.error(f"Failed to create Devin session: {e}")
        logger.error(f"Repository URL: {repository_url}")
        logger.error(f"Branch: {github_repository_info.branch_name}")
        logger.error(f"Method description length: {len(method_description)}")
        logger.error(f"Experiment code length: {len(experiment_code)}")
        raise
