from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pydantic import BaseModel, ValidationError

from airas.core.research_paths import (
    COMPARISON_KEY,
    COMPARISON_METRICS_FILENAME,
    METRICS_FILENAME,
    RECORD_PATH,
    RESULTS_DIR,
)
from airas.core.types.research_record import (
    AnyRun,
    ClaimDeclaration,
    EvalReport,
    InputRef,
    LeanClaim,
    LeanResult,
    LeanRun,
    LlmJudgeClaim,
    LlmJudgeResult,
    ResearchRecord,
    RunResult,
    SeyvalClaim,
    SeyvalResult,
    Verdict,
    VerifierKind,
)
from airas.core.types.run_provenance import (
    PROVENANCE_MANIFEST_PATH,
    RunProvenanceManifest,
)

# ------------------------------------------------------------ record.json


def record_path(local_repo_path: str) -> Path:
    return Path(local_repo_path).expanduser().resolve() / RECORD_PATH


def load_record(local_repo_path: str) -> ResearchRecord:
    path = record_path(local_repo_path)
    if not path.is_file():
        raise ValueError(f"{RECORD_PATH} not found under {path.parents[1]}")

    return ResearchRecord.model_validate_json(path.read_text(encoding="utf-8"))


def save_record(local_repo_path: str, record: ResearchRecord) -> Path:
    path = record_path(local_repo_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    # Defaults are omitted so the file reads as what was declared; containment
    # compares model dumps, not text, so omission changes nothing there.
    path.write_text(
        record.model_dump_json(indent=2, exclude_defaults=True) + "\n",
        encoding="utf-8",
    )
    return path


# ----------------------------------------------- updating the results layer


class _ClaimStatus(BaseModel):
    """A claim's state as recomputed from the run outputs on disk."""

    id: str
    # Every run under the claim has its verifier's report in the results
    # directory: the data the claim rests on is in. Whether the claim was
    # declared before those runs executed is not modelled yet (TODO).
    verified: bool
    # What the verifier concluded once verified; unset for seyval, whose
    # claim condition is not modelled yet.
    verdict: Verdict | None = None


def update_record_with_results(
    root: Path,
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    manifest: RunProvenanceManifest | None,
) -> tuple[list[_ClaimStatus], int]:
    # Results are appended, never replaced: running again adds an entry.
    # verified and verdict are set once and never back; a later disagreement
    # is a verification failure to report, not a value to overwrite.
    appended = 0
    for _, claim in record.active_claims():
        for _, run in claim.runs():
            result = derive_result(root, claim, run, metrics_data, manifest)
            if result is None:
                continue
            latest = run.latest_result()
            if latest is None or latest.model_dump() != result.model_dump():
                run.results.append(result)
                appended += 1

    statuses = compute_claim_statuses(record, runs_with_reports(root, record))
    claims = record.claim_index()
    for status in statuses:
        claim = claims[status.id]
        if status.verified:
            claim.verified = True
        if status.verdict and claim.verdict is None:
            claim.verdict = status.verdict
    return statuses, appended


def compute_claim_statuses(
    record: ResearchRecord, present_run_ids: set[str]
) -> list[_ClaimStatus]:
    statuses: list[_ClaimStatus] = []
    for _, claim in record.active_claims():
        runs = [run for _, run in claim.runs()]
        verified = bool(runs) and all(run.run_id in present_run_ids for run in runs)
        results = [r for r in (run.latest_result() for run in runs) if r is not None]
        statuses.append(
            _ClaimStatus(
                id=claim.id,
                verified=verified,
                verdict=(
                    _claim_verdict(claim, results)
                    if verified and len(results) == len(runs)
                    else None
                ),
            )
        )
    return statuses


# ------------------------------------------------ what the runs left on disk

_EVAL_INPUTS_DIRNAME = "eval_inputs"
_EVALUATION_DIRNAME = "evaluation"
# What each verifier leaves in .research/results/<run_id>/ to say "executed".
_VERIFIER_REPORT_FILENAME = {
    VerifierKind.SEYVAL: METRICS_FILENAME,
    VerifierKind.LEAN: "lean.json",
    VerifierKind.LLM_JUDGE: "judgment.json",
}


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
    return {
        run.run_id
        for _, claim in record.active_claims()
        for _, run in claim.runs()
        if _verifier_report_path(root, claim.verifier.kind, run.run_id).is_file()
    }


def load_eval_inputs_ref(root: Path, run_id: str) -> InputRef | None:
    for path in sorted(
        (root / RESULTS_DIR / run_id / _EVAL_INPUTS_DIRNAME).glob("*.json")
    ):
        return InputRef(
            path=str(path.relative_to(root)),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        )
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


def derive_result(
    root: Path,
    claim: ClaimDeclaration,
    run: AnyRun,
    metrics_data: dict[str, Any],
    manifest: RunProvenanceManifest | None,
) -> RunResult | None:
    if isinstance(claim, SeyvalClaim):
        # A seyval result is the platform's fact: without a manifest entry
        # there is nothing to copy.
        declared = manifest.dirs.get(run.run_id) if manifest else None
        if run.run_id not in metrics_data or declared is None:
            return None
        return SeyvalResult(
            id=declared.execution_id,
            commit=declared.commit_hash,
            eval_inputs=load_eval_inputs_ref(root, run.run_id),
            eval_report=load_eval_report(root, run.run_id),
            metrics=metrics_data[run.run_id],
        )
    payload = _read_json(_verifier_report_path(root, claim.verifier.kind, run.run_id))
    if not isinstance(payload, dict):
        return None
    try:
        if isinstance(claim, LeanClaim):
            return LeanResult(
                commit=payload.get("commit"),
                statement=payload.get("statement", ""),
                axioms=payload.get("axioms", []),
                errors=_lean_errors(claim, run, payload),
                warnings=payload.get("warnings", []),
            )
        votes = payload.get("votes", {})
        return LlmJudgeResult(
            id=payload.get("id", ""),
            commit=payload.get("commit"),
            inputs_sha256=payload["inputs_sha256"],
            verdict=payload["verdict"],
            errors=payload.get("errors", []),
            warnings=[f"votes split {votes}"] if len(votes) > 1 else [],
        )
    except (KeyError, ValueError):
        return None


def _verifier_report_path(root: Path, kind: VerifierKind, run_id: str) -> Path:
    return root / RESULTS_DIR / run_id / _VERIFIER_REPORT_FILENAME[kind]


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


# ------------------------------------------ what the verifier concluded

_SORRY_AXIOM = "sorryAx"


def _claim_verdict(claim: ClaimDeclaration, results: list[RunResult]) -> Verdict | None:
    if any(r.errors for r in results if not isinstance(r, SeyvalResult)):
        return "inconclusive"
    if isinstance(claim, LeanClaim):
        # Lean cannot refute: a proof that did not go through shows nothing.
        return "supported"
    if isinstance(claim, LlmJudgeClaim):
        verdicts = {r.verdict for r in results if isinstance(r, LlmJudgeResult)}
        if verdicts == {"supported"}:
            return "supported"
        return "refuted" if "refuted" in verdicts else "inconclusive"
    return None  # seyval's claim condition is not modelled yet


def _lean_errors(claim: LeanClaim, run: LeanRun, payload: dict[str, Any]) -> list[str]:
    errors = list(payload.get("errors", []))
    if errors:
        return errors
    built = _normalize_statement(payload.get("statement", ""))
    if built != _normalize_statement(run.params.statement):
        errors.append(f"statement differs from the declaration: built '{built}'")
    axioms = set(payload.get("axioms", []))
    if _SORRY_AXIOM in axioms:
        errors.append("the proof uses sorry")
    foreign = sorted(axioms - set(claim.verifier.allowed_axioms) - {_SORRY_AXIOM})
    if foreign:
        errors.append(f"depends on axioms outside allowed_axioms: {', '.join(foreign)}")
    return errors


def _normalize_statement(text: str) -> str:
    return " ".join(text.split())
