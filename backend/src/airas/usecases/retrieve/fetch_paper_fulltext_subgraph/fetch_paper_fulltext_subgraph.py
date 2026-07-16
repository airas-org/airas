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


class FetchPaperFulltextSubgraphInputState(TypedDict):
    arxiv_id: Optional[str]
    doi: Optional[str]
    pdf_url: Optional[str]


class FetchPaperFulltextSubgraphOutputState(ExecutionTimeState):
    text: str
    status: FulltextStatus
    resolved_from: Optional[str]


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

        if resolved_pdf_url:
            text = await download_pdf_text(resolved_pdf_url)
            if text:
                return {"text": text, "status": "fulltext"}

        if fallback_abstract := state.get("fallback_abstract"):
            return {
                "text": fallback_abstract,
                "status": "abstract_only",
                "resolved_from": "semantic_scholar_abstract",
            }
        return {"text": "", "status": "not_found", "resolved_from": None}

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
