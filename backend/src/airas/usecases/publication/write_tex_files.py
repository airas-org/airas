"""Rendering the record's LaTeX inputs and writing them into the template."""

from __future__ import annotations

from pathlib import Path

from airas.core.research_paths import REFERENCES_BIB_FILENAME
from airas.core.types.research_record import ResearchRecord
from airas.research_record.read_run_outputs import load_metrics_data
from airas.usecases.literature.bibliography import (
    render_references_bib,
)
from airas.usecases.publication.map_record_to_publication import (
    CLAIMS_TEX_FILENAME,
    render_claims_tex,
)


def write_claims_tex(local_path: str, template: str, record: ResearchRecord) -> str:
    """Render claims.tex from the record and whatever metrics exist.

    Returns the repo-relative path, for the commit.
    """
    root = Path(local_path).expanduser().resolve()
    try:
        metrics_data = load_metrics_data(local_path)
    except ValueError:
        metrics_data = {}  # prereg stage: every claim renders as pending
    relpath = f".research/latex/{template}/{CLAIMS_TEX_FILENAME}"
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_claims_tex(record, metrics_data), encoding="utf-8")
    return relpath


def write_references_bib(local_path: str, template: str, record: ResearchRecord) -> str:
    relpath = f".research/latex/{template}/{REFERENCES_BIB_FILENAME}"
    path = Path(local_path).expanduser().resolve() / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_references_bib(record.active_literature()), encoding="utf-8")
    return relpath
