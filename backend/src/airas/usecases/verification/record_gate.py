"""Verify the record without reference to a paper.

The paper gate cannot be the check that guards the default branch: it needs
a `main.tex` and builds a PDF, so it has nothing to say about the commits
that make up most of a repository's life — the experiment code, the run
outputs, the record as it fills in. Requiring it on every commit would
either block work that has no paper yet or, if it is not required, leave the
branch unguarded exactly while the record is being written.

So the record is checked on its own terms here: everything in the paper
gate that does not need LaTeX. It is meant to be required on the protected
branch and to be green on a repository that has no record at all, because
a repository with nothing to contradict is not failing anything.
"""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any, Callable

from pydantic import ValidationError

from airas.core.research_paths import RECORD_PATH
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper_values import (
    ClaimStatus,
    PaperValuesVerificationReport,
    ProvenanceCheckResult,
)
from airas.core.types.research_record import RECORD_SCHEMA_VERSION, ResearchRecord
from airas.infra.seyval_client import SeyvalClient
from airas.usecases.publication.paper_values.charts import verify_charts
from airas.usecases.publication.paper_values.compute import (
    COMPARISON_KEY,
    compute_claim_values,
    load_metrics_data,
)
from airas.usecases.publication.paper_values.record import (
    orphan_runs,
    override_problems,
    record_consistency_problems,
    run_index,
)
from airas.usecases.publication.paper_values.verify import (
    apply_provenance_result,
    claim_evaluation_drift,
    referenced_result_dirs,
    verify_paper_record,
)
from airas.usecases.verification.record_history import (
    compute_claim_status,
    record_append_only_status,
)
from airas.usecases.verification.seyval_provenance import (
    SeyvalProvenanceVerifier,
    load_provenance_manifest,
)

logger = logging.getLogger(__name__)


def verify_record_only(local_repo_path: str) -> PaperValuesVerificationReport:
    """Every check the record carries on its own, with no paper involved.

    Returns the same report type the paper gate uses, with the LaTeX-only
    fields (`values_tex_match`, `undefined_keys`) reported as satisfied —
    they are not skipped findings but questions this gate does not ask.
    """
    root = Path(local_repo_path).expanduser().resolve()
    record_file = root / RECORD_PATH

    mismatches: list[str] = []
    if not record_file.is_file():
        # A repository with no record has made no claim to contradict. The
        # requirement to have one belongs to the paper gate, which knows a
        # paper exists; enforcing it here would block the commits that
        # create the record in the first place.
        # Listed as missing rather than left empty: downstream, "did this
        # repository opt into the record system" is read off missing_files,
        # and an empty list there says the record exists and was checked.
        return PaperValuesVerificationReport(
            ok=True,
            stage="prereg",
            values_match=True,
            values_tex_match=True,
            missing_files=[RECORD_PATH],
        )

    record: ResearchRecord | None = None
    raw = record_file.read_text(encoding="utf-8")
    try:
        version = (json.loads(raw) or {}).get("schema_version")
    except json.JSONDecodeError as e:
        version = None
        mismatches.append(f"{RECORD_PATH} is not valid JSON: {e}")
    else:
        if isinstance(version, int) and version < RECORD_SCHEMA_VERSION:
            # Say which airas can read it rather than emitting a validation
            # error that reads like the file is corrupt.
            mismatches.append(
                f"{RECORD_PATH} is schema_version {version}, this airas reads "
                f"{RECORD_SCHEMA_VERSION}"
            )
        else:
            try:
                record = ResearchRecord.model_validate_json(raw)
            except ValidationError as e:
                mismatches.append(f"{RECORD_PATH}: {e}")

    if record is None:
        return PaperValuesVerificationReport(
            ok=False,
            stage="prereg",
            values_match=False,
            values_tex_match=True,
            mismatches=mismatches,
        )

    try:
        metrics_data: dict[str, Any] | None = load_metrics_data(str(root))
    except ValueError:
        metrics_data = None
    stage = "results" if metrics_data else "prereg"

    mismatches.extend(record_consistency_problems(record))
    mismatches.extend(override_problems(record))
    orphans = orphan_runs(record)
    append_only, append_only_problems, _ = record_append_only_status(root, record)

    claims: list[ClaimStatus] = []
    claim_status_match = True
    undeclared_result_dirs: list[str] = []
    refuted: list[str] = []

    if stage == "prereg":
        realized = [c.id for c in record.hypothesis.claims if c.evaluations] + [
            run.run_id for run in run_index(record).values() if run.executions
        ]
        if realized:
            mismatches.append(
                "record.json holds realized results but no run outputs exist "
                f"({', '.join(sorted(set(realized)))})"
            )
        claims = compute_claim_status(root, record, None, set())
    else:
        assert metrics_data is not None
        try:
            claim_values = compute_claim_values(record, metrics_data)
        except ValueError as e:
            mismatches.append(str(e))
            claim_values = {}
        else:
            # Charts live under .research/results/, not in the paper's
            # directory, so their regeneration is a record-level check.
            mismatches.extend(verify_charts(record, str(root), metrics_data))

        declared_runs = set(run_index(record))
        undeclared_result_dirs = sorted(
            d for d in metrics_data if d != COMPARISON_KEY and d not in declared_runs
        )
        manifest = load_provenance_manifest(root)
        claims = compute_claim_status(
            root, record, manifest, set(metrics_data), claim_values
        )
        drifted = claim_evaluation_drift(record, claims)
        claim_status_match = not drifted
        if drifted:
            mismatches.append(
                "stored claim evaluations differ from their recomputation "
                f"({', '.join(drifted)}) — run update_record again"
            )
        refuted = [s.id for s in claims if s.criterion_met is False]

    return PaperValuesVerificationReport(
        ok=(
            not mismatches
            and append_only != "violated"
            and claim_status_match
            and not undeclared_result_dirs
        ),
        stage=stage,
        values_match=True,
        values_tex_match=True,
        mismatches=mismatches,
        append_only=append_only,
        append_only_problems=append_only_problems,
        claims=claims,
        claim_status_match=claim_status_match,
        undeclared_result_dirs=undeclared_result_dirs,
        refuted_claims=refuted,
        orphan_runs=orphans,
        unverified_claims=[c.id for c in claims if not c.verified],
    )


async def record_full_report(
    local_path: str,
    check_provenance: bool,
    seyval_client_factory: Callable[[], SeyvalClient],
    latex_template_name: LATEX_TEMPLATE_NAME | None = None,
) -> PaperValuesVerificationReport:
    """The record's checks, plus the paper's numbers when a paper exists.

    With a template, the paper's value checks — values.tex against its
    regeneration, declared tables, every `\\airasval` key declared — are
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
