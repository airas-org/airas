from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from airas.core.research_paths import RESULTS_DIR
from airas.core.types.paper_values import PaperValue
from airas.core.types.research_record import ResearchRecord
from airas.usecases.publication.paper_values.record import (
    active,
    all_hypotheses,
    run_index,
)

METRICS_FILENAME = "metrics.json"
COMPARISON_KEY = "comparison"
COMPARISON_METRICS_FILENAME = "aggregated_metrics.json"


def load_metrics_data(local_repo_path: str) -> dict[str, Any]:
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
    return max(
        (k for k in metrics_data if ref == k or ref.startswith(k + ".")),
        key=len,
        default=None,
    )


def used_result_dirs(record: ResearchRecord, metrics_data: dict[str, Any]) -> set[str]:
    """Every results directory a declared run or table row reads."""
    dirs = {run_id for run_id in run_index(record) if run_id in metrics_data}
    for hypothesis in all_hypotheses(record):
        for spec in active(hypothesis.tables, "key"):
            for row in spec.rows:
                if row.run_id in metrics_data:
                    dirs.add(row.run_id)
    return dirs


def _walk(node: Any, remainder: str, ref: str, where: str) -> float:
    for segment in remainder.split(".") if remainder else []:
        try:
            node = node[int(segment)] if isinstance(node, list) else node[segment]
        except (KeyError, IndexError, ValueError, TypeError):
            raise ValueError(f"'{ref}': nothing at '{segment}' in {where}") from None
    if isinstance(node, bool) or not isinstance(node, (int, float)):
        raise ValueError(f"'{ref}' is not a number: {node!r}")
    return float(node)


def resolve_ref(metrics_data: dict[str, Any], ref: str) -> float:
    """Resolve '<run_id>.<metric path>' against the committed results files."""
    run_id = match_run_id(metrics_data, ref)
    if run_id is None:
        available = ", ".join(sorted(metrics_data))
        raise ValueError(f"'{ref}' matches no run id (available: {available})")
    return _walk(metrics_data[run_id], ref[len(run_id) + 1 :], ref, f"run '{run_id}'")


def format_display(value: float, round_digits: int | None) -> str:
    if round_digits is not None:
        return f"{value:.{round_digits}f}"
    return f"{value:g}"


def _walk_any(node: Any, path: str) -> Any:
    for segment in path.split(".") if path else []:
        node = node[int(segment)] if isinstance(node, list) else node[segment]
    return node


def resolve_paper_ref(
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    ref: str,
) -> str:
    """Resolve what \\airasval{...} addresses, returning what it prints.

    Two forms, both writable before any run exists — which is what lets the
    preregistered paper be written in full:

      <run_id>.params.<path>    a condition the run was declared with
      <run_id>.<metric path>    a metric of a declared run, read directly

    The params form reads the declaration; the gate checks that declaration
    against what the platform recorded for the dispatch, so citing a batch
    size cites a condition the run was held to, not what the code said it
    was doing. Derived numbers (a claim's target) are not modelled yet.
    """
    head, _, tail = ref.partition(".")

    runs = run_index(record)
    if head in runs and tail.startswith("params."):
        try:
            node = _walk_any(runs[head].params, tail[len("params.") :])
        except (KeyError, IndexError, ValueError, TypeError):
            raise ValueError(
                f"'{ref}': run '{head}' declares no such parameter"
            ) from None
        if isinstance(node, bool) or isinstance(node, (dict, list)):
            raise ValueError(f"'{ref}' is not a scalar: {node!r}")
        # Parameters are legitimately strings ("cifar10", "jacob_cov"), so
        # only numbers get rounded; anything else prints as written.
        return (
            format_display(float(node), None)
            if isinstance(node, (int, float))
            else str(node)
        )

    return format_display(resolve_ref(metrics_data, ref), None)


def resolve_paper_values(
    record: ResearchRecord, metrics_data: dict[str, Any], used_keys: list[str]
) -> tuple[list[PaperValue], list[str]]:
    """Every \\airasval the paper uses, in the order it uses them.

    Shared by the tool that writes values.tex and the check that regenerates
    it: two builders would have to agree byte-for-byte forever, and the first
    time they disagreed the regeneration check would fail on a paper nobody
    had touched.
    """
    values: list[PaperValue] = []
    undefined: list[str] = []
    for ref in dict.fromkeys(used_keys):
        try:
            display = resolve_paper_ref(record, metrics_data, ref)
        except ValueError:
            undefined.append(ref)
            continue
        values.append(PaperValue(ref=ref, display=display, derivation=ref))
    return values, undefined
