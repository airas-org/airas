"""Declaring hypotheses, claims and passages in the research record.

The record only ever grows: `preregister_record` writes the freeze commit
and `append_to_record` adds to it without touching what is already there.
"""

import asyncio
from pathlib import Path
from typing import Any

from pydantic import TypeAdapter

from airas.core.research_paths import RECORD_PATH
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.map_record_to_publication import TableSpec
from airas.core.types.research_record import (
    ChartDeclaration,
    ClaimDeclaration,
    Hypothesis,
    ResearchRecord,
)
from airas.research_record.lookup import (
    find_hypothesis,
    find_source,
)
from airas.research_record.passages import (
    add_passages,
)
from airas.research_record.store import (
    commit_record_paths,
    load_record,
    record_path,
    save_record,
)
from airas.research_record.verify import (
    verify_consistency,
    verify_literature,
)
from airas.usecases.publication.write_tex_files import (
    write_claims_tex,
)

_CLAIM: TypeAdapter[ClaimDeclaration] = TypeAdapter(ClaimDeclaration)


def _parse_hypotheses(hypotheses: list[dict[str, Any]] | None) -> list[Hypothesis]:
    return [Hypothesis.model_validate(h) for h in hypotheses or []]


async def preregister_record(
    local_path: str,
    hypotheses: list[dict[str, Any]],
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> dict[str, Any]:
    """Write the declarations into an empty record and commit the freeze point."""
    parsed = _parse_hypotheses(hypotheses)

    def _run() -> dict[str, Any]:
        path = record_path(local_path)
        if (
            path.is_file()
            and ResearchRecord.model_validate_json(
                path.read_text(encoding="utf-8")
            ).hypotheses
        ):
            raise ValueError(
                f"{path} already holds declarations — the record only ever "
                "grows; add declarations with append_to_record"
            )

        record = load_record(local_path) if path.is_file() else ResearchRecord()
        record.hypotheses = parsed
        problems = verify_consistency(record)
        if problems:
            raise ValueError("; ".join(problems))

        save_record(local_path, record)
        claims_tex = write_claims_tex(local_path, latex_template_name, record)
        freeze_commit = commit_record_paths(
            local_path,
            [RECORD_PATH, claims_tex],
            "prereg: declare the research record",
        )
        return {
            "record_path": str(path),
            "claims_tex_path": claims_tex,
            "hypotheses": {
                h.id: {
                    c.id: {d.id: [r.run_id for r in d.runs] for d in c.designs}
                    for c in h.claims
                }
                for h in parsed
            },
            "freeze_commit": freeze_commit,
            "next": (
                "this commit is the freeze point runs must descend from — "
                "write the prereg main.tex with \\input{claims.tex} where the "
                "claims are listed, then push to the staging ref"
            ),
        }

    return await asyncio.to_thread(_run)


async def append_to_record(
    local_path: str,
    hypotheses: list[dict[str, Any]] | None = None,
    hypothesis_id: str | None = None,
    claims: list[dict[str, Any]] | None = None,
    tables: list[dict[str, Any]] | None = None,
    charts: list[dict[str, Any]] | None = None,
    notes: list[str] | None = None,
    source_id: str | None = None,
    passages: list[dict[str, Any]] | None = None,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
) -> dict[str, Any]:
    """Append declarations under an existing record and commit them."""
    new_hypotheses = _parse_hypotheses(hypotheses)
    scoped = any(x for x in (claims, tables, charts, notes))
    if scoped and not hypothesis_id:
        raise ValueError(
            "claims, tables, charts and notes append under a hypothesis — "
            "pass hypothesis_id"
        )
    if passages and not source_id:
        raise ValueError("passages append under a source — pass source_id")

    def _run() -> dict[str, Any]:
        record = load_record(local_path)
        record.hypotheses.extend(new_hypotheses)
        counts = {"hypotheses": len(new_hypotheses)}
        if hypothesis_id:
            target = find_hypothesis(record, hypothesis_id)
            parsed_claims = [_CLAIM.validate_python(c) for c in claims or []]
            parsed_tables = [TableSpec.model_validate(t) for t in tables or []]
            parsed_charts = [ChartDeclaration.model_validate(c) for c in charts or []]
            target.claims.extend(parsed_claims)
            target.tables.extend(parsed_tables)
            target.charts.extend(parsed_charts)
            target.notes.extend(notes or [])
            counts.update(
                claims=len(parsed_claims),
                tables=len(parsed_tables),
                charts=len(parsed_charts),
                notes=len(notes or []),
            )
        if source_id:
            add_passages(find_source(record, source_id), passages or [])
            counts["passages"] = len(passages or [])
        root = Path(local_path).expanduser().resolve()
        problems = verify_consistency(record) + verify_literature(root, record)
        if problems:
            raise ValueError("; ".join(problems))
        save_record(local_path, record)
        claims_tex = write_claims_tex(local_path, latex_template_name, record)
        commit = commit_record_paths(
            local_path, [RECORD_PATH, claims_tex], "record: append declarations"
        )
        return {
            "record_path": str(record_path(local_path)),
            "claims_tex_path": claims_tex,
            "appended": counts,
            "commit": commit,
            "next": (
                "the appended declarations are committed — any run they "
                "should count for must execute this commit or a descendant"
            ),
        }

    return await asyncio.to_thread(_run)
