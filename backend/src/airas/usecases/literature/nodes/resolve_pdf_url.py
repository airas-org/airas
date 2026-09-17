import asyncio
import logging

from airas.infra.semantic_scholar_client import SemanticScholarClient

logger = logging.getLogger(__name__)

PdfCandidates = list[tuple[str, str]]  # (url, resolved_from)


def arxiv_pdf_url(arxiv_id: str) -> str:
    return f"https://arxiv.org/pdf/{arxiv_id.split('v')[0]}"


def resolve_pdf_url(
    arxiv_id: str | None, doi: str | None, pdf_url: str | None
) -> PdfCandidates:
    """The candidates reachable without a network lookup, in trial order."""
    arxiv_id, doi, pdf_url = ((s or "").strip() for s in (arxiv_id, doi, pdf_url))
    candidates: PdfCandidates = []
    if arxiv_id:
        candidates.append((arxiv_pdf_url(arxiv_id), "arxiv"))
    # arXiv-minted DOIs map straight to arXiv and are unknown to Semantic Scholar.
    if doi.lower().startswith("10.48550/arxiv."):
        candidates.append((arxiv_pdf_url(doi[len("10.48550/arxiv.") :]), "arxiv"))
    if pdf_url:
        candidates.append((pdf_url, "pdf_url"))
    return candidates


async def lookup_doi(
    doi: str | None, semantic_scholar_client: SemanticScholarClient
) -> tuple[PdfCandidates, str | None]:
    """More candidates and the abstract, from Semantic Scholar. Rate-limited
    hard, so callers ask only once the direct candidates are exhausted."""
    doi = (doi or "").strip()
    if not doi:
        return [], None
    try:
        paper = await asyncio.to_thread(semantic_scholar_client.get_paper_by_doi, doi)
    except Exception as e:
        logger.warning(f"Semantic Scholar DOI lookup failed for {doi}: {e}")
        return [], None
    candidates: PdfCandidates = []
    if resolved := (paper.get("externalIds") or {}).get("ArXiv"):
        candidates.append((arxiv_pdf_url(resolved), "arxiv"))
    if open_access := (paper.get("openAccessPdf") or {}).get("url"):
        candidates.append((open_access, "open_access_pdf"))
    return candidates, paper.get("abstract")
