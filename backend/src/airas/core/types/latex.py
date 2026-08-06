from typing import Literal, Optional

from pydantic import BaseModel, Field

from airas.core.types.github import GitHubRepositoryInfo

LATEX_TEMPLATE_NAME = Literal["iclr2024", "agents4science_2025", "mdpi"]


class LatexBuildReport(BaseModel):
    """What a LaTeX build produced, and what is wrong with it.

    The fields below are the failures that still render a PDF, so a build
    that only checks the exit status calls them a success: a citation that
    prints as `?`, a figure that never made it into images/, a dangling
    \\ref. They are reported separately because each has a different fix.
    """

    ok: bool = Field(
        description=(
            "True only if a PDF was produced with no undefined citation, no "
            "undefined reference, no missing figure, and no LaTeX error"
        )
    )
    compiled: bool = Field(description="Whether a PDF file was produced at all")
    page_count: Optional[int] = Field(
        default=None, description="Pages in the produced PDF"
    )
    undefined_citations: list[str] = Field(
        default_factory=list,
        description="Citation keys that render as '?' (missing from the .bib)",
    )
    undefined_references: list[str] = Field(
        default_factory=list,
        description="\\ref/\\label targets that render as '??'",
    )
    missing_figures: list[str] = Field(
        default_factory=list,
        description="Figure paths the document includes but the project lacks",
    )
    errors: list[str] = Field(
        default_factory=list, description="LaTeX errors, in the order emitted"
    )
    log_tail: str = Field(
        default="", description="Tail of the build log, for diagnosing errors"
    )


# Official LaTeX template repository
LATEX_TEMPLATE_REPOSITORY_INFO = GitHubRepositoryInfo(
    github_owner="airas-org",
    repository_name="airas-template",
    branch_name="main",
)
