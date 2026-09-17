import asyncio
from pathlib import Path
from typing import Any

import httpx

from airas.core.research_paths import RECORD_PATH, REFERENCES_BIB_FILENAME
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.research_record import (
    Hypothesis,
    LiteratureSource,
    ResearchRecord,
)
from airas.infra.airas_records_index import AirasRecordsIndex
from airas.infra.arxiv_client import ArxivClient
from airas.infra.local_git import commit_paths, restore_paths
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.research_record.read.load_record import load_record, record_path
from airas.research_record.render.render_claims_tex import (
    CLAIMS_TEX_FILENAME,
    write_claims_tex,
)
from airas.research_record.render.render_references_bib import write_references_bib
from airas.research_record.update._add_literatures import add_literatures
from airas.research_record.update._add_quoted_passages import add_quoted_passages
from airas.research_record.update._resolve_literatures import resolve_literatures
from airas.research_record.verify.verify_record import verify_record_offline


def _required(client: Any, name: str) -> Any:
    if client is None:
        raise ValueError(f"literature entries need {name} to be verified")
    return client


def _registered(sources: list[LiteratureSource]) -> dict[str, Any]:
    return {
        s.id: {
            "bibkey": s.bibkey,
            "title": s.title,
            "fulltext": s.fulltext.path if s.fulltext else None,
            "passages": [p.id for p in s.passages],
            "verified_by": s.verified_by,
        }
        for s in sources
    }


async def preregister_record(
    local_path: str,
    hypotheses: list[dict[str, Any]],
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    literature: list[dict[str, Any]] | None = None,
    *,
    records_index: AirasRecordsIndex | None = None,
    arxiv_client: ArxivClient | None = None,
    semantic_scholar_client: SemanticScholarClient | None = None,
    http: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """The literature, then the declarations, into an empty record; one
    commit is the freeze point."""
    parsed = [Hypothesis.model_validate(h) for h in hypotheses or []]
    materials = (
        await resolve_literatures(
            literature,
            records_index=_required(records_index, "records_index"),
            arxiv_client=_required(arxiv_client, "arxiv_client"),
            semantic_scholar_client=_required(
                semantic_scholar_client, "semantic_scholar_client"
            ),
            http=_required(http, "http"),
        )
        if literature
        else []
    )

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
        root = Path(local_path).expanduser().resolve()
        snapshots: list[str] = []
        try:
            sources, written = add_literatures(root, record, materials)
            snapshots.extend(written)
            for source, material in zip(sources, materials, strict=True):
                add_quoted_passages(source, material.passages)
            registered = _registered(sources)
            record.hypotheses = parsed
            problems = verify_record_offline(root, record)
            if problems:
                raise ValueError("; ".join(problems))
            record.save(local_path)
            claims_tex = write_claims_tex(local_path, latex_template_name, record)
            paths = [RECORD_PATH, claims_tex, *snapshots]
            if record.literature:
                paths.append(
                    write_references_bib(local_path, latex_template_name, record)
                )
            freeze_commit = commit_paths(
                root, paths, "prereg: declare the research record"
            )
        except Exception:
            latex = f".research/latex/{latex_template_name}"
            restore_paths(
                root,
                [
                    RECORD_PATH,
                    f"{latex}/{CLAIMS_TEX_FILENAME}",
                    f"{latex}/{REFERENCES_BIB_FILENAME}",
                    *snapshots,
                ],
            )
            raise
        return {
            "record_path": str(path),
            "claims_tex_path": claims_tex,
            "sources": registered,
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
