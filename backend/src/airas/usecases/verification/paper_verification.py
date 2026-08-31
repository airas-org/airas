"""Composition of the paper-value checks with the provenance cross-check.

Shared by the MCP tools (`verify_paper_values`, `verify_latex`) and the
`airas verify-paper` CI gate, so both judge a paper by exactly the same
rules — the CI run is a re-execution of the local check, not a variant
of it.
"""

from __future__ import annotations

import asyncio
from typing import Callable

from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper_values import (
    PaperValuesVerificationReport,
    ProvenanceCheckResult,
)
from airas.infra.seyval_client import SeyvalClient
from airas.usecases.publication.paper_values.verify import (
    apply_provenance_result,
    paper_values_configured,
    referenced_result_dirs,
    verify_paper_values,
)
from airas.usecases.verification.seyval_provenance import SeyvalProvenanceVerifier


async def paper_values_full_report(
    local_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
    check_provenance: bool,
    seyval_client_factory: Callable[[], SeyvalClient],
) -> PaperValuesVerificationReport:
    """Local value checks, plus the provenance cross-check when requested.

    The paper-values layer only knows the ProvenanceVerifier interface;
    this composition point is the one place that picks the Seyval-backed
    implementation. The factory is called (and may fail) only when the
    cross-check actually runs, and any failure to consult Seyval degrades
    to `provenance.status == "unavailable"` rather than an exception —
    the caller decides whether unavailable is acceptable (local use) or
    fatal (CI).
    """
    report = await asyncio.to_thread(
        verify_paper_values, local_path, latex_template_name
    )
    if not (check_provenance and paper_values_configured(report)):
        return report
    used_dirs = await asyncio.to_thread(
        referenced_result_dirs, local_path, latex_template_name
    )
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
