from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.fetch_repository_files import fetch_repository_files

_FILE_NAMES = ("result.json", "tuning_figure.png")


async def fetch_tuning_outputs(
    github_client: GithubClient,
    github_config: GitHubConfig,
    repro_id: str,
) -> dict:
    # run_parameter_tuning_run.yml commits the fixed driver's outputs (result.json +
    # tuning_figure.png) to .reproduction/<repro_id>/tuning/ on the branch.
    return await fetch_repository_files(
        github_client=github_client,
        github_config=github_config,
        dir_path=f".reproduction/{repro_id}/tuning",
        file_names=_FILE_NAMES,
    )
