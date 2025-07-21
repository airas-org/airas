from logging import getLogger
from typing import Any

logger = getLogger(__name__)


def _filter_papers_by_queries(
    papers: list[dict[str, Any]],
    queries: list[str],
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

        if any(query in searchable_text for query in active_queries):
            filtered_list.append(paper)

    return filtered_list


def filter_titles_by_queries(
    papers: list[dict[str, Any]],
    queries: list[str],
    max_results: int | None = None,
) -> list[str]:
    filtered_papers = _filter_papers_by_queries(
        papers=papers,
        queries=queries,
    )
    if max_results is not None and max_results >= 0:
        filtered_papers = filtered_papers[:max_results]

    filtered_titles = [
        paper.get("title", "No Title Found") for paper in filtered_papers
    ]

    return filtered_titles
