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


class FetchPaperFulltextSubgraphState(
    FetchPaperFulltextSubgraphInputState, FetchPaperFulltextSubgraphOutputState
):
    resolved_pdf_url: Optional[str]
    fallback_abstract: Optional[str]


class FetchPaperFulltextSubgraph:
    """Resolve a paper identifier to a PDF, download it, and extract the text.

    Resolution order: arXiv ID → explicit PDF URL → open-access PDF located
    via Semantic Scholar by DOI. When no PDF can be fetched, the abstract
    (when the DOI lookup provided one) is returned with status
    `abstract_only`, or `not_found` when nothing is available.

    A DOI that Semantic Scholar cannot resolve to an open-access PDF falls
    back to an explicitly supplied `pdf_url` before giving up on the
    abstract: sources such as bioRxiv host their own PDF and are absent from
    Semantic Scholar's open-access index, so the same paper that returns
    `abstract_only` by DOI returns full text by URL.
    """

    def __init__(self, semantic_scholar_client: SemanticScholarClient):
        self.semantic_scholar_client = semantic_scholar_client

    @record_execution_time
    async def _resolve_pdf_url(self, state: FetchPaperFulltextSubgraphState) -> dict:
        arxiv_id = (state.get("arxiv_id") or "").strip()
        pdf_url = (state.get("pdf_url") or "").strip()
        doi = (state.get("doi") or "").strip()

        if arxiv_id:
            bare_id = arxiv_id.split("v")[0]
            return {
                "resolved_pdf_url": f"https://arxiv.org/pdf/{bare_id}",
                "resolved_from": "arxiv",
            }
        if pdf_url:
            return {"resolved_pdf_url": pdf_url, "resolved_from": "pdf_url"}
        # arXiv-minted DOIs (10.48550/arxiv.<id>) map directly to arXiv and
        # are not resolvable through Semantic Scholar.
        if doi and doi.lower().startswith("10.48550/arxiv."):
            bare_id = doi[len("10.48550/arxiv.") :].split("v")[0]
            return {
                "resolved_pdf_url": f"https://arxiv.org/pdf/{bare_id}",
                "resolved_from": "arxiv",
            }
        if doi:
            try:
                paper = await asyncio.to_thread(
                    self.semantic_scholar_client.get_paper_by_doi, doi
                )
            except Exception as e:
                logger.warning(f"Semantic Scholar DOI lookup failed for {doi}: {e}")
                return {"resolved_pdf_url": None, "resolved_from": None}

            open_access_pdf = (paper.get("openAccessPdf") or {}).get("url")
            external = paper.get("externalIds") or {}
            resolved: dict = {"fallback_abstract": paper.get("abstract")}
            if resolved_arxiv_id := external.get("ArXiv"):
                resolved["resolved_pdf_url"] = (
                    f"https://arxiv.org/pdf/{resolved_arxiv_id}"
                )
                resolved["resolved_from"] = "arxiv"
            elif open_access_pdf:
                resolved["resolved_pdf_url"] = open_access_pdf
                resolved["resolved_from"] = "open_access_pdf"
            else:
                resolved["resolved_pdf_url"] = None
                resolved["resolved_from"] = None
            return resolved
        return {"resolved_pdf_url": None, "resolved_from": None}

    @record_execution_time
    async def _download_and_extract(
        self, state: FetchPaperFulltextSubgraphState
    ) -> dict:
        resolved_pdf_url = state.get("resolved_pdf_url")
        supplied_pdf_url = (state.get("pdf_url") or "").strip()

        attempts = [(resolved_pdf_url, state.get("resolved_from"))]
        if supplied_pdf_url and supplied_pdf_url != resolved_pdf_url:
            attempts.append((supplied_pdf_url, "pdf_url"))

        for candidate_url, resolved_from in attempts:
            if not candidate_url:
                continue
            text = await download_pdf_text(candidate_url)
            if text:
                return self._as_fulltext(text, resolved_from, state)
            logger.info(f"No text extracted from {candidate_url}")

        if fallback_abstract := state.get("fallback_abstract"):
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
