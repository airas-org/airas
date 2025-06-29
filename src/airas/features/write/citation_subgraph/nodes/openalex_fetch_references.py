import logging
from time import sleep
from typing import Any

from airas.services.api_client.openalex_client import OpenAlexClient

logger = logging.getLogger(__name__)


def _search_one_query(
    query: str,
    *,
    year: str | None,
    max_results: int,
    sleep_sec: float,
    client: OpenAlexClient | None = None,
) -> list[dict[str, Any]]:
    client = client or OpenAlexClient()

    collected: list[dict[str, Any]] = []
    current_page = 1

    while len(collected) < max_results:
        per_page = min(max_results - len(collected), 200)
        try:
            resp = client.search_papers(
                query=query,
                year=year,
                per_page=per_page,
                page=current_page,
            )
        except Exception as e:
            logger.warning(f"Search failed for {query} (page {current_page}): {e}")
            break

        results = resp.get("results") or []
        if not results:
            break

        collected.extend(results)
        current_page += 1
        sleep(sleep_sec)

    return collected[:max_results]


def _summarize_paper_info(paper: dict[str, Any]) -> dict[str, Any]:
    authors = []
    for a in paper.get("authorships") or []:
        if name := (a.get("author") or {}).get("display_name"):
            authors.append(name)

    journal = ((paper.get("primary_location") or {}).get("source") or {}).get(
        "display_name"
    )

    summary = {
        "id": paper.get("id"),
        "doi": paper.get("doi"),
        "title": paper.get("display_name"),
        "authors": authors,
        "year": paper.get("publication_year"),
        "biblio": paper.get("biblio", {}),
        "journal": journal,
    }
    return summary


# NOTE: Currently returns a single finalized paper per query, not a list of candidate papers.
def openalex_fetch_references(
    generated_citation_queries: dict[str, str],
    *,
    year: str | None = None,
    max_results: int = 1,
    sleep_sec: float = 0.2,
    client: OpenAlexClient | None = None,
) -> dict[str, dict[str, Any]]:
    client = client or OpenAlexClient()

    references = {}
    for placeholder, query in generated_citation_queries.items():
        results = _search_one_query(
            query,
            year=year,
            max_results=max_results,
            client=client,
            sleep_sec=sleep_sec,
        )
        references[placeholder] = _summarize_paper_info(results[0]) if results else {}

    return references
