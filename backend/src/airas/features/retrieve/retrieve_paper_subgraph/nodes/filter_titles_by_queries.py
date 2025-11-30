from logging import getLogger
from typing import Any

logger = getLogger(__name__)


def _match_score(text: str, query: str) -> int:
    """Simple matching score: number of occurrences of query in text"""
    return text.count(query)


def _filter_papers_for_single_query(
    papers: list[dict[str, Any]],
    query: str,
    max_results: int | None = None,
) -> list[str]:
    query = query.lower().strip()
    if not query:
        return []

    scored_papers = []
    for paper in papers:
        searchable_text = " ".join(
            [
                paper.get("title", ""),
                # paper.get("abstract", ""),
                # " ".join(paper.get("authors", [])),
                # paper.get("topic", "")
            ]
        ).lower()

        score = _match_score(searchable_text, query)
        if score > 0:
            scored_papers.append((score, paper.get("title", "No Title Found")))

    scored_papers.sort(key=lambda x: x[0], reverse=True)

    return [title for _, title in scored_papers[:max_results]]


def filter_titles_by_queries(
    papers: list[dict[str, Any]],
    queries: list[str],
    max_results_per_query: int | None = None,
) -> list[list[str]]:
    """各クエリごとの上位マッチ結果を配列として返す"""
    query_results: list[list[str]] = []

    for query in queries:
        if query and not query.isspace():
            matched_titles = _filter_papers_for_single_query(
                papers, query, max_results=max_results_per_query
            )
            query_results.append(matched_titles)
        else:
            query_results.append([])

    return query_results
