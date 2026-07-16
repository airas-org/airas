import io
import logging
import zipfile

from airas.core.types.github import GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.infra.github_client import GithubClient

logger = logging.getLogger(__name__)

# Not needed to compile the paper: main.tex already embeds the template, and
# leaving template.tex in the project confuses Overleaf's main-file detection.
_EXCLUDED_FILES = {"template.tex", "template.pdf"}


def collect_latex_project_files(
    github_config: GitHubConfig,
    latex_template_name: LATEX_TEMPLATE_NAME,
    github_client: GithubClient,
) -> dict[str, bytes]:
    repo_zip = github_client.download_repository_zip(
        github_owner=github_config.github_owner,
        repository_name=github_config.repository_name,
        ref=github_config.branch_name,
    )

    # GitHub zipball entries are prefixed with a "{repo}-{sha}/" directory.
    prefix = f".research/latex/{latex_template_name}/"
    latex_files: dict[str, bytes] = {}
    with zipfile.ZipFile(io.BytesIO(repo_zip)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            _, _, repo_path = info.filename.partition("/")
            if not repo_path.startswith(prefix):
                continue
            relative_path = repo_path[len(prefix) :]
            if relative_path in _EXCLUDED_FILES:
                continue
            latex_files[relative_path] = archive.read(info)

    if "main.tex" not in latex_files:
        raise ValueError(
            f"main.tex not found under {prefix} in "
            f"{github_config.github_owner}/{github_config.repository_name}"
            f"@{github_config.branch_name}. Run push_latex first."
        )

    logger.info(f"Collected {len(latex_files)} LaTeX project files from {prefix}")
    return latex_files
