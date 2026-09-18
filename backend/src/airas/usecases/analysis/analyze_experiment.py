import json
from pathlib import Path
from typing import Any

from jinja2 import Environment
from pydantic import BaseModel

from airas.core.llm_config import NodeLLMConfig
from airas.core.types.research_record import ResearchRecord, SeyvalClaim, active
from airas.infra.litellm_client import LiteLLMClient
from airas.research_record.read.derive_results import compute_claim_statuses
from airas.research_record.read.load_record import load_record
from airas.research_record.read.read_run_outputs import (
    load_metrics_data,
    runs_with_reports,
)
from airas.usecases.analysis.analyze_experiment_prompt import analyze_experiment_prompt


class LLMOutput(BaseModel):
    analysis_report: str


def analysis_context(
    record: ResearchRecord, metrics: dict[str, Any], reported_run_ids: set[str]
) -> dict[str, Any]:
    """What the analyst is shown: every live hypothesis and claim with its
    frozen criterion and prediction, the observed difference, and the verdict
    derived from the run outputs."""
    verdicts = {
        s.id: s.verdict for s in compute_claim_statuses(record, reported_run_ids)
    }
    hypotheses = []
    for h in record.active_hypotheses():
        claims = []
        for c in active(h.claims, "id"):
            entry: dict[str, Any] = {
                "id": c.id,
                "statement": c.statement,
                "rationale": c.rationale,
                "verdict": c.verdict or verdicts.get(c.id),
                "criterion": None,
            }
            if isinstance(c, SeyvalClaim):
                k = c.criterion
                reference = (
                    f"{k.reference}.{k.metric}"
                    if isinstance(k.reference, str)
                    else k.reference
                )
                try:
                    observed: float | None = k.observed(metrics)
                except (KeyError, ValueError):
                    observed = None
                entry.update(
                    criterion=f"{k.subject}.{k.metric} - {reference} {k.op} {k.margin:g}",
                    prediction=c.prediction,
                    observed=observed,
                    in_prediction=(
                        observed is not None
                        and c.prediction.low <= observed <= c.prediction.high
                    ),
                )
            claims.append(entry)
        hypotheses.append(
            {
                "id": h.id,
                "statement": h.statement,
                "assumptions": h.assumptions,
                "notes": h.notes,
                "claims": claims,
            }
        )
    return {
        "hypotheses": hypotheses,
        "metrics": json.dumps(metrics, indent=1, ensure_ascii=False) if metrics else "",
    }


def analysis_context_of(local_path: str) -> dict[str, Any]:
    root = Path(local_path).expanduser().resolve()
    record = load_record(local_path)
    try:
        metrics = load_metrics_data(local_path)
    except ValueError:
        metrics = {}
    return analysis_context(record, metrics, runs_with_reports(root, record))


def render_analysis_prompt(context: dict[str, Any]) -> str:
    return Environment().from_string(analyze_experiment_prompt).render(context)


async def analyze_experiment(
    local_path: str, *, litellm_client: LiteLLMClient, llm_config: NodeLLMConfig
) -> dict[str, Any]:
    context = analysis_context_of(local_path)
    output = await litellm_client.structured_output(
        message=render_analysis_prompt(context),
        data_model=LLMOutput,
        llm_name=llm_config.llm_name,
        params=llm_config.params,
    )
    if output is None:
        raise ValueError("No response from LLM in analyze_experiment.")
    return {
        "analysis": output.analysis_report,
        "claims": [
            {k: c[k] for k in ("id", "verdict", "observed") if k in c}
            for h in context["hypotheses"]
            for c in h["claims"]
        ],
    }
