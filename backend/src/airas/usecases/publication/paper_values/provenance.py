from __future__ import annotations

from typing import Protocol

from airas.core.types.paper_values import ProvenanceCheckResult
from airas.usecases.publication.paper_values.compute import (
    COMPARISON_KEY,
    COMPARISON_METRICS_FILENAME,
    METRICS_FILENAME,
    RESULTS_DIR,
)


class ProvenanceVerifier(Protocol):
    """Answers: is each local metrics file backed by a real, completed run?

    Implementations consult an execution platform's own storage (which
    the writing agent cannot write to) — e.g. Seyval's per-run S3, or a
    CI provider's artifact store. The paper-values layer only depends on
    this interface, never on a specific platform.
    """

    async def verify(
        self, local_repo_path: str, used_dirs: set[str]
    ) -> ProvenanceCheckResult: ...


def metrics_repo_path(dir_name: str) -> str:
    """Repository-relative path of the metrics file for a results dir."""
    filename = (
        COMPARISON_METRICS_FILENAME if dir_name == COMPARISON_KEY else METRICS_FILENAME
    )
    return f"{RESULTS_DIR}/{dir_name}/{filename}"
