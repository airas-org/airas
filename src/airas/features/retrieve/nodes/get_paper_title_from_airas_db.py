import time
from logging import getLogger
from typing import Any

import requests

logger = getLogger(__name__)

UNIFIED_DB_URL = "https://raw.githubusercontent.com/airas-org/airas-papers-db/main/data/iclr/2024.json"


def _fetch_all_papers() -> list[dict[str, Any]]:
    logger.info(f"Fetching unified paper data from {UNIFIED_DB_URL}...")
    try:
        response = requests.get(UNIFIED_DB_URL, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"  -> An error occurred while fetching data: {e}")
    except ValueError as e:
        logger.error(f"  -> Failed to parse JSON: {e}")
    return []


def _apply_filters_by_queries(
    papers: list[dict[str, Any]], queries: list[str]
) -> list[dict[str, Any]]:
    active_queries = [q.lower() for q in queries if q and not q.isspace()]

    if not active_queries:
        return papers

    filtered_list = []
    for paper in papers:
        searchable_text = " ".join(
            [
                paper.get("title", ""),
                # paper.get("abstract", ""),
                # " ".join(paper.get("authors", [])),
                # paper.get("topic", "")
            ]
        ).lower()

        if all(query in searchable_text for query in active_queries):
            filtered_list.append(paper)

    return filtered_list


def get_paper_title_from_airas_db(queries: list[str]) -> list[dict[str, Any]]:
    all_papers = _fetch_all_papers()
    if not all_papers:
        return []

    filtered_papers = _apply_filters_by_queries(all_papers, queries)
    filtered_titles = [
        paper.get("title", "No Title Found") for paper in filtered_papers
    ]

    return filtered_titles


if __name__ == "__main__":
    queries = ["diffusion model"]

    logger.info(f"Searching for papers with queries: {queries}")
    start_time = time.perf_counter()

    results = get_paper_title_from_airas_db(queries)

    end_time = time.perf_counter()
    elapsed_time = end_time - start_time

    print(f"results: {results}")
    print(f"count: {len(results)}")
    print(f"Execution time: {elapsed_time:.4f} seconds")
