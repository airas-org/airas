import asyncio
import base64
import logging

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


async def _retrieve_artifacts_from_branch(
    client: GithubClient,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    experiment_iteration: int,
    include_code: bool = False,
) -> tuple[str, str, list[str], ExperimentCode | None]:
    output_file_path = f".research/iteration{experiment_iteration}/output.txt"
    error_file_path = f".research/iteration{experiment_iteration}/error.txt"
    image_directory_path = f".research/iteration{experiment_iteration}/images"

    output_text_data = ""
    error_text_data = ""
    image_file_name_list: list[str] = []

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

    try:
        image_data_list = _get_single_file_content(
            client, github_owner, repository_name, image_directory_path, branch_name
        )
        if isinstance(image_data_list, list):
            image_file_name_list = [
                image_data["name"] for image_data in image_data_list
            ]
    except Exception as e:
        logger.warning(f"Images directory not found at {image_directory_path}: {e}")
        image_file_name_list = []

    experiment_code = None
    if include_code:
        dummy_code = ExperimentCode(
            **{field: "" for field in ExperimentCode.model_fields}
        )
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
                    logger.warning(
                        f"Code file {file_path} found but content is missing."
                    )
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

    logger.info(f"Successfully retrieved artifacts from branch {branch_name}")

    return output_text_data, error_text_data, image_file_name_list, experiment_code


async def _retrieve_trial_experiment_artifacts_async(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    new_method: ResearchHypothesis,
    github_client: GithubClient | None = None,
) -> tuple[ResearchHypothesis, ExperimentalResults]:
    client = github_client or GithubClient()

    github_owner = github_repository.github_owner
    repository_name = github_repository.repository_name
    branch_name = github_repository.branch_name

    (
        output_text,
        error_text,
        image_files,
        base_code,
    ) = await _retrieve_artifacts_from_branch(
        client,
        github_owner,
        repository_name,
        branch_name,
        experiment_iteration,
        include_code=True,
    )

    if new_method.experimental_design and base_code:
        new_method.experimental_design.base_code = base_code
        logger.info(f"Updated base_code from branch {branch_name}")
    else:
        logger.warning(
            "No experimental_design found in new_method or code retrieval failed"
        )

    trial_experiment_results = ExperimentalResults(
        result=output_text,
        error=error_text,
        image_file_name_list=image_files,
    )

    logger.info(
        f"Successfully retrieved trial experiment artifacts from branch {branch_name}"
    )

    return new_method, trial_experiment_results


async def _retrieve_full_experiment_artifacts_async(
    experiment_iteration: int,
    new_method: ResearchHypothesis,
    github_client: GithubClient | None = None,
) -> ResearchHypothesis:
    client = github_client or GithubClient()

    if not new_method.experiment_runs:
        logger.error("No experiment runs found")
        return new_method

    for exp_run in new_method.experiment_runs:
        if not exp_run.github_repository_info:
            logger.warning(f"No branch information found for run {exp_run.run_id}")
            continue

        github_owner = exp_run.github_repository_info.github_owner
        repository_name = exp_run.github_repository_info.repository_name
        branch_name = exp_run.github_repository_info.branch_name

        logger.info(
            f"Retrieving artifacts for run '{exp_run.run_id}' from branch '{branch_name}'"
        )

        try:
            (
                output_text,
                error_text,
                image_files,
                _,
            ) = await _retrieve_artifacts_from_branch(
                client,
                github_owner,
                repository_name,
                branch_name,
                experiment_iteration,
                include_code=False,
            )

            exp_run.results = ExperimentalResults(
                result=output_text,
                error=error_text,
                image_file_name_list=image_files,
            )
            logger.info(f"Successfully stored results for run {exp_run.run_id}")

        except Exception as e:
            logger.error(f"Failed to retrieve artifacts for run {exp_run.run_id}: {e}")
            exp_run.results = ExperimentalResults(
                result="",
                error=f"Failed to retrieve artifacts: {str(e)}",
                image_file_name_list=[],
            )

    return new_method


def retrieve_trial_experiment_artifacts(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    new_method: ResearchHypothesis,
    github_client: GithubClient | None = None,
) -> tuple[ResearchHypothesis, ExperimentalResults]:
    return asyncio.run(
        _retrieve_trial_experiment_artifacts_async(
            github_repository,
            experiment_iteration,
            new_method,
            github_client,
        )
    )


def retrieve_full_experiment_artifacts(
    experiment_iteration: int,
    new_method: ResearchHypothesis,
    github_client: GithubClient | None = None,
) -> ResearchHypothesis:
    return asyncio.run(
        _retrieve_full_experiment_artifacts_async(
            experiment_iteration,
            new_method,
            github_client,
        )
    )
