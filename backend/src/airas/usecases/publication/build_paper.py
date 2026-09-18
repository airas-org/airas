from airas.core.types.latex import LATEX_TEMPLATE_NAME, LatexBuildReport
from airas.usecases.publication.nodes.build_latex_project import build_latex_project
from airas.usecases.publication.nodes.collect_latex_project_files import (
    collect_latex_project_files_local,
)


def build_paper(
    local_path: str | None,
    template: LATEX_TEMPLATE_NAME,
    pdf_path: str | None = None,
    *,
    latex_files: dict[str, bytes] | None = None,
) -> LatexBuildReport:
    """Build the paper as it stands, in the clone or from files already
    collected, and report what is wrong with it. No value check: the paper
    gate does that, so publish only compiles."""
    if latex_files is None:
        if local_path is None:
            raise ValueError("build_paper needs local_path or latex_files")
        latex_files = collect_latex_project_files_local(local_path, template)
    return build_latex_project(latex_files, "main.tex", pdf_path)
