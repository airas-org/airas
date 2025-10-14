import asyncio
import base64
import json
import logging

from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.wandb_client import WandbClient
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import (
    ExperimentalResults,
    ExperimentCode,
    ResearchHypothesis,
)
from airas.types.wandb import WandbInfo

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


def _get_wandb_run_id_from_metadata(
    client: GithubClient,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    experiment_iteration: int,
) -> str | None:
    metadata_path = f".research/iteration{experiment_iteration}/wandb_metadata.json"

    try:
        response = _get_single_file_content(
            client, github_owner, repository_name, metadata_path, branch_name
        )
        if response and "content" in response:
            content = _decode_base64_content(response["content"])
            metadata = json.loads(content)
            wandb_run_id = metadata.get("wandb_run_id")
            if wandb_run_id:
                logger.info(f"Found wandb_run_id: {wandb_run_id} from {metadata_path}")
                return wandb_run_id
            else:
                logger.warning(f"wandb_run_id not found in {metadata_path}")
                return None
        else:
            logger.warning(
                f"Metadata file {metadata_path} found but content is missing"
            )
            return None
    except Exception as e:
        logger.warning(f"Could not retrieve wandb metadata from {metadata_path}: {e}")
        return None


def _retrieve_experiment_code(
    client: GithubClient,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    new_method: ResearchHypothesis,
) -> ExperimentCode:
    dummy_code = ExperimentCode(**{field: "" for field in ExperimentCode.model_fields})
    experiment_runs = new_method.experiment_runs if new_method else None
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
            ExperimentCode.model_fields.keys(), file_dict.values(), strict=True
        )
    }

    return ExperimentCode(**field_values)


def _append_wandb_metrics(
    output_text: str,
    wandb_client: WandbClient,
    wandb_info: WandbInfo,
    client: GithubClient,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    experiment_iteration: int,
    run_id: str,
) -> str:
    try:
        wandb_run_id = _get_wandb_run_id_from_metadata(
            client, github_owner, repository_name, branch_name, experiment_iteration
        )

        if not wandb_run_id:
            logger.warning(f"Could not find wandb_run_id in metadata for run {run_id}")
            return output_text

        logger.info(
            f"Retrieving WandB metrics for run '{wandb_run_id}' "
            f"from {wandb_info.entity}/{wandb_info.project}"
        )
        metrics_df = wandb_client.retrieve_run_metrics(
            entity=wandb_info.entity,
            project=wandb_info.project,
            run_id=wandb_run_id,
        )
        metrics_text = metrics_df.to_string() if metrics_df is not None else ""
        logger.info(f"Successfully retrieved WandB metrics for run {wandb_run_id}")
        return f"{output_text}\n\n=== WandB Metrics ===\n{metrics_text}"

    except Exception as wandb_error:
        logger.warning(
            f"Failed to retrieve WandB metrics for run {run_id}: {wandb_error}"
        )
        return output_text


async def _retrieve_artifacts_from_branch(
    client: GithubClient,
    github_owner: str,
    repository_name: str,
    branch_name: str,
    experiment_iteration: int,
    include_code: bool = False,
    new_method: ResearchHypothesis | None = None,
) -> tuple[str, str, list[str], ExperimentCode | None]:
    iteration_path = f".research/iteration{experiment_iteration}"
    output_file_path = f"{iteration_path}/output.txt"
    error_file_path = f"{iteration_path}/error.txt"
    # NOTE: Image names are retrieved from repository regardless of source (Python generation or WandB)
    image_directory_path = f"{iteration_path}/images"

    output_text_data = ""
    try:
        output_text_response = _get_single_file_content(
            client, github_owner, repository_name, output_file_path, branch_name
        )
        if output_text_response and "content" in output_text_response:
            output_text_data = _decode_base64_content(output_text_response["content"])
        else:
            logger.warning(
                f"Output file {output_file_path} found but content is missing."
            )
    except Exception as e:
        logger.warning(f"Could not retrieve output file {output_file_path}: {e}")

    error_text_data = ""
    try:
        error_text_response = _get_single_file_content(
            client, github_owner, repository_name, error_file_path, branch_name
        )
        if error_text_response and "content" in error_text_response:
            error_text_data = _decode_base64_content(error_text_response["content"])
        else:
            logger.warning(
                f"Error file {error_file_path} found but content is missing."
            )
    except Exception as e:
        logger.warning(f"Could not retrieve error file {error_file_path}: {e}")

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
    if include_code and new_method:
        experiment_code = _retrieve_experiment_code(
            client, github_owner, repository_name, branch_name, new_method
        )

    logger.info(f"Successfully retrieved artifacts from branch {branch_name}")
    return output_text_data, error_text_data, image_file_name_list, experiment_code


async def _retrieve_trial_experiment_artifacts_async(
    github_repository: GitHubRepositoryInfo,
    experiment_iteration: int,
    new_method: ResearchHypothesis,
    github_client: GithubClient | None = None,
) -> tuple[ResearchHypothesis, ExperimentalResults]:
    client = github_client or GithubClient()

    (
        output_text,
        error_text,
        image_files,
        experiment_code,
    ) = await _retrieve_artifacts_from_branch(
        client,
        github_repository.github_owner,
        github_repository.repository_name,
        github_repository.branch_name,
        experiment_iteration,
        include_code=True,
        new_method=new_method,
    )

    new_method.experimental_design.experiment_code = experiment_code
    logger.info(f"Updated experiment_code from branch {github_repository.branch_name}")

    trial_experiment_results = ExperimentalResults(
        result=output_text,
        error=error_text,
        image_file_name_list=image_files,
    )

    logger.info(
        f"Successfully retrieved trial experiment artifacts from branch {github_repository.branch_name}"
    )
    return new_method, trial_experiment_results


async def _retrieve_full_experiment_artifacts_async(
    experiment_iteration: int,
    new_method: ResearchHypothesis,
    github_client: GithubClient | None = None,
    wandb_client: WandbClient | None = None,
    wandb_info: WandbInfo | None = None,
) -> ResearchHypothesis:
    github_client = github_client or GithubClient()
    wandb_client = wandb_client or (WandbClient() if wandb_info else None)

    for exp_run in new_method.experiment_runs:
        if not exp_run.github_repository_info:
            logger.warning(f"No branch information found for run {exp_run.run_id}")
            continue

        repo_info = exp_run.github_repository_info
        logger.info(
            f"Retrieving artifacts for run '{exp_run.run_id}' from branch '{repo_info.branch_name}'"
        )

        try:
            (
                output_text,
                error_text,
                image_files,
                _,
            ) = await _retrieve_artifacts_from_branch(
                github_client,
                repo_info.github_owner,
                repo_info.repository_name,
                repo_info.branch_name,
                experiment_iteration,
                include_code=False,
            )

            # Append WandB metrics if available
            if wandb_client and wandb_info:
                output_text = _append_wandb_metrics(
                    output_text,
                    wandb_client,
                    wandb_info,
                    github_client,
                    repo_info.github_owner,
                    repo_info.repository_name,
                    repo_info.branch_name,
                    experiment_iteration,
                    exp_run.run_id,
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
    wandb_client: WandbClient | None = None,
    wandb_info: WandbInfo | None = None,
) -> ResearchHypothesis:
    return asyncio.run(
        _retrieve_full_experiment_artifacts_async(
            experiment_iteration,
            new_method,
            github_client,
            wandb_client,
            wandb_info,
        )
    )
