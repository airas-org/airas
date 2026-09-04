import io
import logging
import re
import zipfile
from pathlib import Path

from airas.core.research_paths import LEGACY_DIAGRAM_DIR, RESULTS_DIR
from airas.core.types.github import GitHubConfig
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.infra.github_client import GithubClient

# pdflatex has no way to typeset CJK: every Japanese character raises
# `LaTeX Error: Unicode character` and the PDF comes out with the text
# missing. LuaTeX handles it natively, so the engine follows the document
# rather than the other way round — a paper drafted in Japanese should not
# have to be rewritten to be checkable.
LUALATEX_ENGINE = "lualatex"

PDFLATEX_ENGINE = "pdflatex"

# CJK ideographs, hiragana, katakana, and the fullwidth punctuation that
# comes with them. Latin text with a stray “ or — stays on pdflatex.
_CJK = re.compile(r"[぀-ヿ㐀-䶿一-鿿＀-ﾟ]")


def select_engine(main_tex: str) -> str:
    return LUALATEX_ENGINE if _CJK.search(main_tex) else PDFLATEX_ENGINE


logger = logging.getLogger(__name__)

# Not needed to compile the paper: main.tex already embeds the template, and
# leaving template.tex in the project confuses Overleaf's main-file detection.
_EXCLUDED_FILES = {"template.tex", "template.pdf"}

# Figure sources are merged into the project's images/ directory at export
# time (structure preserved), so nothing has to be copied into the LaTeX
# directory beforehand. Generated LaTeX references figures as images/<path>.
# The legacy .research/diagrams/ entry is scheduled for removal in the next
# major release (see issue #913).
_FIGURE_SOURCE_DIRS = (f"{RESULTS_DIR}/", f"{LEGACY_DIAGRAM_DIR}/")

# PDF for run-generated and diagram figures; PNG because verified charts
# are rendered as png (vl-convert's PDF output is not byte-deterministic,
# so the chart pipeline cannot use it).
_FIGURE_SUFFIXES = (".pdf", ".png")

# Overleaf drives the build with latexmk and defaults it to pdfLaTeX, which
# cannot typeset CJK — a Japanese paper would arrive there and come out with
# its text missing. latexmk reads this file, so shipping it means the export
# compiles on arrival instead of requiring the reader to find the compiler
# setting. `$pdf_mode = 4` is latexmk's own name for "use lualatex".
_LATEXMKRC = "latexmkrc"
_LUALATEX_LATEXMKRC = b"$pdf_mode = 4;\n"


def _add_engine_hint(latex_files: dict[str, bytes]) -> None:
    """Tell latexmk which engine this document needs, if it is not the default."""
    main_tex = latex_files.get("main.tex")
    if main_tex is None or _LATEXMKRC in latex_files:
        return
    if select_engine(main_tex.decode("utf-8", errors="replace")) == "lualatex":
        latex_files[_LATEXMKRC] = _LUALATEX_LATEXMKRC


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
    if not repo_path.lower().endswith(_FIGURE_SUFFIXES):
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
            ) and repo_path.lower().endswith(_FIGURE_SUFFIXES):
                # Only figure files are read: these directories can also hold
                # large experiment artifacts that must not be loaded here.
                if _is_unsafe_relative_path(repo_path):
                    logger.warning(
                        f"Skipping suspicious path in repository zip: {info.filename}"
                    )
                    continue
                figure_entries.append((repo_path, archive.read(info)))

    for repo_path, content in figure_entries:
        _merge_figure(latex_files, repo_path, content)

    _add_engine_hint(latex_files)
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
        # Filter before sorting: these directories can hold many large
        # experiment artifacts that are not figures.
        figure_paths = (
            path
            for path in figure_root.rglob("*")
            if path.suffix.lower() in _FIGURE_SUFFIXES
        )
        for path in sorted(figure_paths):
            if not _is_safe_local_file(path, figure_root):
                continue
            repo_path = source_dir + path.relative_to(figure_root).as_posix()
            _merge_figure(latex_files, repo_path, path.read_bytes())

    _add_engine_hint(latex_files)
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
