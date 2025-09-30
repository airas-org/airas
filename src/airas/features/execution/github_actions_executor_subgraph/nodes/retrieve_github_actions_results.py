import asyncio
import base64
import logging
from typing import cast

from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import (
    ExperimentalResults,
    ExperimentCode,
    ResearchHypothesis,
)

logger = logging.getLogger(__name__)


def _decode_base64_content(content: str) -> str:
    try:
        decoded_bytes = base64.b64decode(content)
        return decoded_bytes.decode("utf-8")
    except Exception as e:
        logger.error(f"Failed to decode base64 content: {e}")
        raise


def _get_single_file_content(
    client: GithubClient,
    github_owner: str,
    repository_name: str,
    file_path: str,
    branch_name: str,
) -> dict | bytes:
    try:
        response = client.get_repository_content(
            github_owner=github_owner,
            repository_name=repository_name,
            file_path=file_path,
            branch_name=branch_name,
            as_="json",
        )
        return response

    except Exception as e:
        logger.error(f"Error retrieving {file_path} from repository: {e}")
        raise


async def _retrieve_results_for_branch(
    client: GithubClient,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    experiment_iteration: int,
) -> tuple[str, str, list[str], ExperimentCode]:
    """Retrieve results and code for a single branch."""
    output_file_path = f".research/iteration{experiment_iteration}/output.txt"
    error_file_path = f".research/iteration{experiment_iteration}/error.txt"
    image_directory_path = f".research/iteration{experiment_iteration}/images"

    output_text_data = ""
    error_text_data = ""
    image_file_name_list = []

    # Retrieve output file
    try:
        output_text_response = _get_single_file_content(
            client, github_owner, repository_name, output_file_path, branch_name
        )
        if output_text_response and "content" in output_text_response:
            output_text_data = _decode_base64_content(output_text_response["content"])
        else:
            logger.warning(
                f"Output file {output_file_path} found but content is missing or invalid."
            )
    except Exception as e:
        logger.warning(
            f"Could not retrieve output file {output_file_path}: {e}. Continuing with empty string."
        )

    # Retrieve error file
    try:
        error_text_response = _get_single_file_content(
            client, github_owner, repository_name, error_file_path, branch_name
        )
        if error_text_response and "content" in error_text_response:
            error_text_data = _decode_base64_content(error_text_response["content"])
        else:
            logger.warning(
                f"Error file {error_file_path} found but content is missing or invalid."
            )
    except Exception as e:
        logger.warning(
            f"Could not retrieve error file {error_file_path}: {e}. Continuing with empty string."
        )

    # Retrieve images
    try:
        image_data_list = _get_single_file_content(
            client, github_owner, repository_name, image_directory_path, branch_name
        )
        image_file_name_list = [
            image_data["name"] for image_data in cast(list[dict], image_data_list)
        ]
    except Exception as e:
        logger.warning(f"Images directory not found at {image_directory_path}: {e}")
        image_file_name_list = []

    # Retrieve ExperimentCode files
    dummy_code = ExperimentCode(**{field: "" for field in ExperimentCode.model_fields})
    file_dict = dummy_code.to_file_dict()

    code_contents = {}
    for file_path in file_dict.values():
        try:
            file_response = _get_single_file_content(
                client, github_owner, repository_name, file_path, branch_name
            )
            if file_response and "content" in file_response:
                code_contents[file_path] = _decode_base64_content(
                    file_response["content"]
                )
            else:
                logger.warning(f"Code file {file_path} found but content is missing.")
                code_contents[file_path] = ""
        except Exception as e:
            logger.warning(f"Could not retrieve code file {file_path}: {e}")
            code_contents[file_path] = ""

    field_values = {}
    for field_name, file_path in zip(
        ExperimentCode.model_fields.keys(), file_dict.values(), strict=True
    ):
        field_values[field_name] = code_contents.get(file_path, "")

    experiment_code = ExperimentCode(**field_values)
    logger.info(f"Successfully retrieved results from branch {branch_name}")

    return output_text_data, error_text_data, image_file_name_list, experiment_code


async def _retrieve_github_actions_results(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    new_method: ResearchHypothesis,
    experiment_branches: list[str],
    github_client: GithubClient | None = None,
) -> ResearchHypothesis:
    client = github_client or GithubClient()

    github_owner = github_repository.github_owner
    repository_name = github_repository.repository_name

    if not experiment_branches:
        logger.warning("No experiment branches provided")
        return new_method

    if (
        not new_method.experimental_design
        or not new_method.experimental_design.experiments
    ):
        logger.error("No experiments found in experimental design")
        return new_method

    # Process results for all branches
    for i, branch_name in enumerate(experiment_branches):
        if i >= len(new_method.experimental_design.experiments):
            logger.warning(
                f"More branches ({len(experiment_branches)}) than experiments ({len(new_method.experimental_design.experiments)})"
            )
            break

        experiment = new_method.experimental_design.experiments[i]
        logger.info(
            f"Retrieving results for experiment '{experiment.experiment_id}' from branch '{branch_name}'"
        )

        try:
            (
                output_text,
                error_text,
                image_files,
                exp_code,
            ) = await _retrieve_results_for_branch(
                client, github_owner, repository_name, branch_name, experiment_iteration
            )

            # Store results in the experiment
            experiment.results = ExperimentalResults(
                result=output_text,
                error=error_text,
                image_file_name_list=image_files,
            )
            experiment.code = exp_code
            experiment.github_repository_info = github_repository

        except Exception as e:
            logger.error(f"Failed to retrieve results for branch {branch_name}: {e}")
            experiment.results = ExperimentalResults(
                result="",
                error=f"Failed to retrieve results: {str(e)}",
                image_file_name_list=[],
            )

    return new_method


def retrieve_github_actions_results(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    new_method: ResearchHypothesis,
    experiment_branches: list[str],
    github_client: GithubClient | None = None,
) -> ResearchHypothesis:
    return asyncio.run(
        _retrieve_github_actions_results(
            github_repository,
            experiment_iteration,
            new_method,
            experiment_branches,
            github_client,
        )
    )
