import logging

from airas.services.api_client.semantic_scholar_client import SemanticScholarClient

logger = logging.getLogger(__name__)


def semantic_scholar_search_titles(
    queries: list[str],
    *,
    limit: int = 20,
    year: str | None = None,
    publication_date_or_year: str | None = None,
    client: SemanticScholarClient | None = None,
) -> list[str]:
    if client is None:
        client = SemanticScholarClient()

    logger.info("Executing Semantic Scholar API searches...")
    collected: set[str] = set()

    for q in queries:
        logger.info(f"Searching papers for query: '{q}'")

        try:
            resp = client.search_paper_titles(
                query=q,
                fields=[],
                year=year,
                publication_date_or_year=publication_date_or_year,
                limit=limit,
            )
        except Exception as exc:
            logger.warning(f"Search failed for '{q}': {exc}")
            continue

        data = resp.get("data", [])
        if not data:
            logger.warning(f"No results for '{q}'")
            continue

        for item in data:
            title = item.get("title", "").strip()
            if title:
                collected.add(title)

    if not collected:
        raise RuntimeError("No paper titles obtained for any query")

    return sorted(collected)


if __name__ == "__main__":
    titles = semantic_scholar_search_titles(
        queries=["neural network", "transformer"],
        year="2020-2024",
        limit=20,
    )
    print("\n".join(titles))
