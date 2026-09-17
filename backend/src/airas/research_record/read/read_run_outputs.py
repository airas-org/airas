from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from airas.core.research_paths import (
    COMPARISON_KEY,
    COMPARISON_METRICS_FILENAME,
    METRICS_FILENAME,
    RESULTS_DIR,
)
from airas.core.types.research_record import (
    EvalReport,
    InputRef,
    ResearchRecord,
    VerifierKind,
)
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    RunProvenanceManifest,
)

_EVAL_INPUTS_DIRNAME = "eval_inputs"
_EVALUATION_DIRNAME = "evaluation"
# What each verifier leaves in .research/results/<run_id>/ to say "executed".
_VERIFIER_REPORT_FILENAME = {
    VerifierKind.SEYVAL: METRICS_FILENAME,
    VerifierKind.LEAN: "lean.json",
    VerifierKind.LLM_JUDGE: "judgment.json",
}
# The reports that are not metrics.json, for code that only has a directory.
VERIFIER_REPORT_FILENAMES = tuple(
    name
    for kind, name in _VERIFIER_REPORT_FILENAME.items()
    if kind != VerifierKind.SEYVAL
)


def load_metrics_data(local_repo_path: str) -> dict[str, Any]:
    results_dir = Path(local_repo_path).expanduser().resolve() / RESULTS_DIR
    if not results_dir.is_dir():
        raise ValueError(f"No {RESULTS_DIR} directory under {results_dir.parent}")
    metrics_data: dict[str, Any] = {}
    for run_dir in sorted(p for p in results_dir.iterdir() if p.is_dir()):
        filename = (
            COMPARISON_METRICS_FILENAME
            if run_dir.name == COMPARISON_KEY
            else METRICS_FILENAME
        )
        if (run_dir / filename).is_file():
            metrics_data[run_dir.name] = _read_json(run_dir / filename)
    if not metrics_data:
        raise ValueError(f"No {METRICS_FILENAME} found under {results_dir}")
    return metrics_data


def load_provenance_manifest(root: Path) -> RunProvenanceManifest | None:
    try:
        return RunProvenanceManifest.model_validate_json(
            (root / PROVENANCE_MANIFEST_PATH).read_text(encoding="utf-8")
        )
    except (OSError, ValidationError, ValueError):
        return None


def runs_with_reports(root: Path, record: ResearchRecord) -> set[str]:
    """The declared runs whose verifier report is on disk and readable. A
    file that does not parse is no report: the run stays unexecuted rather
    than verified with nothing to check."""
    return {
        run.run_id
        for _, claim in record.active_claims()
        for _, run in claim.runs()
        if isinstance(
            _read_json(_verifier_report_path(root, claim.verifier.kind, run.run_id)),
            dict,
        )
    }


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_eval_inputs_ref(root: Path, run_id: str) -> InputRef | None:
    for path in sorted(
        (root / RESULTS_DIR / run_id / _EVAL_INPUTS_DIRNAME).glob("*.json")
    ):
        return InputRef(path=str(path.relative_to(root)), sha256=file_sha256(path))
    return None


def load_eval_report(root: Path, run_id: str) -> EvalReport | None:
    for path in sorted(
        (root / RESULTS_DIR / run_id / _EVALUATION_DIRNAME).glob("*.json")
    ):
        payload = _read_json(path)
        if payload is None:
            return None
        provenance = payload.get("provenance") or {}
        return EvalReport(
            task_type=payload.get("task_type", path.stem),
            task_signature=provenance.get("task_signature"),
            inputs_sha256=provenance.get("inputs_sha256"),
            versions={k: str(v) for k, v in (provenance.get("versions") or {}).items()},
            metrics={
                k: float(v)
                for k, v in (payload.get("metrics") or {}).items()
                if isinstance(v, (int, float)) and not isinstance(v, bool)
            },
            curves=payload.get("curves") or {},
            inputs_summary=payload.get("inputs_summary") or {},
            skipped=payload.get("skipped") or {},
        )
    return None


def _verifier_report_path(root: Path, kind: VerifierKind, run_id: str) -> Path:
    return root / RESULTS_DIR / run_id / _VERIFIER_REPORT_FILENAME[kind]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
