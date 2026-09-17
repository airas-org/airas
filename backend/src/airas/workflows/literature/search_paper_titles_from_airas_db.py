from airas.infra.airas_db_index import AirasDbPaperSearchIndex


async def search_paper_titles_from_airas_db(
    queries: list[str],
    max_results_per_query: int,
    search_index: AirasDbPaperSearchIndex,
) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []

    for query in queries:
        if query and not query.isspace():
            matched_titles = await search_index.search(
                query, max_results=max_results_per_query
            )
            for title in matched_titles:
                if title not in seen:
                    seen.add(title)
                    results.append(title)

    return results
