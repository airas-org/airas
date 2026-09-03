"""Verify the record without reference to a paper.

The paper gate cannot be the check that guards the default branch: it needs
a `main.tex` and builds a PDF, so it has nothing to say about the commits
that make up most of a repository's life — the experiment code, the run
outputs, the record as it fills in. Requiring it on every commit would
either block work that has no paper yet or, if it is not required, leave the
branch unguarded exactly while the record is being written.

So the record is checked on its own terms here — the same `check_record`
the paper gate runs, without the paper on top. It is meant to be required on
the protected branch and to be green on a repository that has no record at
all, because a repository with nothing to contradict is not failing anything.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from airas.core.research_paths import RECORD_PATH
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper_values import (
    PaperValuesVerificationReport,
    ProvenanceCheckResult,
)
from airas.infra.seyval_client import SeyvalClient
from airas.usecases.publication.paper_values.compute import load_metrics_data
from airas.usecases.publication.paper_values.record import load_record
from airas.usecases.publication.paper_values.verify import (
    apply_provenance_result,
    check_record,
    record_ok,
    referenced_result_dirs,
    verify_paper_record,
)
from airas.usecases.verification.seyval_provenance import SeyvalProvenanceVerifier

logger = logging.getLogger(__name__)


def verify_record_only(local_repo_path: str) -> PaperValuesVerificationReport:
    """Every check the record carries on its own, with no paper involved.

    Returns the same report type the paper gate uses, with the LaTeX-only
    fields (`values_tex_match`, `undefined_keys`) reported as satisfied —
    they are not skipped findings but questions this gate does not ask.
    """
    root = Path(local_repo_path).expanduser().resolve()
    if not (root / RECORD_PATH).is_file():
        # A repository with no record has made no claim to contradict. The
        # requirement to have one belongs to the paper gate, which knows a
        # paper exists; enforcing it here would block the commits that
        # create the record in the first place. Listed as missing rather
        # than left empty: downstream, "did this repository opt into the
        # record system" is read off missing_files.
        return PaperValuesVerificationReport(
            ok=True,
            stage="prereg",
            values_match=True,
            values_tex_match=True,
            missing_files=[RECORD_PATH],
        )

    try:
        record = load_record(str(root))
    except (ValidationError, ValueError) as e:
        return PaperValuesVerificationReport(
            ok=False,
            stage="prereg",
            values_match=False,
            values_tex_match=True,
            mismatches=[f"{RECORD_PATH}: {e}"],
        )

    try:
        metrics_data: dict[str, Any] | None = load_metrics_data(str(root))
    except ValueError:
        metrics_data = None

    checks = check_record(root, record, metrics_data)
    return PaperValuesVerificationReport(
        ok=record_ok(checks),
        stage=checks.stage,
        values_match=True,
        values_tex_match=True,
        mismatches=checks.mismatches,
        append_only=checks.append_only,
        append_only_problems=checks.append_only_problems,
        record_commits=checks.record_commits,
        claims=checks.claims,
        claim_status_match=checks.claim_status_match,
        undeclared_result_dirs=checks.undeclared_result_dirs,
        unverified_claims=[c.id for c in checks.claims if not c.verified],
    )


async def record_full_report(
    local_path: str,
    check_provenance: bool,
    seyval_client_factory: Callable[[], SeyvalClient],
    latex_template_name: LATEX_TEMPLATE_NAME | None = None,
) -> PaperValuesVerificationReport:
    """The record's checks, plus the paper's numbers when a paper exists.

    With a template, the paper's value checks — values.tex against its
    regeneration, declared tables, every `\\\\airasval` key declared — are
    included, because "the numbers in the paper are the numbers in the
    record" is integrity, not rendering, and belongs in the gate that
    decides what lands. None of it needs LaTeX installed; the compile is
    the publish step's concern. Then the cross-check against the platform.
    """
    if latex_template_name is None:
        report = await asyncio.to_thread(verify_record_only, local_path)
    else:
        report = await asyncio.to_thread(
            verify_paper_record, local_path, latex_template_name
        )
    if not check_provenance:
        return report

    used_dirs = await asyncio.to_thread(referenced_result_dirs, local_path)
    if not used_dirs:
        return report

    try:
        verifier = SeyvalProvenanceVerifier(seyval_client_factory())
        provenance = await verifier.verify(local_path, used_dirs)
    except Exception as e:
        provenance = ProvenanceCheckResult(
            source="seyval",
            status="unavailable",
            detail=f"provenance verifier unavailable: {e}",
        )
    return apply_provenance_result(report, provenance)
