from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.fetch_repository_files import fetch_repository_files

# src/main.py (the Hydra experiment code) / run.log / paper.txt feed the backend validation nodes;
# validation is produced on the backend side, so no validation.json/final_status.json in the results.
_RESULTS_FILES = ("result.json", "repro.md", "repro.png", "run.log")
_REPRO_FILES = ("paper.txt",)
_SRC_FILES = ("main.py",)


async def fetch_reproduction_outputs(
    github_client: GithubClient,
    github_config: GitHubConfig,
    repro_id: str,
) -> dict:
    # The run workflow commits deliverables to .reproduction/<repro_id>/results/; paper.txt lives
    # at .reproduction/<repro_id>/ and the Hydra experiment code at .reproduction/<repro_id>/src/,
    # so several directory reads are needed.
    repro_dir = f".reproduction/{repro_id}"
    outputs = await fetch_repository_files(
        github_client=github_client,
        github_config=github_config,
        dir_path=f"{repro_dir}/results",
        file_names=_RESULTS_FILES,
    )

    repro = await fetch_repository_files(
        github_client=github_client,
        github_config=github_config,
        dir_path=repro_dir,
        file_names=_REPRO_FILES,
    )
    outputs["paper_txt"] = repro.get("paper_txt")

    src = await fetch_repository_files(
        github_client=github_client,
        github_config=github_config,
        dir_path=f"{repro_dir}/src",
        file_names=_SRC_FILES,
    )
    outputs["main_py"] = src.get("main_py")
    return outputs
