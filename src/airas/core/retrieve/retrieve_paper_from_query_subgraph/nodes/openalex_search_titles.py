import logging
from time import sleep

from airas.services.api_client.openalex_client import OpenAlexClient

logger = logging.getLogger(__name__)


_EXCLUDE_KEYWORDS = ("survey", "review", "overview", "systematic review")


def _is_excluded_title(title: str) -> bool:
    lowered = title.lower()
    return any(word in lowered for word in _EXCLUDE_KEYWORDS)

def openalex_search_titles(
    queries: list[str],
    *,
    year: str | None = None,
    max_results: int = 20,
    fields: tuple[str] = ("id", "display_name", "publication_year"), 
    sleep_sec: float = 0.2,
    client: OpenAlexClient | None = None,
) -> list[str] | None:
    if client is None:
        client = OpenAlexClient()

    collected: set[str] = set()

    for q in queries:
        logger.info(f"Searching ML works for query: '{q}'")
        current_page = 1
        per_page = min(max_results - len(collected), 200)

        while per_page > 0:
            try:
                response = client.search_papers(
                    query=q,
                    year=year,
                    per_page=per_page,
                    page=current_page,
                    fields=fields, 
                )
            except Exception as exc:
                logger.warning(f"Search failed for '{q}' (page {current_page}): {exc}")
                break

            results = response.get("results", [])
            if not results:
                break

            for item in results:
                title = item.get("display_name", "").strip()
                if title and not _is_excluded_title(title):
                    collected.add(title)
                    if len(collected) >= max_results:
                        return sorted(collected)

            current_page += 1
            sleep(sleep_sec)
            per_page = min(max_results - len(collected), 200)

    if not collected:
        logger.warning("No paper titles obtained for any query")
        return None
    
    return sorted(collected)


if __name__ == "__main__":
    results = openalex_search_titles(
        queries=["This study introduces a vision transformer model for image recognition tasks."],
        year="2020-2024",
        max_results=20,
    )
    for title in results:
        print(f"- {title}")
