"""Turn the agent's literature entries into materials the record can pin: existence confirmed by a registry, full text in hand, title checked."""

from __future__ import annotations

import asyncio
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, get_args

import feedparser
import httpx

from airas.core.research_paths import PAGE_SEPARATOR, RECORD_PATH
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.literature_material import LiteratureMaterial
from airas.infra.airas_records_index import AirasRecordsIndex
from airas.infra.arxiv_client import ArxivClient
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.research_record.verify._verify_quoted_passages import passage_is_quoted
from airas.usecases.literature.nodes.cache_fulltext import cached_fulltext
from airas.usecases.literature.nodes.fetch_fulltext_from_repository import (
    fetch_fulltext_from_repository,
)
from airas.usecases.literature.nodes.fetch_fulltext_from_url import (
    fetch_fulltext_from_url,
    parser_version,
)
from airas.usecases.literature.nodes.resolve_pdf_url import lookup_doi, resolve_pdf_url


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def _fulltext_pages(
    arxiv_id: str | None,
    doi: str | None,
    pdf_url: str | None,
    semantic_scholar_client: SemanticScholarClient,
) -> dict[str, Any]:
    """The pages fetch_paper_fulltext cached, or a fresh download."""
    candidates = resolve_pdf_url(arxiv_id, doi, pdf_url)
    if not candidates:
        candidates, _ = await lookup_doi(doi, semantic_scholar_client)
    for url, _ in candidates:
        pages = cached_fulltext(url) or await fetch_fulltext_from_url(url)
        if "".join(pages).strip():
            return {"status": "fulltext", "pages": pages, "pdf_url": url}
    return {"status": "not_found", "pages": [], "pdf_url": None}


async def _repository(entry: dict[str, Any]) -> LiteratureMaterial:
    url, commit = (entry.get("url") or "").strip(), (entry.get("commit") or "").strip()
    if not (url and commit and entry.get("files")):
        raise ValueError("a repository needs url, commit and files")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError(
            f"'{url}': commit must be a full 40-hex sha, not '{commit}' — "
            "a branch or tag moves"
        )
    metadata, pages = await asyncio.to_thread(
        fetch_fulltext_from_repository, url, commit, list(entry["files"])
    )
    return LiteratureMaterial(
        kind="repository",
        pages=pages,
        verified_by="git",
        verified_at=_now(),
        parser="git show",
        passages=entry.get("passages") or [],
        bib_title=metadata["title"].rsplit("/", 1)[-1],
        **metadata,
    )


async def _airas_record(
    entry: dict[str, Any], records_index: AirasRecordsIndex
) -> LiteratureMaterial:
    record_id = str(entry["airas_record"])
    found = await records_index.get(record_id)
    if found is None:
        raise ValueError(
            f"'{record_id}': not in airas-records-db (search_papers with "
            'sources="airas_records" lists what is)'
        )
    sha = record_id.rsplit("@", 1)[-1]
    if not re.fullmatch(r"[0-9a-f]{40}", sha) or found.commit != sha:
        raise ValueError(
            f"'{record_id}': the store's commit {found.commit!r} is not the sha "
            "in the id — a study is pinned by the exact commit its id names"
        )
    # The record as the gate saw it, and claims.tex — the verdicts in prose —
    # from whichever template the study used.
    metadata, pages = await asyncio.to_thread(
        fetch_fulltext_from_repository,
        found.url,
        sha,
        [RECORD_PATH],
        [f".research/latex/{t}/claims.tex" for t in get_args(LATEX_TEMPLATE_NAME)],
    )
    return LiteratureMaterial(
        kind="airas_record",
        title=found.title,
        authors=[f"{found.owner_repo} (AIRAS)"],
        year=metadata["year"],
        url=found.url,
        commit=found.commit,
        pages=pages,
        verified_by="airas_records",
        verified_at=_now(),
        parser="git show",
        passages=entry.get("passages") or [],
        bib_authors=[found.owner_repo.rsplit("/", 1)[-1]],
    )


async def _paper(
    entry: dict[str, Any],
    *,
    arxiv_client: ArxivClient,
    semantic_scholar_client: SemanticScholarClient,
    http: httpx.AsyncClient,
) -> LiteratureMaterial:
    title = (entry.get("title") or "").strip()
    doi = (entry.get("doi") or "").strip() or None
    arxiv_id = (entry.get("arxiv_id") or "").strip() or None
    label = title or doi or arxiv_id
    if not (doi or arxiv_id):
        raise ValueError(
            f"'{label}': a paper needs a doi or an arxiv_id so that its "
            "existence can be checked"
        )
    registries, verified_at = await _verify_paper_existence(
        doi=doi,
        arxiv_id=arxiv_id,
        arxiv=arxiv_client,
        http=http,
    )
    verified_by = next((r for r, s in registries.items() if s == "found"), "")
    if not verified_by:
        raise ValueError(f"'{label}': no registry verified it ({registries})")

    pdf_url = entry.get("pdf_url")
    fulltext_path = entry.get("fulltext_path")
    if fulltext_path and Path(fulltext_path).is_file():
        pages = Path(fulltext_path).read_text(encoding="utf-8").split(PAGE_SEPARATOR)
    else:
        fetched = await _fulltext_pages(arxiv_id, doi, pdf_url, semantic_scholar_client)
        if fetched["status"] != "fulltext":
            raise ValueError(
                f"'{label}': no PDF yielded text ({fetched['status']}) — pass pdf_url"
            )
        pages, pdf_url = fetched["pages"], fetched["pdf_url"]
    # The registry confirmed the identifier; this ties the text to it.
    # Case-insensitive (title pages are often set in capitals) and, as a
    # fallback, space-insensitive: extractors drop the spaces around symbols.
    head = "".join(pages[:2]).casefold()
    if title and not (
        passage_is_quoted(head, title.casefold())
        or passage_is_quoted(
            re.sub(r"\s+", "", head), re.sub(r"\s+", "", title.casefold())
        )
    ):
        raise ValueError(
            f"'{label}': the PDF's first pages do not carry this title — "
            "is pdf_url the right paper?"
        )
    return LiteratureMaterial(
        kind="paper",
        title=title,
        authors=entry.get("authors") or [],
        year=entry.get("year"),
        venue=entry.get("venue") or "",
        doi=doi,
        arxiv_id=arxiv_id,
        url=entry.get("url") or pdf_url,
        pages=pages,
        verified_by=verified_by,
        verified_at=verified_at,
        parser=parser_version(),
        passages=entry.get("passages") or [],
    )


async def resolve_literatures(
    entries: list[dict[str, Any]],
    *,
    records_index: AirasRecordsIndex,
    arxiv_client: ArxivClient,
    semantic_scholar_client: SemanticScholarClient,
    http: httpx.AsyncClient,
) -> list[LiteratureMaterial]:
    materials = []
    for entry in entries:
        if entry.get("airas_record"):
            materials.append(await _airas_record(entry, records_index))
        elif "commit" in entry or "files" in entry:
            materials.append(await _repository(entry))
        else:
            materials.append(
                await _paper(
                    entry,
                    arxiv_client=arxiv_client,
                    semantic_scholar_client=semantic_scholar_client,
                    http=http,
                )
            )
    return materials


async def _verify_paper_existence(
    *,
    doi: str | None,
    arxiv_id: str | None,
    arxiv: ArxivClient,
    http: httpx.AsyncClient,
) -> tuple[dict[str, str], str]:
    """registry -> found | not_found | 'error: ...' for the registry behind
    each identifier given, and when it was asked."""
    # TODO: OpenAlex / Semantic Scholar could confirm and enrich too; skipped
    # because the indexers miss papers the resolvers know.
    registries: dict[str, str] = {}
    if doi:
        try:
            response = await http.head(
                f"https://doi.org/{doi}", timeout=30.0, follow_redirects=False
            )
            registries["doi.org"] = (
                "found"
                if response.is_redirect or response.is_success
                else "not_found"
                if response.status_code == 404
                else f"error: {response.status_code}"
            )
        except httpx.HTTPError as e:
            registries["doi.org"] = f"error: {e}"

    if arxiv_id:
        try:
            feed = feedparser.parse(await arxiv.aget_paper_by_id(arxiv_id))
            registries["arxiv"] = "found" if feed.entries else "not_found"
        except Exception as e:
            registries["arxiv"] = f"error: {e}"
    return registries, datetime.now(timezone.utc).isoformat(timespec="seconds")
