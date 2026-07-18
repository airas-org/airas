import io
import logging
import zipfile
from pathlib import Path

from airas.core.types.github import GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.infra.github_client import GithubClient

logger = logging.getLogger(__name__)

# Not needed to compile the paper: main.tex already embeds the template, and
# leaving template.tex in the project confuses Overleaf's main-file detection.
_EXCLUDED_FILES = {"template.tex", "template.pdf"}

# Figure sources are merged into the project's images/ directory at export
# time (structure preserved), so nothing has to be copied into the LaTeX
# directory beforehand. Generated LaTeX references figures as images/<path>.
_FIGURE_SOURCE_DIRS = (".research/results/", ".research/diagrams/")


def _is_safe_local_file(path: Path, containing_dir: Path) -> bool:
    # Symlinks could point outside the repository (e.g. at secrets) and the
    # contents end up in the zip handed to Overleaf, so only read regular
    # files whose real location stays inside the directory being collected.
    if path.is_symlink() or not path.is_file():
        return False
    if not path.resolve().is_relative_to(containing_dir.resolve()):
        logger.warning(f"Skipping file outside the collected directory: {path}")
        return False
    return True


def _is_unsafe_relative_path(relative_path: str) -> bool:
    # Guard against zip-slip style entries: the paths end up inside the
    # zip handed to Overleaf, so never pass through empty, absolute, or
    # parent-escaping paths.
    return (
        not relative_path
        or relative_path.startswith("/")
        or ".." in relative_path.split("/")
    )


def _merge_figure(
    latex_files: dict[str, bytes], repo_path: str, content: bytes
) -> None:
    if not repo_path.lower().endswith(".pdf"):
        return
    for source_dir in _FIGURE_SOURCE_DIRS:
        if repo_path.startswith(source_dir):
            image_path = f"images/{repo_path[len(source_dir) :]}"
            # Files already in the LaTeX directory win (explicitly placed).
            if image_path not in latex_files:
                latex_files[image_path] = content
            return


def collect_latex_project_files(
    github_config: GitHubConfig,
    latex_template_name: LATEX_TEMPLATE_NAME,
    github_client: GithubClient,
) -> dict[str, bytes]:
    """Collect the LaTeX project from the repository on GitHub."""
    repo_zip = github_client.download_repository_zip(
        github_owner=github_config.github_owner,
        repository_name=github_config.repository_name,
        ref=github_config.branch_name,
    )

    # GitHub zipball entries are prefixed with a "{repo}-{sha}/" directory.
    prefix = f".research/latex/{latex_template_name}/"
    latex_files: dict[str, bytes] = {}
    figure_entries: list[tuple[str, bytes]] = []
    with zipfile.ZipFile(io.BytesIO(repo_zip)) as archive:
        for info in archive.infolist():
            if info.is_dir():
                continue
            _, _, repo_path = info.filename.partition("/")
            if repo_path.startswith(prefix):
                relative_path = repo_path[len(prefix) :]
                if relative_path in _EXCLUDED_FILES:
                    continue
                if _is_unsafe_relative_path(relative_path):
                    logger.warning(
                        f"Skipping suspicious path in repository zip: {info.filename}"
                    )
                    continue
                latex_files[relative_path] = archive.read(info)
            elif repo_path.startswith(
                _FIGURE_SOURCE_DIRS
            ) and repo_path.lower().endswith(".pdf"):
                # Only figure PDFs are read: these directories can also hold
                # large experiment artifacts that must not be loaded here.
                if _is_unsafe_relative_path(repo_path):
                    logger.warning(
                        f"Skipping suspicious path in repository zip: {info.filename}"
                    )
                    continue
                figure_entries.append((repo_path, archive.read(info)))

    for repo_path, content in figure_entries:
        _merge_figure(latex_files, repo_path, content)

    _require_main_tex(latex_files, prefix, source=github_config.repository_name)
    logger.info(f"Collected {len(latex_files)} LaTeX project files from {prefix}")
    return latex_files


def collect_latex_project_files_local(
    local_repo_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
) -> dict[str, bytes]:
    """Collect the LaTeX project from a local clone's working tree.

    Reads the current state on disk (no push required), so figures rendered
    locally (e.g. by render_chart / render_diagram) are included as-is.
    """
    root = Path(local_repo_path).expanduser().resolve()
    if not root.is_dir():
        raise ValueError(f"local_repo_path is not a directory: {root}")

    prefix = f".research/latex/{latex_template_name}/"
    latex_dir = root / ".research" / "latex" / latex_template_name
    latex_files: dict[str, bytes] = {}
    if latex_dir.is_dir():
        for path in sorted(latex_dir.rglob("*")):
            if not _is_safe_local_file(path, latex_dir):
                continue
            relative_path = path.relative_to(latex_dir).as_posix()
            if relative_path in _EXCLUDED_FILES:
                continue
            latex_files[relative_path] = path.read_bytes()

    for source_dir in _FIGURE_SOURCE_DIRS:
        figure_root = root / source_dir.rstrip("/")
        if not figure_root.is_dir():
            continue
        for path in sorted(figure_root.rglob("*.pdf")):
            if not _is_safe_local_file(path, figure_root):
                continue
            repo_path = source_dir + path.relative_to(figure_root).as_posix()
            _merge_figure(latex_files, repo_path, path.read_bytes())

    _require_main_tex(latex_files, prefix, source=str(root))
    logger.info(f"Collected {len(latex_files)} LaTeX project files from {latex_dir}")
    return latex_files


def _require_main_tex(latex_files: dict[str, bytes], prefix: str, source: str) -> None:
    if "main.tex" not in latex_files:
        raise ValueError(
            f"main.tex not found under {prefix} in {source}. Write the "
            "generated LaTeX there first (push it with git, or for a local "
            "clone just save the file)."
        )
