import json
import os
from typing import Any

from airas.core.credentials import SETUP_INSTRUCTIONS, refresh_environment
from airas.core.research_paths import FETCH_LITERATURE_WORKFLOW_PATH
from airas.mcp.app import mcp
from airas.mcp.context import (
    _arxiv_client,
    _github_client,
    _openalex_client,
    _records_index,
    _search_index,
    _semantic_scholar_client,
)
from airas.usecases.literature import search_papers as search_papers_usecase
from airas.usecases.literature.fetch_literature import validate_literature_input


@mcp.tool()
async def search_papers(
    query: str,
    sources: str = "all",
    max_results_per_source: int = 5,
    year: str | None = None,
    openalex_semantic: bool = False,
) -> dict[str, Any]:
    """Search academic papers across multiple sources in parallel.

    Sources: openalex, semantic_scholar, arxiv, airas_db (curated conference
    database: the major ML and NLP venues, plus the formal-methods and
    theorem-proving venues — ITP, CPP, CADE, IJCAR, CAV, TACAS, LICS, POPL —
    for theory claims), airas_records (the research AIRAS itself produced
    whose gate passed). Pass a comma-separated subset or "all". `year`
    filters by publication year ("2024" or "2020-2024"); it does not apply
    to airas_records.

    `airas_records` matches the query against what each study hypothesized
    and claimed — and the titles of the papers it built on, so a paper's
    title finds the studies that rest on it — not against paper prose. Each
    row's `abstract` lists the hypotheses and claims with their verdicts, and
    `external_ids.airas_record` is the id `preregister_record` takes.

    Every source does lexical/relevance search. `openalex_semantic=True`
    switches openalex alone to AI-embedding search that matches by meaning
    (requires OPENALEX_API_KEY and openalex among `sources`); the other
    sources stay lexical in the same call.

    Results are normalized (title, authors, abstract, doi, arxiv_id, pdf_url,
    citations, source) and de-duplicated across sources; failures of
    individual sources are reported in `search_errors` without failing the
    search. Keyword search needs no API keys (SEMANTIC_SCHOLAR_API_KEY /
    OPENALEX_API_KEY optionally raise rate limits).
    """
    refresh_environment()
    if openalex_semantic and not os.getenv("OPENALEX_API_KEY"):
        raise RuntimeError(
            f"Semantic search requires OPENALEX_API_KEY. {SETUP_INSTRUCTIONS}"
        )
    result = await search_papers_usecase.search_papers(
        query,
        sources=search_papers_usecase.parse_sources(sources),
        max_results_per_source=max_results_per_source,
        year=year,
        openalex_semantic=openalex_semantic,
        openalex_client=_openalex_client(),
        semantic_scholar_client=_semantic_scholar_client(),
        arxiv_client=_arxiv_client(),
        airas_db_index=_search_index,
        airas_records_index=_records_index,
    )
    return {
        "papers": [paper.model_dump(exclude_none=True) for paper in result["papers"]],
        "source_results": result["source_results"],
        "search_errors": result["search_errors"],
    }


@mcp.tool()
async def dispatch_literature_fetch(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    query: str | None = None,
    sources: str = "arxiv,airas_records",
    max_results_per_source: int = 5,
    year: str | None = None,
    openalex_semantic: bool = False,
    arxiv_ids: list[str] | None = None,
    dois: list[str] | None = None,
) -> dict[str, Any]:
    """Fetch literature in CI and commit it into `.research/sources/` on the branch.

    Pass either `query` with `search_papers` options, or `arxiv_ids` and/or
    `dois` as raw identifiers, not URLs. Direct lookup checks the identifiers,
    preserves requested arXiv versions and records resolved versions when
    omitted. `year` and `openalex_semantic` apply only to query searches.
    DOI lookup uses Semantic Scholar's metadata and PDF URL. Missing text
    is kept with its reason; a failed lookup never substitutes another paper.
    Once `get_workflow_runs` reports success, pull the branch and read the
    sources. Requires GH_PERSONAL_ACCESS_TOKEN and, for semantic search,
    the repository's OPENALEX_API_KEY secret.
    """
    validate_literature_input(
        query, arxiv_ids, dois, year=year, openalex_semantic=openalex_semantic
    )
    response = await _github_client().acreate_workflow_dispatch(
        github_owner,
        repository_name,
        FETCH_LITERATURE_WORKFLOW_PATH.rsplit("/", 1)[-1],
        ref=branch_name,
        inputs={
            "query": query or "",
            "sources": sources,
            "max_results_per_source": str(max_results_per_source),
            "year": year or "",
            "openalex_semantic": str(openalex_semantic).lower(),
            "arxiv_ids": json.dumps(arxiv_ids or []),
            "dois": json.dumps(dois or []),
        },
        return_run_details=True,
    )
    details = response if isinstance(response, dict) else {}
    return {
        "workflow_run_id": details.get("workflow_run_id"),
        "html_url": details.get("html_url"),
    }
