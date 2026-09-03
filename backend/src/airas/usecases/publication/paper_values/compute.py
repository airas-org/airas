from __future__ import annotations

import json
import statistics
from pathlib import Path
from typing import Any

from airas.core.research_paths import RESULTS_DIR
from airas.core.types.paper_values import PaperValue
from airas.core.types.research_record import (
    ClaimDeclaration,
    ResearchRecord,
    Target,
)
from airas.usecases.publication.paper_values.record import (
    active,
    ref_run_id,
    run_index,
    selected_execution,
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
    dirs: set[str] = set()
    refs = [
        ref
        for claim in active(record.hypothesis.claims, "id")
        for ref in claim.target.refs
    ]
    refs += [
        f"{row.run_id}.{column.ref_path}"
        for spec in active(record.tables, "key")
        for row in spec.rows
        for column in spec.columns
    ]
    for ref in refs:
        run_id = match_run_id(metrics_data, ref)
        if run_id is not None:
            dirs.add(run_id)
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


def _require_arity(target: Target, arity: int, claim_id: str) -> None:
    if len(target.refs) != arity:
        raise ValueError(
            f"'{claim_id}': op '{target.op}' takes exactly {arity} ref(s), "
            f"got {len(target.refs)}"
        )


def evaluate_target(
    target: Target, metrics_data: dict[str, Any], claim_id: str = "target"
) -> float:
    values = [resolve_ref(metrics_data, ref) for ref in target.refs]

    if target.op == "value":
        _require_arity(target, 1, claim_id)
        result = values[0]
    elif target.op == "mean":
        result = statistics.fmean(values)
    elif target.op == "std":
        if len(values) < 2:
            raise ValueError(f"'{claim_id}': std needs at least 2 refs")
        result = statistics.stdev(values)
    elif target.op == "diff":
        _require_arity(target, 2, claim_id)
        result = values[0] - values[1]
    else:  # pct_improve
        _require_arity(target, 2, claim_id)
        if values[1] == 0:
            raise ValueError(f"'{claim_id}': pct_improve baseline is 0")
        result = (values[0] - values[1]) / abs(values[1]) * 100.0

    return abs(result) if target.abs else result


def format_display(value: float, round_digits: int | None) -> str:
    if round_digits is not None:
        return f"{value:.{round_digits}f}"
    return f"{value:g}"


def claim_executions(record: ResearchRecord, claim: ClaimDeclaration) -> dict[str, str]:
    """Which execution supplied each run the claim's target reads.

    Recorded per realization so a number in the paper stays traceable to one
    execution even after the same configuration has been run again.
    """
    runs = run_index(record)
    used: dict[str, str] = {}
    for ref in claim.target.refs:
        run_id = ref_run_id(ref)
        run = runs.get(run_id)
        execution = selected_execution(run) if run else None
        if execution and execution.execution_id:
            used[run_id] = execution.execution_id
    return used


def compute_claim_values(
    record: ResearchRecord, metrics_data: dict[str, Any]
) -> dict[str, tuple[float, str, dict[str, str]]]:
    """Every active claim's measured value, display form and executions."""
    computed: dict[str, tuple[float, str, dict[str, str]]] = {}
    for claim in active(record.hypothesis.claims, "id"):
        value = evaluate_target(claim.target, metrics_data, claim.id)
        computed[claim.id] = (
            value,
            format_display(value, claim.target.round),
            claim_executions(record, claim),
        )
    return computed


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

    Three forms, all writable before any run exists — which is what lets the
    preregistered paper be written in full:

      <claim_id>.value          the claim's target, for derived numbers
      <run_id>.params.<path>    a parameter the run actually executed with
      <run_id>.<metric path>    a metric of a declared run, read directly

    The params form puts the experimental setup under the same guarantee as
    the results: without it a paper can state a batch size the run never
    used and nothing objects. It reads the platform's record of the
    dispatch, so citing a parameter cites what ran, not what the code said
    it was doing.
    """
    head, _, tail = ref.partition(".")

    claims = {c.id: c for c in active(record.hypothesis.claims, "id")}
    if head in claims and tail == "value":
        claim = claims[head]
        value = evaluate_target(claim.target, metrics_data, claim.id)
        return format_display(value, claim.target.round)

    runs = run_index(record)
    if head in runs and tail.startswith("params."):
        execution = selected_execution(runs[head])
        if execution is None:
            raise ValueError(f"'{ref}': run '{head}' has no execution")
        resolved = execution.parameters or execution.overrides
        try:
            node = _walk_any(resolved, tail[len("params.") :])
        except (KeyError, IndexError, ValueError, TypeError):
            raise ValueError(
                f"'{ref}': the platform did not report this parameter for run '{head}'"
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
    claims = {c.id: c for c in active(record.hypothesis.claims, "id")}
    for ref in dict.fromkeys(used_keys):
        try:
            display = resolve_paper_ref(record, metrics_data, ref)
        except ValueError:
            undefined.append(ref)
            continue
        claim = claims.get(ref.partition(".")[0])
        derivation = (
            f"{claim.target.op}({', '.join(claim.target.refs)})"
            if claim and ref.endswith(".value")
            else ref
        )
        values.append(PaperValue(ref=ref, display=display, derivation=derivation))
    return values, undefined
