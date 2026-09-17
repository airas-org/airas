from __future__ import annotations

from typing import Any

from airas.core.types.research_record import walk_metric_path


def resolve_ref(metrics_data: dict[str, Any], ref: str) -> float:
    """Resolve '<run_id>.<metric path>' against the committed results files."""
    run_id = max(
        (k for k in metrics_data if ref == k or ref.startswith(k + ".")),
        key=len,
        default=None,
    )
    if run_id is None:
        available = ", ".join(sorted(metrics_data))
        raise ValueError(f"'{ref}' matches no run id (available: {available})")
    try:
        return walk_metric_path(metrics_data[run_id], ref[len(run_id) + 1 :])
    except ValueError as e:
        raise ValueError(f"'{ref}': {e} in run '{run_id}'") from None
