from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.fetch_repository_files import fetch_repository_files

# src/main.py (the Hydra experiment code) / run.log / paper.txt / paper_extraction.json / the run
# config feed the backend validation nodes; validation is produced on the backend side, so no
# validation.json/final_status.json in the results. paper_extraction.json is written by a dedicated
# paper-extraction agent step in the generate workflow (run after the code-generation agent, given
# only the parameter key schema from the generated config), recording parameter values exactly as
# stated in the paper for cross-checking. result.json has no `parameters` field (it would just
# duplicate the run config, which has no CLI overrides for a plain run) — parameter values and their
# `# source: ..., note: ...` comments are read from config/run/reproduction.yaml instead.
_RESULTS_FILES = ("result.json", "repro.md", "repro.png", "run.log")
_REPRO_FILES = ("paper.txt", "paper_extraction.json")
_SRC_FILES = ("main.py",)
_CONFIG_FILES = ("reproduction.yaml",)


async def fetch_reproduction_outputs(
    github_client: GithubClient,
    github_config: GitHubConfig,
    repro_id: str,
) -> dict:
    # The run workflow commits deliverables to .reproduction/<repro_id>/results/; paper.txt lives
    # at .reproduction/<repro_id>/, the Hydra experiment code at .reproduction/<repro_id>/src/, and
    # the run config at .reproduction/<repro_id>/config/run/, so several directory reads are needed.
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
    outputs["paper_extraction"] = repro.get("paper_extraction")

    src = await fetch_repository_files(
        github_client=github_client,
        github_config=github_config,
        dir_path=f"{repro_dir}/src",
        file_names=_SRC_FILES,
    )
    outputs["main_py"] = src.get("main_py")

    config = await fetch_repository_files(
        github_client=github_client,
        github_config=github_config,
        dir_path=f"{repro_dir}/config/run",
        file_names=_CONFIG_FILES,
    )
    outputs["reproduction_yaml"] = config.get("reproduction_yaml")
    return outputs
