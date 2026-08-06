import asyncio
import logging
from typing import Literal, Optional

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.infra.semantic_scholar_client import SemanticScholarClient
from airas.usecases.retrieve.fetch_paper_fulltext_subgraph.nodes.download_pdf_text import (
    download_pdf_text,
)

setup_logging()
logger = logging.getLogger(__name__)

subgraph_name = "fetch_paper_fulltext_subgraph"
record_execution_time = lambda f: time_node(subgraph_name)(f)  # noqa: E731

FulltextStatus = Literal["fulltext", "abstract_only", "not_found"]


def _truncate(text: str, max_chars: Optional[int]) -> dict:
    """Cap `text`, reporting the full length so the caller can page on."""
    total_chars = len(text)
    if max_chars is None or max_chars <= 0 or total_chars <= max_chars:
        return {"text": text, "total_chars": total_chars, "truncated": False}
    logger.info(f"Truncating extracted text from {total_chars} to {max_chars} chars")
    return {
        "text": text[:max_chars],
        "total_chars": total_chars,
        "truncated": True,
    }


class FetchPaperFulltextSubgraphInputState(TypedDict):
    arxiv_id: Optional[str]
    doi: Optional[str]
    pdf_url: Optional[str]
    max_chars: Optional[int]


class FetchPaperFulltextSubgraphOutputState(ExecutionTimeState):
    text: str
    status: FulltextStatus
    resolved_from: Optional[str]
    total_chars: int
    truncated: bool


# (url, resolved_from) pairs, in the order they should be downloaded.
PdfCandidates = list[tuple[str, str]]


class FetchPaperFulltextSubgraphState(
    FetchPaperFulltextSubgraphInputState, FetchPaperFulltextSubgraphOutputState
):
    pdf_candidates: PdfCandidates
    fallback_abstract: Optional[str]
    doi_lookup_done: bool


class FetchPaperFulltextSubgraph:
    """Resolve a paper identifier to a PDF, download it, and extract the text.

    Candidates are tried in order: the arXiv PDF (from an arXiv ID or an
    arXiv-minted DOI), then an explicitly supplied `pdf_url`, then whatever
    a Semantic Scholar DOI lookup turns up. The abstract is the last resort
    (`abstract_only`), and `not_found` means there was nothing at all.

    **Supplying more identifiers never produces a worse result.** That is not
    free: the DOI lookup is what provides the abstract to fall back on, and
    also finds arXiv URLs for papers that only announce them there. So the
    lookup runs whenever the direct candidates come up empty — even if a
    `pdf_url` was supplied — rather than being skipped because a URL was
    already on hand. It stays lazy because Semantic Scholar rate-limits
    hard, so a request that never needs the fallback never pays for it.
    """

    def __init__(self, semantic_scholar_client: SemanticScholarClient):
        self.semantic_scholar_client = semantic_scholar_client

    @staticmethod
    def _arxiv_pdf_url(arxiv_id: str) -> str:
        return f"https://arxiv.org/pdf/{arxiv_id.split('v')[0]}"

    @record_execution_time
    async def _resolve_pdf_url(self, state: FetchPaperFulltextSubgraphState) -> dict:
        """Collect the candidates reachable without a network lookup."""
        arxiv_id = (state.get("arxiv_id") or "").strip()
        pdf_url = (state.get("pdf_url") or "").strip()
        doi = (state.get("doi") or "").strip()

        candidates: PdfCandidates = []
        if arxiv_id:
            candidates.append((self._arxiv_pdf_url(arxiv_id), "arxiv"))
        # arXiv-minted DOIs (10.48550/arxiv.<id>) map directly to arXiv and
        # are not resolvable through Semantic Scholar.
        if doi.lower().startswith("10.48550/arxiv."):
            candidates.append(
                (self._arxiv_pdf_url(doi[len("10.48550/arxiv.") :]), "arxiv")
            )
        if pdf_url:
            candidates.append((pdf_url, "pdf_url"))

        if candidates:
            return {"pdf_candidates": candidates, "doi_lookup_done": False}

        # Nothing to try without asking, so ask now rather than in the
        # download node — there is no download to attempt first.
        return await self._lookup_doi(doi)

    async def _lookup_doi(self, doi: str) -> dict:
        """Ask Semantic Scholar for more candidates, and for the abstract."""
        if not doi:
            return {"pdf_candidates": [], "doi_lookup_done": True}
        try:
            paper = await asyncio.to_thread(
                self.semantic_scholar_client.get_paper_by_doi, doi
            )
        except Exception as e:
            logger.warning(f"Semantic Scholar DOI lookup failed for {doi}: {e}")
            return {"pdf_candidates": [], "doi_lookup_done": True}

        candidates: PdfCandidates = []
        external = paper.get("externalIds") or {}
        if resolved_arxiv_id := external.get("ArXiv"):
            candidates.append((self._arxiv_pdf_url(resolved_arxiv_id), "arxiv"))
        if open_access_pdf := (paper.get("openAccessPdf") or {}).get("url"):
            candidates.append((open_access_pdf, "open_access_pdf"))
        return {
            "pdf_candidates": candidates,
            "fallback_abstract": paper.get("abstract"),
            "doi_lookup_done": True,
        }

    async def _try_candidates(
        self,
        candidates: PdfCandidates,
        already_tried: set[str],
        state: FetchPaperFulltextSubgraphState,
    ) -> Optional[dict]:
        for url, resolved_from in candidates:
            if not url or url in already_tried:
                continue
            already_tried.add(url)
            text = await download_pdf_text(url)
            if text:
                return self._as_fulltext(text, resolved_from, state)
            logger.info(f"No text extracted from {url}")
        return None

    @record_execution_time
    async def _download_and_extract(
        self, state: FetchPaperFulltextSubgraphState
    ) -> dict:
        tried: set[str] = set()
        fallback_abstract = state.get("fallback_abstract")

        result = await self._try_candidates(
            state.get("pdf_candidates") or [], tried, state
        )
        if result:
            return result

        # The direct candidates are exhausted. A DOI still has two things to
        # give: URLs that were never announced anywhere else (arXiv mirrors,
        # open-access copies) and the abstract to fall back on. Skipping this
        # because a pdf_url happened to be supplied is what made passing more
        # identifiers produce a worse answer than passing fewer.
        if not state.get("doi_lookup_done"):
            looked_up = await self._lookup_doi((state.get("doi") or "").strip())
            fallback_abstract = looked_up.get("fallback_abstract")
            result = await self._try_candidates(
                looked_up["pdf_candidates"], tried, state
            )
            if result:
                return result

        if fallback_abstract:
            return {
                **_truncate(fallback_abstract, state.get("max_chars")),
                "status": "abstract_only",
                "resolved_from": "semantic_scholar_abstract",
            }
        return {
            "text": "",
            "status": "not_found",
            "resolved_from": None,
            "total_chars": 0,
            "truncated": False,
        }

    @staticmethod
    def _as_fulltext(
        text: str, resolved_from: Optional[str], state: FetchPaperFulltextSubgraphState
    ) -> dict:
        return {
            **_truncate(text, state.get("max_chars")),
            "status": "fulltext",
            "resolved_from": resolved_from,
        }

    def build_graph(self):
        graph_builder = StateGraph(
            FetchPaperFulltextSubgraphState,
            input_schema=FetchPaperFulltextSubgraphInputState,
            output_schema=FetchPaperFulltextSubgraphOutputState,
        )
        graph_builder.add_node("resolve_pdf_url", self._resolve_pdf_url)
        graph_builder.add_node("download_and_extract", self._download_and_extract)
        graph_builder.add_edge(START, "resolve_pdf_url")
        graph_builder.add_edge("resolve_pdf_url", "download_and_extract")
        graph_builder.add_edge("download_and_extract", END)
        return graph_builder.compile()
