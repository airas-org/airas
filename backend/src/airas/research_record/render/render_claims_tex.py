from __future__ import annotations

from pathlib import Path
from typing import Any

from airas.core.types.research_record import (
    LeanClaim,
    LeanResult,
    LiteratureSource,
    ResearchRecord,
    SeyvalClaim,
    active,
)
from airas.research_record.read.read_run_outputs import load_metrics_data
from airas.research_record.render._latex_text import AUTO_GENERATED_HEADER, latex_text

CLAIMS_TEX_FILENAME = "claims.tex"


def _tt(text: str) -> str:
    return rf"\texttt{{\detokenize{{{text}}}}}"


def _lean_evidence_lines(claim: LeanClaim) -> list[str]:
    lines: list[str] = []
    for _, run in claim.runs():
        result = run.latest_result()
        if not isinstance(result, LeanResult):
            lines.append(rf"  \emph{{Evidence:}} run {_tt(run.run_id)}, pending.")
            continue
        where = ", ".join(
            part
            for part in (
                f"execution {_tt(result.id)}" if result.id else "",
                f"commit {_tt(result.commit[:12])}" if result.commit else "",
            )
            if part
        )
        axioms = ", ".join(_tt(a) for a in result.axioms) or "none"
        lines.append(
            rf"  \emph{{Evidence:}} run {_tt(run.run_id)}, {where}; axioms: {axioms}."
        )
    return lines


def _passages(ids: list[str]) -> str:
    return ", ".join(_tt(pid) for pid in ids)


def _cited_passages_line(claim: Any) -> str | None:
    parts = [_passages(claim.cites_passages)] if claim.cites_passages else []
    if isinstance(claim, SeyvalClaim) and claim.criterion.reference_passage:
        parts.append(f"criterion: {_tt(claim.criterion.reference_passage)}")
    for design in active(claim.designs, "id"):
        if design.cites_passages:
            parts.append(f"{_tt(design.id)}: {_passages(design.cites_passages)}")
        for run in active(design.runs, "run_id"):
            if run.cites_passages:
                parts.append(f"{_tt(run.run_id)}: {_passages(run.cites_passages)}")
    return rf"  \emph{{Cites:}} {'; '.join(parts)}." if parts else None


def _literature_lines(literature: list[LiteratureSource]) -> list[str]:
    # The (statement, quote) pairs reach the reviewer through the PDF: the
    # declarations above name passages, these are the passages verbatim.
    lines = [r"\noindent\textbf{Sources.}"]
    for source in literature:
        year = f" ({source.year})" if source.year else ""
        lines.append(
            rf"\noindent\textbf{{{source.id.upper()}}} {_tt(source.bibkey)}: "
            + latex_text(source.title)
            + f"{year}."
        )
        passages = active(source.passages, "id")
        if not passages:
            continue
        lines.append(r"\begin{itemize}")
        for passage in passages:
            where = "" if passage.anchor == "text" else f" {passage.anchor}"
            lines.append(
                rf"\item[{_tt(passage.id)}] ({passage.node_type}{where}) "
                + "``"
                + latex_text(passage.quote)
                + "''"
            )
        lines.append(r"\end{itemize}")
    return lines


def render_claims_tex(record: ResearchRecord, metrics_data: dict[str, Any]) -> str:
    # Deterministic from (record, metrics) alone — no commit link — so the
    # freeze commit can carry it before any run exists.
    ops = {">=": r"\geq", "<=": r"\leq", ">": ">", "<": "<"}
    lines = [AUTO_GENERATED_HEADER]
    for hypothesis in record.active_hypotheses():
        lines += [
            rf"\noindent\textbf{{{hypothesis.id.upper()}.}} "
            + latex_text(hypothesis.statement),
        ]
        if hypothesis.grounded_on:
            lines.append(rf"\emph{{Grounded on:}} {_passages(hypothesis.grounded_on)}.")
        lines.append(r"\begin{enumerate}")
        for claim in active(hypothesis.claims, "id"):
            lines.append(
                rf"\item[\textbf{{{claim.id.upper()}}}] {latex_text(claim.statement)}"
            )
            lines.append(rf"  \emph{{Rationale:}} {latex_text(claim.rationale)}")
            if cited := _cited_passages_line(claim):
                lines.append(cited)
            if isinstance(claim, SeyvalClaim):
                c = claim.criterion
                reference = (
                    f"{_tt(c.reference)}.{_tt(c.metric)}"
                    if isinstance(c.reference, str)
                    else f"{c.reference:g}"
                )
                lines.append(
                    rf"  \emph{{Criterion:}} {_tt(c.subject)}.{_tt(c.metric)} $-$ "
                    rf"{reference} ${ops[c.op]} {c.margin:g}$."
                )
                p = claim.prediction
                lines.append(
                    rf"  \emph{{Prediction:}} $[{p.low:g}, {p.high:g}]$ ({latex_text(p.basis)})."
                )
                try:
                    observed = f"{c.observed(metrics_data):g}"
                except (KeyError, ValueError):
                    observed = "pending"
                lines.append(rf"  \emph{{Observed:}} {observed}.")
            if isinstance(claim, LeanClaim):
                lines += _lean_evidence_lines(claim)
            lines.append(rf"  \emph{{Verdict:}} {claim.verdict or 'pending'}.")
        lines.append(r"\end{enumerate}")
        if hypothesis.assumptions:
            lines.append(
                r"\noindent\emph{Assumed, so that the claims together imply "
                rf"{hypothesis.id.upper()}:}}"
            )
            lines.append(r"\begin{itemize}")
            lines += [rf"\item {latex_text(a)}" for a in hypothesis.assumptions]
            lines.append(r"\end{itemize}")
    if literature := record.active_literature():
        lines += _literature_lines(literature)
    return "\n".join(lines) + "\n"


def write_claims_tex(local_path: str, template: str, record: ResearchRecord) -> str:
    root = Path(local_path).expanduser().resolve()
    try:
        metrics_data = load_metrics_data(local_path)
    except ValueError:
        metrics_data = {}  # prereg stage: every claim renders as pending
    relpath = f".research/latex/{template}/{CLAIMS_TEX_FILENAME}"
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_claims_tex(record, metrics_data), encoding="utf-8")
    return relpath
