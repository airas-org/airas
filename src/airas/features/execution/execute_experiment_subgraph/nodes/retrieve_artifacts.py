import base64
import logging

from dependency_injector.wiring import Provide, inject

from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.github_client import GithubClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_iteration import (
    ExperimentalAnalysis,
    ExperimentalResults,
    ExperimentCode,
    ExperimentRun,
)
from airas.types.research_session import ResearchSession

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


def _retrieve_experiment_code(
    client: GithubClient,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    experiment_runs: list[ExperimentRun],
) -> ExperimentCode:
    dummy_code = ExperimentCode(**{field: "" for field in ExperimentCode.model_fields})
    file_dict = dummy_code.to_file_dict(experiment_runs=experiment_runs)

    code_contents = {}
    for file_path in file_dict.keys():
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

    field_values = {
        field_name: code_contents.get(file_path, "")
        for field_name, file_path in zip(
            ExperimentCode.model_fields.keys(), file_dict.keys(), strict=False
        )
    }

    # Store run configs in ExperimentRun.run_config
    for exp_run in experiment_runs:
        run_config_path = f"config/runs/{exp_run.run_id}.yaml"
        if run_config_path in code_contents:
            exp_run.run_config = code_contents[run_config_path]

    return ExperimentCode(**field_values)


async def _retrieve_artifacts_from_branch(
    client: GithubClient,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    experiment_iteration: int,
    include_code: bool = False,
    experiment_runs: list[ExperimentRun] | None = None,
) -> tuple[str, str, list[str], ExperimentCode | None]:
    iteration_path = f".research/iteration{experiment_iteration}"
    stdout_file_path = f"{iteration_path}/stdout.txt"
    stderr_file_path = f"{iteration_path}/stderr.txt"
    image_directory_path = f"{iteration_path}/images"

    stdout_text_data = ""
    try:
        stdout_text_response = _get_single_file_content(
            client, github_owner, repository_name, stdout_file_path, branch_name
        )
        if stdout_text_response and "content" in stdout_text_response:
            stdout_text_data = _decode_base64_content(stdout_text_response["content"])
        else:
            logger.warning(
                f"Stdout file {stdout_file_path} found but content is missing."
            )
    except Exception as e:
        logger.warning(f"Could not retrieve stdout file {stdout_file_path}: {e}")

    stderr_text_data = ""
    try:
        stderr_text_response = _get_single_file_content(
            client, github_owner, repository_name, stderr_file_path, branch_name
        )
        if stderr_text_response and "content" in stderr_text_response:
            stderr_text_data = _decode_base64_content(stderr_text_response["content"])
        else:
            logger.warning(
                f"Stderr file {stderr_file_path} found but content is missing."
            )
    except Exception as e:
        logger.warning(f"Could not retrieve stderr file {stderr_file_path}: {e}")

    image_file_name_list: list[str] = []
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

    # Retrieve experiment code if requested
    experiment_code = None
    if include_code and experiment_runs:
        experiment_code = _retrieve_experiment_code(
            client, github_owner, repository_name, branch_name, experiment_runs
        )

    logger.info(f"Successfully retrieved artifacts from branch {branch_name}")
    return stdout_text_data, stderr_text_data, image_file_name_list, experiment_code


@inject
async def retrieve_trial_experiment_artifacts(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    research_session: ResearchSession,
    github_client: GithubClient = Provide[SyncContainer.github_client],
) -> tuple[ResearchSession, ExperimentalResults]:
    if (
        not research_session.current_iteration
        or not research_session.current_iteration.experiment_runs
    ):
        logger.error("No experiment runs found in current_iteration")
        return research_session, ExperimentalResults()

    (
        stdout_text,
        error_text,
        image_files,
        experiment_code,
    ) = await _retrieve_artifacts_from_branch(
        github_client,
        github_repository.github_owner,
        github_repository.repository_name,
        github_repository.branch_name,
        experiment_iteration,
        include_code=True,
        experiment_runs=research_session.current_iteration.experiment_runs,
    )

    research_session.current_iteration.experimental_design.experiment_code = (
        experiment_code
    )
    logger.info(f"Updated experiment_code from branch {github_repository.branch_name}")

    trial_experiment_results = ExperimentalResults(
        stdout=stdout_text,
        stderr=error_text,
        figures=image_files,
    )

    logger.info(
        f"Successfully retrieved trial experiment artifacts from branch {github_repository.branch_name}"
    )
    return research_session, trial_experiment_results


@inject
async def retrieve_evaluation_artifacts(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    research_session: ResearchSession,
    github_client: GithubClient = Provide[SyncContainer.github_client],
) -> ResearchSession:
    iteration_path = f".research/iteration{experiment_iteration}"

    for run in research_session.current_iteration.experiment_runs:
        run_dir = f"{iteration_path}/{run.run_id}"
        if run.results is None:
            run.results = ExperimentalResults()

        try:
            metrics_file = _get_single_file_content(
                github_client,
                github_repository.github_owner,
                github_repository.repository_name,
                f"{run_dir}/metrics.json",
                github_repository.branch_name,
            )
            if metrics_file and "content" in metrics_file:
                run.results.metrics_data = _decode_base64_content(
                    metrics_file["content"]
                )
                logger.info(f"Retrieved metrics for run {run.run_id}")
        except Exception as e:
            logger.warning(f"Could not retrieve metrics for run {run.run_id}: {e}")

        try:
            figures_list = _get_single_file_content(
                github_client,
                github_repository.github_owner,
                github_repository.repository_name,
                run_dir,
                github_repository.branch_name,
            )
            if isinstance(figures_list, list):
                run.results.figures = [f["name"] for f in figures_list]
                logger.info(
                    f"Retrieved {len(run.results.figures)} figures for run {run.run_id}"
                )
        except Exception as e:
            logger.warning(f"Could not retrieve figures for run {run.run_id}: {e}")

    comparison_dir = f"{iteration_path}/comparison"
    aggregated_metrics = ""
    try:
        aggregated_file = _get_single_file_content(
            github_client,
            github_repository.github_owner,
            github_repository.repository_name,
            f"{comparison_dir}/aggregated_metrics.json",
            github_repository.branch_name,
        )
        if aggregated_file and "content" in aggregated_file:
            aggregated_metrics = _decode_base64_content(aggregated_file["content"])
            logger.info("Retrieved aggregated metrics")
    except Exception as e:
        logger.warning(f"Could not retrieve aggregated metrics: {e}")

    comparison_figures: list[str] = []
    try:
        comparison_files = _get_single_file_content(
            github_client,
            github_repository.github_owner,
            github_repository.repository_name,
            comparison_dir,
            github_repository.branch_name,
        )
        if isinstance(comparison_files, list):
            comparison_figures = [f["name"] for f in comparison_files]
            logger.info(f"Retrieved {len(comparison_figures)} comparison figures")
    except Exception as e:
        logger.warning(f"Could not retrieve comparison figures: {e}")

    if not research_session.current_iteration.experimental_analysis:
        research_session.current_iteration.experimental_analysis = (
            ExperimentalAnalysis()
        )

    research_session.current_iteration.experimental_analysis.aggregated_metrics = (
        aggregated_metrics
    )
    research_session.current_iteration.experimental_analysis.comparison_figures = (
        comparison_figures
    )

    logger.info(
        f"Successfully retrieved evaluation artifacts from branch {github_repository.branch_name}"
    )
    return research_session
