"""Pinning the papers and repositories the research draws on."""

import asyncio
import contextlib
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, get_args

import httpx

from airas.core.research_paths import (
    RECORD_PATH,
    SOURCES_DIR,
)
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.research_record import (
    LiteratureSource,
    ResearchRecord,
)
from airas.infra.arxiv_client import ArxivClient
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.research_record.ids import (
    next_source_id,
)
from airas.research_record.passages import (
    add_passages,
    quote_in,
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
from airas.usecases.literature.bibliography import (
    unique_bibkey,
)
from airas.usecases.literature.fulltext_snapshot import (
    snapshot_repository,
    write_fulltext,
)
from airas.usecases.literature.search_airas_records import AirasRecordsIndex
from airas.usecases.literature.verify_existence import (
    airas_db_metadata,
    verify_existence,
)
from airas.usecases.publication.write_tex_files import (
    write_claims_tex,
    write_references_bib,
)
from airas.usecases.retrieve.fetch_paper_fulltext_subgraph.fetch_paper_fulltext_subgraph import (
    FetchPaperFulltextSubgraph,
)
from airas.usecases.retrieve.fetch_paper_fulltext_subgraph.nodes.download_pdf_text import (
    parser_version,
)
from airas.usecases.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
)


async def register_sources(
    local_path: str,
    papers: list[dict[str, Any]] | None = None,
    repositories: list[dict[str, Any]] | None = None,
    latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
    *,
    search_index: AirasDbPaperSearchIndex,
    records_index: AirasRecordsIndex,
    arxiv_client: ArxivClient,
    semantic_scholar_client: SemanticScholarClient,
    http: httpx.AsyncClient,
) -> dict[str, Any]:
    """Pin each source by a fulltext snapshot and commit it with the record.

    All or nothing: a source that fails a check leaves nothing written.
    """
    if not (papers or repositories):
        raise ValueError("nothing to register: pass papers and/or repositories")
    root = Path(local_path).expanduser().resolve()
    record = (
        load_record(local_path)
        if record_path(local_path).is_file()
        else ResearchRecord()
    )
    registered: dict[str, Any] = {}
    snapshots: list[str] = []

    def _discard_snapshots() -> None:
        for relpath in snapshots:
            shutil.rmtree((root / relpath).parent, ignore_errors=True)
        with contextlib.suppress(OSError):
            (root / SOURCES_DIR).rmdir()  # only when nothing else is left in it

    def _register(source: LiteratureSource, entry: dict[str, Any]) -> None:
        add_passages(source, entry.get("passages") or [])
        registered[source.id] = {
            "bibkey": source.bibkey,
            "title": source.title,
            "fulltext": source.fulltext.path if source.fulltext else None,
            "passages": [p.id for p in source.passages],
            "verified_by": source.verified_by,
        }

    async def _register_airas_record(record_id: str, entry: dict[str, Any]) -> None:
        found = await records_index.get(record_id)
        if found is None:
            raise ValueError(
                f"'{record_id}': not in airas-records-db (search_papers with "
                'sources="airas_records" lists what is)'
            )
        source = next(
            (
                s
                for s in record.active_literature()
                if s.kind == "airas_record"
                and s.url == found.url
                and s.commit == found.commit
            ),
            None,
        )
        if source is None:
            # The record as the gate saw it, and claims.tex — the verdicts in
            # prose — from whichever template the study used.
            metadata, pages = await asyncio.to_thread(
                snapshot_repository,
                found.url,
                found.commit,
                [RECORD_PATH],
                [
                    f".research/latex/{t}/claims.tex"
                    for t in get_args(LATEX_TEMPLATE_NAME)
                ],
            )
            source_id = next_source_id(record)
            fulltext = write_fulltext(root, source_id, pages)
            snapshots.append(fulltext.path)
            repo_name = found.owner_repo.rsplit("/", 1)[-1]
            source = LiteratureSource(
                id=source_id,
                kind="airas_record",
                title=found.title,
                authors=[f"{found.owner_repo} (AIRAS)"],
                year=metadata["year"],
                url=found.url,
                commit=found.commit,
                bibkey=unique_bibkey(
                    found.title,
                    [repo_name],
                    metadata["year"],
                    {s.bibkey for s in record.literature},
                ),
                verified_by="airas_records",
                verified_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
                fulltext=fulltext,
                parser="git show",
            )
            record.literature.append(source)
        _register(source, entry)

    try:
        for entry in repositories or []:
            url, commit = (
                (entry.get("url") or "").strip(),
                (entry.get("commit") or "").strip(),
            )
            if not (url and commit and entry.get("files")):
                raise ValueError("a repository needs url, commit and files")
            if not re.fullmatch(r"[0-9a-f]{40}", commit):
                raise ValueError(
                    f"'{url}': commit must be a full 40-hex sha, not '{commit}' — "
                    "a branch or tag moves"
                )
            source = next(
                (
                    s
                    for s in record.active_literature()
                    if s.url == url and s.commit == commit
                ),
                None,
            )
            if source is None:
                metadata, pages = await asyncio.to_thread(
                    snapshot_repository, url, commit, list(entry["files"])
                )
                source_id = next_source_id(record)
                fulltext = write_fulltext(root, source_id, pages)
                snapshots.append(fulltext.path)
                source = LiteratureSource(
                    id=source_id,
                    kind="repository",
                    bibkey=unique_bibkey(
                        metadata["title"].rsplit("/", 1)[-1],
                        metadata["authors"],
                        metadata["year"],
                        {s.bibkey for s in record.literature},
                    ),
                    verified_by="git",
                    verified_at=datetime.now(timezone.utc).isoformat(
                        timespec="seconds"
                    ),
                    fulltext=fulltext,
                    parser="git show",
                    **metadata,
                )
                record.literature.append(source)
            _register(source, entry)

        for entry in papers or []:
            if record_id := str(entry.get("airas_record") or ""):
                await _register_airas_record(record_id, entry)
                continue
            db_id = str(entry.get("airas_db") or "") or None
            db_record = await search_index.get(db_id) if db_id else None
            metadata = airas_db_metadata(db_record) if db_record else {}
            title = metadata.get("title") or (entry.get("title") or "").strip()
            doi = (entry.get("doi") or "").strip() or None
            arxiv_id = (entry.get("arxiv_id") or "").strip() or None
            label = title or db_id or doi or arxiv_id
            if not (db_id or doi or arxiv_id):
                raise ValueError(
                    f"'{label}': a paper needs an airas_db id, a doi or an arxiv_id "
                    "so that its existence can be checked"
                )
            url = entry.get("url") or metadata.get("url")
            source = next(
                (
                    s
                    for s in record.active_literature()
                    if (doi and s.doi == doi)
                    or (arxiv_id and s.arxiv_id == arxiv_id)
                    or (url and s.url == url)
                ),
                None,
            )
            if source is None:
                registries, verified_at = await verify_existence(
                    airas_db_record={} if db_id and db_record is None else db_record,
                    doi=doi,
                    arxiv_id=arxiv_id,
                    arxiv=arxiv_client,
                    http=http,
                )
                verified_by = next(
                    (r for r, s in registries.items() if s == "found"), ""
                )
                if not verified_by:
                    raise ValueError(
                        f"'{label}': no registry verified it ({registries})"
                    )
                pdf_url = entry.get("pdf_url") or metadata.get("url")
                fetched = (
                    await FetchPaperFulltextSubgraph(
                        semantic_scholar_client=semantic_scholar_client
                    )
                    .build_graph()
                    .ainvoke(
                        {
                            "arxiv_id": arxiv_id,
                            "doi": doi,
                            "pdf_url": pdf_url,
                            "max_chars": None,
                        }
                    )
                )
                if fetched["status"] != "fulltext":
                    raise ValueError(
                        f"'{label}': no PDF yielded text ({fetched['status']}) — pass pdf_url"
                    )
                # The registry confirmed the identifier; this ties the PDF to it.
                # Case-insensitive: title pages are often set in capitals.
                if title and not quote_in(
                    "".join(fetched["pages"][:2]).casefold(), title.casefold()
                ):
                    raise ValueError(
                        f"'{label}': the PDF's first pages do not carry this title — "
                        "is pdf_url the right paper?"
                    )
                source_id = next_source_id(record)
                fulltext = write_fulltext(root, source_id, fetched["pages"])
                snapshots.append(fulltext.path)
                authors = metadata.get("authors") or entry.get("authors") or []
                year = metadata.get("year") or entry.get("year")
                source = LiteratureSource(
                    id=source_id,
                    title=title,
                    authors=authors,
                    year=year,
                    venue=metadata.get("venue") or entry.get("venue") or "",
                    doi=doi,
                    arxiv_id=arxiv_id,
                    url=url or fetched["pdf_url"],
                    bibkey=unique_bibkey(
                        title, authors, year, {s.bibkey for s in record.literature}
                    ),
                    verified_by=verified_by,
                    verified_at=verified_at,
                    fulltext=fulltext,
                    parser=parser_version(),
                )
                record.literature.append(source)
            _register(source, entry)

    except Exception:
        _discard_snapshots()
        raise

    def _run() -> dict[str, Any]:
        problems = verify_consistency(record) + verify_literature(root, record)
        if problems:
            raise ValueError("; ".join(problems))
        save_record(local_path, record)
        claims_tex = write_claims_tex(local_path, latex_template_name, record)
        references_bib = write_references_bib(local_path, latex_template_name, record)
        commit = commit_record_paths(
            local_path,
            [RECORD_PATH, claims_tex, references_bib, *snapshots],
            "record: register sources",
        )
        return {
            "record_path": str(record_path(local_path)),
            "references_bib_path": references_bib,
            "sources": registered,
            "commit": commit,
            "next": (
                "read each fulltext.txt and copy the passages the research "
                "rests on into append_to_record(source_id=..., passages=[...]); "
                "name them in grounded_on / cites_passages when declaring"
            ),
        }

    try:
        return await asyncio.to_thread(_run)
    except Exception:
        _discard_snapshots()
        raise
