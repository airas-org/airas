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
    verify_paper_record,
)
from airas.usecases.verification.seyval_provenance import SeyvalProvenanceVerifier


async def paper_values_full_report(
    local_path: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
    check_provenance: bool,
    seyval_client_factory: Callable[[], SeyvalClient],
) -> PaperValuesVerificationReport:
    report = await asyncio.to_thread(
        verify_paper_record, local_path, latex_template_name
    )
    if not (check_provenance and paper_values_configured(report)):
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
