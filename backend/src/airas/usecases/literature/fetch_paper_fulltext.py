from pathlib import Path
from typing import Any

from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.usecases.literature.nodes.cache_fulltext import (
    CACHE_DIR,
    cache_fulltext,
    cache_path,
    cached_fulltext,
)
from airas.usecases.literature.nodes.fetch_fulltext_from_url import (
    fetch_fulltext_from_url,
)
from airas.usecases.literature.nodes.resolve_pdf_url import (
    PdfCandidates,
    lookup_doi,
    resolve_pdf_url,
)


async def _first_fulltext(
    candidates: PdfCandidates, tried: set[str], cache_dir: Path
) -> dict[str, Any] | None:
    for url, resolved_from in candidates:
        if not url or url in tried:
            continue
        tried.add(url)
        pages = cached_fulltext(url, cache_dir)
        if pages is None:
            pages = await fetch_fulltext_from_url(url)
            if not "".join(pages).strip():
                continue
            cache_fulltext(url, pages, cache_dir)
        return {
            "status": "fulltext",
            "resolved_from": resolved_from,
            "pdf_url": url,
            "total_chars": sum(len(p) for p in pages),
            "fulltext_path": str(cache_path(url, cache_dir)),
        }
    return None


async def fetch_paper_fulltext(
    arxiv_id: str | None = None,
    doi: str | None = None,
    pdf_url: str | None = None,
    *,
    semantic_scholar_client: SemanticScholarClient,
    cache_dir: Path = CACHE_DIR,
) -> dict[str, Any]:
    tried: set[str] = set()
    candidates = resolve_pdf_url(arxiv_id, doi, pdf_url)
    abstract = None
    looked_up = not candidates
    if looked_up:
        candidates, abstract = await lookup_doi(doi, semantic_scholar_client)
    if found := await _first_fulltext(candidates, tried, cache_dir):
        return found
    if not looked_up:
        candidates, abstract = await lookup_doi(doi, semantic_scholar_client)
        if found := await _first_fulltext(candidates, tried, cache_dir):
            return found
    if abstract:
        return {
            "status": "abstract_only",
            "resolved_from": "semantic_scholar_abstract",
            "pdf_url": None,
            "total_chars": len(abstract),
            "fulltext_path": None,
            "abstract": abstract,
        }
    return {
        "status": "not_found",
        "resolved_from": None,
        "pdf_url": None,
        "total_chars": 0,
        "fulltext_path": None,
    }
