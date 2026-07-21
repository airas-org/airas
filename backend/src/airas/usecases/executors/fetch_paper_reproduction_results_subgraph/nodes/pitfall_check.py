"""Deterministic (non-LLM) pitfall checks over the reproduction code / log.

A static-analysis checklist that must stay mechanical for auditability (random seed fixed, evidence
of training, no hardcoded result arrays, no undisclosed scale reduction, execution log present,
required deliverable present). The paper-vs-reproduction parameter cross-check is done
deterministically in parameter_check.py; metrics and everything else qualitative is left to the
judge LLM.
"""

from __future__ import annotations

import re

_SEED_RE = re.compile(
    r"(random_state\s*=|seed\s*=|manual_seed\(|set_seed\(|np\.random\.seed\(|random\.seed\()"
)
# Matches both real training/evaluation loops and AI-agent/LLM API calls (any provider).
_TRAIN_RE = re.compile(
    r"(\.fit\(|\.train\(|optimizer\.step\(|for\s+epoch|\.backward\(\)"
    r"|messages\.create\(|chat\.completions\.create\(|responses\.create\("
    r"|litellm\.completion\(|import\s+litellm"
    r"|import\s+anthropic|import\s+openai|import\s+google\.generativeai"
    r"|claude\s+-p|[\"']claude[\"'])"
)
_HARDCODE_RE = re.compile(
    r"\b(accuracy|accuracies|acc|loss|losses|result|results|score|scores)\w*\s*=\s*\[\s*[\d.]+",
    re.IGNORECASE,
)
# n_samples of up to 3 digits (<= 999) counts as a reduced scale.
_REDUCTION_RE = re.compile(
    r"(\[:\d+\]|\.sample\(|subset|n_samples\s*=\s*\d{1,3}\b)", re.IGNORECASE
)


def run_pitfall_checklist(
    reproduce_code: str | None,
    run_log: str | None,
    summary: str,
    repro_md: str | None = None,
    repro_png_base64: str | None = None,
) -> list[dict]:
    code = reproduce_code or ""
    checklist: list[dict] = []
    has_deliverable = repro_md is not None or repro_png_base64 is not None

    if not code:
        # Code-dependent checks cannot be judged without source.
        for item_id, label in (
            ("seed_fixed", "random seed fixed"),
            ("training_executed", "evidence of training/evaluation"),
            ("no_hardcoded_results", "suspected hardcoded result array"),
            ("scale_reduction_disclosed", "reduced experiment scale"),
        ):
            checklist.append(
                {
                    "id": item_id,
                    "label": label,
                    "status": "unknown",
                    "detail": "no code found",
                }
            )
    else:
        if _SEED_RE.search(code):
            checklist.append(
                {
                    "id": "seed_fixed",
                    "label": "random seed fixed",
                    "status": "pass",
                    "detail": "found seed-fixing code",
                }
            )
        else:
            checklist.append(
                {
                    "id": "seed_fixed",
                    "label": "random seed fixed",
                    "status": "fail",
                    "detail": "no seed-fixing code found",
                }
            )
        if _TRAIN_RE.search(code):
            checklist.append(
                {
                    "id": "training_executed",
                    "label": "evidence of training/evaluation",
                    "status": "pass",
                    "detail": "found a training/evaluation loop call",
                }
            )
        else:
            checklist.append(
                {
                    "id": "training_executed",
                    "label": "evidence of training/evaluation",
                    "status": "fail",
                    "detail": "no training/evaluation loop call found (may only be loading existing results)",
                }
            )

        hit = _HARDCODE_RE.search(code)
        if hit:
            checklist.append(
                {
                    "id": "no_hardcoded_results",
                    "label": "suspected hardcoded result array",
                    "status": "fail",
                    "detail": f"suspicious pattern found: {hit.group(0)[:80]}",
                }
            )
        else:
            checklist.append(
                {
                    "id": "no_hardcoded_results",
                    "label": "suspected hardcoded result array",
                    "status": "pass",
                    "detail": "no suspicious hardcoding pattern found",
                }
            )

        if _REDUCTION_RE.search(code):
            checklist.append(
                {
                    "id": "scale_reduction_disclosed",
                    "label": "reduced experiment scale",
                    "status": "fail",
                    "detail": "found code suggesting a scale reduction",
                }
            )
        else:
            checklist.append(
                {
                    "id": "scale_reduction_disclosed",
                    "label": "reduced experiment scale",
                    "status": "pass",
                    "detail": "no sign of scale reduction found",
                }
            )

    if run_log and run_log.strip():
        checklist.append(
            {
                "id": "execution_log_present",
                "label": "execution log present",
                "status": "pass",
                "detail": "run.log is present and non-empty",
            }
        )
    else:
        checklist.append(
            {
                "id": "execution_log_present",
                "label": "execution log present",
                "status": "unknown",
                "detail": "run.log not found or empty",
            }
        )

    has_summary = bool((summary or "").strip())
    if has_summary and has_deliverable:
        checklist.append(
            {
                "id": "required_artifacts_present",
                "label": "required deliverables present",
                "status": "pass",
                "detail": "summary and repro.(png|md) are both present",
            }
        )
    else:
        missing = [
            m
            for m, ok in (("summary", has_summary), ("repro.(png|md)", has_deliverable))
            if not ok
        ]
        checklist.append(
            {
                "id": "required_artifacts_present",
                "label": "required deliverables present",
                "status": "fail",
                "detail": f"missing: {', '.join(missing)}",
            }
        )

    return checklist


def format_evidence(checklist: list[dict]) -> str:
    lines = [
        "## Pitfall checklist (pre-computed deterministically — do not repeat this judgment)"
    ]
    for c in checklist:
        lines.append(f"- [{c['status']}] {c['label']}: {c['detail']}")
    return "\n".join(lines)
