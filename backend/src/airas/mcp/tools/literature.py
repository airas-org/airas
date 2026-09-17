import os
from typing import Any, Literal

from airas.core.credentials import SETUP_INSTRUCTIONS, refresh_environment
from airas.mcp.app import mcp
from airas.mcp.context import (
    _arxiv_client,
    _openalex_client,
    _records_index,
    _search_index,
    _semantic_scholar_client,
)
from airas.usecases.literature import (
    fetch_paper_fulltext as fetch_paper_fulltext_usecase,
)
from airas.usecases.literature import search_papers as search_papers_usecase


@mcp.tool()
async def search_papers(
    query: str,
    sources: str = "all",
    max_results_per_source: int = 5,
    year: str | None = None,
    search_mode: Literal["keyword", "semantic"] = "keyword",
    verdict: Literal["supported", "refuted", "inconclusive"] | None = None,
    stage: Literal["prereg", "results"] | None = None,
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
    `external_ids.airas_record` is the id `preregister_record` takes. `verdict`
    keeps studies with a claim of that verdict (`refuted` finds what has
    already failed), `stage` keeps preregistered-only or realized studies;
    both apply to airas_records alone, so select only that source with them.

    `search_mode="keyword"` (default) does lexical/relevance search on every
    source. `search_mode="semantic"` does AI-embedding search that matches by
    meaning; it is only supported by `openalex` and requires OPENALEX_API_KEY
    (so pass sources="openalex"). Selecting any other source in semantic mode
    is an error.

    Results are normalized (title, authors, abstract, doi, arxiv_id, pdf_url,
    citations, source) and de-duplicated across sources; failures of
    individual sources are reported in `search_errors` without failing the
    search. Keyword search needs no API keys (SEMANTIC_SCHOLAR_API_KEY /
    OPENALEX_API_KEY optionally raise rate limits). Pass a promising row's
    arxiv_id / doi / pdf_url to `fetch_paper_fulltext`.
    """
    refresh_environment()
    if search_mode == "semantic" and not os.getenv("OPENALEX_API_KEY"):
        raise RuntimeError(
            f"Semantic search requires OPENALEX_API_KEY. {SETUP_INSTRUCTIONS}"
        )
    result = await search_papers_usecase.search_papers(
        query,
        sources=search_papers_usecase.parse_sources(sources),
        max_results_per_source=max_results_per_source,
        year=year,
        search_mode=search_mode,
        verdict=verdict,
        stage=stage,
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
async def fetch_paper_fulltext(
    arxiv_id: str | None = None,
    doi: str | None = None,
    pdf_url: str | None = None,
) -> dict[str, Any]:
    """Download a paper's full text into a local file you then read yourself.

    Identifiers are tried in the order arXiv ID, then PDF URL, then DOI, and
    passing several is useful rather than wasteful: arXiv IDs are fetched
    straight from arXiv, DOIs are resolved to an open-access PDF through
    Semantic Scholar, and a DOI that resolves to nothing falls back to the
    `pdf_url` you supplied. Pass both whenever `search_papers` gave you both
    — a DOI alone returns only the abstract for any paper Semantic Scholar's
    open-access index does not cover, bioRxiv among them.

    On `status="fulltext"` the text is written to `fulltext_path` under
    `~/.airas/cache/fulltext/` (pages separated by form feeds) and nothing is
    returned inline: a paper runs to 80k+ characters, so read the file with
    your own tools, in parts or by searching it. `total_chars` says how long
    it is. `abstract_only` returns the abstract inline and writes no file;
    `not_found` means nothing at all was reachable. The cache keeps files
    for seven days; nothing is written to the research repository or the
    record — that happens at `preregister_record`, which takes the papers
    the hypothesis rests on together with their `fulltext_path`.
    No API keys required.
    """
    if not (arxiv_id or doi or pdf_url):
        raise ValueError("One of arxiv_id, doi, or pdf_url must be provided.")
    refresh_environment()
    return await fetch_paper_fulltext_usecase.fetch_paper_fulltext(
        arxiv_id, doi, pdf_url, semantic_scholar_client=_semantic_scholar_client()
    )
