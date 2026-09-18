from typing import Any

from airas.core.types.github import GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.infra.github_client import GithubClient
from airas.usecases.publication.nodes.build_overleaf_export import build_overleaf_export
from airas.usecases.publication.nodes.collect_latex_project_files import (
    collect_latex_project_files,
    collect_latex_project_files_local,
)


def open_in_overleaf(
    github_config: GitHubConfig,
    template: LATEX_TEMPLATE_NAME,
    *,
    github_client: GithubClient | None = None,
    local_path: str | None = None,
) -> dict[str, Any]:
    """The page that hands the paper's LaTeX project to Overleaf: from the
    clone's working tree with `local_path`, else from GitHub. Figures under
    .research/results/ and .research/diagrams/ are merged into images/."""
    if local_path is not None:
        latex_files = collect_latex_project_files_local(local_path, template)
    elif github_client is not None:
        latex_files = collect_latex_project_files(
            github_config=github_config,
            latex_template_name=template,
            github_client=github_client,
        )
    else:
        raise ValueError("github_client is required unless local_path is provided")
    return {
        "overleaf_html": build_overleaf_export(
            latex_files=latex_files,
            project_name=f"{github_config.repository_name}-{github_config.branch_name}",
        ),
        "file_names": sorted(latex_files),
    }
