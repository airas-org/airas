import asyncio
import contextlib
import shutil
from pathlib import Path
from typing import Any

import httpx
from pydantic import TypeAdapter

from airas.core.research_paths import RECORD_PATH, SOURCES_DIR
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.map_record_to_publication import TableSpec
from airas.core.types.research_record import (
    ChartDeclaration,
    ClaimDeclaration,
    Hypothesis,
    LiteratureSource,
    ResearchRecord,
)
from airas.core.types.run_provenance import RunProvenanceManifest
from airas.infra.airas_db_index import AirasDbPaperSearchIndex
from airas.infra.airas_records_index import AirasRecordsIndex
from airas.infra.arxiv_client import ArxivClient
from airas.infra.local_git import commit_paths, normalize_git_url, remote_origin_url
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.research_record.read.derive_results import (
    ClaimStatus,
    compute_claim_statuses,
    derive_result,
)
from airas.research_record.read.find_by_id import find_hypothesis, find_source
from airas.research_record.read.load_record import load_record, record_path
from airas.research_record.read.read_run_outputs import (
    load_metrics_data,
    load_provenance_manifest,
    runs_with_reports,
)
from airas.research_record.read.scan_main_tex import scan_main_tex
from airas.research_record.render.render_claims_tex import write_claims_tex
from airas.research_record.render.render_paper_values import (
    VALUES_TEX_FILENAME,
    record_link_commit,
    render_values_tex,
    resolve_paper_values,
)
from airas.research_record.render.render_references_bib import write_references_bib
from airas.research_record.render.render_tables import TABLES_DIR_NAME, render_table_tex
from airas.research_record.update._add_literatures import add_literatures
from airas.research_record.update._add_quoted_passages import add_quoted_passages
from airas.research_record.update._resolve_literatures import resolve_literatures
from airas.research_record.verify.verify_record import verify_record_offline

_CLAIM: TypeAdapter[ClaimDeclaration] = TypeAdapter(ClaimDeclaration)


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


def _discard(root: Path, snapshots: list[str]) -> None:
    for relpath in snapshots:
        shutil.rmtree((root / relpath).parent, ignore_errors=True)
    with contextlib.suppress(OSError):
        (root / SOURCES_DIR).rmdir()


def _append_run_results(
    root: Path,
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    manifest: RunProvenanceManifest | None,
) -> tuple[list[ClaimStatus], int]:
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


def _write_paper_values(
    root: Path,
    record: ResearchRecord,
    metrics_data: dict[str, Any],
    template: str,
) -> tuple[dict[str, Any], list[str]]:
    """values.tex and tables/ from the record as committed; the paths to commit."""
    latex_dir = root / ".research" / "latex" / template
    latex_dir.mkdir(parents=True, exist_ok=True)
    main_tex = latex_dir / "main.tex"
    used_keys = (
        scan_main_tex(main_tex.read_text(encoding="utf-8"))[1]
        if main_tex.is_file()
        else []
    )
    paper_values, _ = resolve_paper_values(record, metrics_data, used_keys)
    remote = remote_origin_url(root)
    values_tex = latex_dir / VALUES_TEX_FILENAME
    values_tex.write_text(
        render_values_tex(
            paper_values,
            normalize_git_url(remote) if remote else None,
            record_link_commit(root),
        ),
        encoding="utf-8",
    )
    paths = [f".research/latex/{template}/{VALUES_TEX_FILENAME}"]
    tables: dict[str, str] = {}
    if specs := record.active_tables():
        tables_dir = latex_dir / TABLES_DIR_NAME
        tables_dir.mkdir(parents=True, exist_ok=True)
        for spec in specs:
            table_path = tables_dir / f"{spec.key}.tex"
            table_path.write_text(
                render_table_tex(spec, metrics_data), encoding="utf-8"
            )
            tables[spec.key] = str(table_path)
        # git add is fatal on a pathspec that matches nothing
        paths.append(f".research/latex/{template}/{TABLES_DIR_NAME}")
    return {
        "values": {v.ref: v.display for v in paper_values},
        "tables": tables,
        "values_tex_path": str(values_tex),
    }, paths


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
    run_results: bool = False,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    literature: list[dict[str, Any]] | None = None,
    *,
    search_index: AirasDbPaperSearchIndex | None = None,
    records_index: AirasRecordsIndex | None = None,
    arxiv_client: ArxivClient | None = None,
    semantic_scholar_client: SemanticScholarClient | None = None,
    http: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    """Append to an existing record — declarations the agent passes, and with
    `run_results` what the run outputs on disk say — then re-render the paper
    files the record feeds and commit."""
    new_hypotheses = [Hypothesis.model_validate(h) for h in hypotheses or []]
    materials = (
        await resolve_literatures(
            literature,
            search_index=_required(search_index, "search_index"),
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
    if any(x for x in (claims, tables, charts, notes)) and not hypothesis_id:
        raise ValueError(
            "claims, tables, charts and notes append under a hypothesis — "
            "pass hypothesis_id"
        )
    if passages and not source_id:
        raise ValueError("passages append under a source — pass source_id")

    def _run() -> dict[str, Any]:
        record = load_record(local_path)
        root = Path(local_path).expanduser().resolve()
        snapshots: list[str] = []
        try:
            return _append(record, root, snapshots)
        except Exception:
            _discard(root, snapshots)
            raise

    def _append(
        record: ResearchRecord, root: Path, snapshots: list[str]
    ) -> dict[str, Any]:
        sources, written = add_literatures(root, record, materials)
        snapshots.extend(written)
        for source, material in zip(sources, materials, strict=True):
            add_quoted_passages(source, material.passages)
        registered = _registered(sources)
        record.hypotheses.extend(new_hypotheses)
        counts: dict[str, Any] = {"hypotheses": len(new_hypotheses)}
        if materials:
            counts["literature"] = registered
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
            add_quoted_passages(find_source(record, source_id), passages or [])
            counts["passages"] = len(passages or [])

        extra: dict[str, Any] = {}
        metrics_data: dict[str, Any] = {}
        if run_results:
            try:
                metrics_data = load_metrics_data(local_path)
            except ValueError:
                pass  # a record verified by lean or llm_judge alone has no metrics
            statuses, appended = _append_run_results(
                root, record, metrics_data, load_provenance_manifest(root)
            )
            counts["run_results"] = appended
            extra["claims"] = {
                s.id: {"verified": s.verified, "verdict": s.verdict} for s in statuses
            }

        problems = verify_record_offline(root, record)
        if problems:
            raise ValueError("; ".join(problems))
        record.save(local_path)

        paths = [RECORD_PATH, *snapshots]
        if run_results:
            # values.tex links the commit that holds record.json, so that
            # commit has to exist first; the second one leaves record.json alone.
            commit_paths(root, paths, "record: append run results")
            extra["record_commit"] = record_link_commit(root)
            paper, paper_paths = _write_paper_values(
                root, record, metrics_data, latex_template_name
            )
            extra.update(paper)
            paths = paper_paths
        claims_tex = write_claims_tex(local_path, latex_template_name, record)
        paths.append(claims_tex)
        if materials:
            paths.append(write_references_bib(local_path, latex_template_name, record))
        commit = commit_paths(root, paths, "record: append")
        return {
            "record_path": str(record_path(local_path)),
            "claims_tex_path": claims_tex,
            "appended": counts,
            **extra,
            "commit": commit,
            "next": (
                "the appended declarations are committed — any run they "
                "should count for must execute this commit or a descendant"
            ),
        }

    return await asyncio.to_thread(_run)
