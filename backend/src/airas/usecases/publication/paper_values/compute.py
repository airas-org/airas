from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from airas.core.types.paper_values import (
    ComputedValue,
    PaperValues,
    ValueDeclaration,
)

RESULTS_DIR = ".research/results"
METRICS_FILENAME = "metrics.json"
COMPARISON_KEY = "comparison"
COMPARISON_METRICS_FILENAME = "aggregated_metrics.json"


def load_metrics_data(local_repo_path: str) -> dict[str, Any]:
    """Read every run's metrics from a local clone's working tree.

    Returns the same shape as ExperimentalResults.metrics_data: one entry
    per run directory under .research/results/ that has a metrics.json,
    plus 'comparison' for comparison/aggregated_metrics.json.
    """
    root = Path(local_repo_path).expanduser().resolve()
    results_dir = root / ".research" / "results"
    if not results_dir.is_dir():
        raise ValueError(f"No {RESULTS_DIR} directory under {root}")

    metrics_data: dict[str, Any] = {}
    for run_dir in sorted(results_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        filename = (
            COMPARISON_METRICS_FILENAME
            if run_dir.name == COMPARISON_KEY
            else METRICS_FILENAME
        )
        metrics_path = run_dir / filename
        if metrics_path.is_file():
            metrics_data[run_dir.name] = json.loads(
                metrics_path.read_text(encoding="utf-8")
            )
    if not metrics_data:
        raise ValueError(f"No {METRICS_FILENAME} found under {results_dir}")
    return metrics_data


def match_run_id(metrics_data: dict[str, Any], ref: str) -> str | None:
    """The results-directory key a ref addresses (longest prefix match)."""
    return max(
        (k for k in metrics_data if ref == k or ref.startswith(k + ".")),
        key=len,
        default=None,
    )


def used_result_dirs(
    declarations: list[ValueDeclaration], metrics_data: dict[str, Any]
) -> set[str]:
    """Every results directory the declarations draw values from."""
    dirs: set[str] = set()
    for declaration in declarations:
        for ref in declaration.refs:
            run_id = match_run_id(metrics_data, ref)
            if run_id is not None:
                dirs.add(run_id)
    return dirs


def resolve_ref(metrics_data: dict[str, Any], ref: str) -> float:
    """Resolve 'run_id.path.to.metric' to a number in the metrics data."""
    run_id = match_run_id(metrics_data, ref)
    if run_id is None:
        available = ", ".join(sorted(metrics_data))
        raise ValueError(f"'{ref}' matches no run id (available: {available})")

    node: Any = metrics_data[run_id]
    remainder = ref[len(run_id) + 1 :]
    for segment in remainder.split(".") if remainder else []:
        try:
            node = node[int(segment)] if isinstance(node, list) else node[segment]
        except (KeyError, IndexError, ValueError, TypeError):
            raise ValueError(
                f"'{ref}': nothing at '{segment}' in run '{run_id}'"
            ) from None
    if isinstance(node, bool) or not isinstance(node, (int, float)):
        raise ValueError(f"'{ref}' is not a number: {node!r}")
    return float(node)


def _require_arity(declaration: ValueDeclaration, arity: int) -> None:
    if len(declaration.refs) != arity:
        raise ValueError(
            f"'{declaration.key}': op '{declaration.op}' takes exactly "
            f"{arity} ref(s), got {len(declaration.refs)}"
        )


def evaluate(declaration: ValueDeclaration, metrics_data: dict[str, Any]) -> float:
    values = [resolve_ref(metrics_data, ref) for ref in declaration.refs]
    if declaration.op == "value":
        _require_arity(declaration, 1)
        return values[0]
    if declaration.op == "mean":
        return statistics.fmean(values)
    if declaration.op == "std":
        if len(values) < 2:
            raise ValueError(f"'{declaration.key}': std needs at least 2 refs")
        return statistics.stdev(values)
    if declaration.op == "diff":
        _require_arity(declaration, 2)
        return values[0] - values[1]
    _require_arity(declaration, 2)  # pct_improve
    if values[1] == 0:
        raise ValueError(f"'{declaration.key}': pct_improve baseline is 0")
    return (values[0] - values[1]) / abs(values[1]) * 100.0


def format_display(value: float, round_digits: int | None) -> str:
    if round_digits is not None:
        return f"{value:.{round_digits}f}"
    return f"{value:g}"


def compute_paper_values(
    declarations: list[ValueDeclaration], metrics_data: dict[str, Any]
) -> PaperValues:
    seen: set[str] = set()
    computed: list[ComputedValue] = []

    for declaration in declarations:
        if declaration.key in seen:
            raise ValueError(f"duplicate key '{declaration.key}'")

        seen.add(declaration.key)
        value = evaluate(declaration, metrics_data)
        computed.append(
            ComputedValue(
                **declaration.model_dump(),
                value=value,
                display=format_display(value, declaration.round),
            )
        )
    return PaperValues(values=computed)
