from logging import getLogger

from airas.infra.litellm_client import LiteLLMClient
from airas.infra.qdrant_client import QdrantClient

logger = getLogger(__name__)


async def search_paper_titles_from_qdrant(
    queries: list[str],
    max_results_per_query: int,
    litellm_client: LiteLLMClient,
    qdrant_client: QdrantClient,
    collection_name: str,
    embedding_model: str,
) -> list[str]:
    non_empty_queries = [q for q in queries if q and not q.isspace()]
    if not non_empty_queries:
        return []

    query_vectors = await litellm_client.embedding(
        non_empty_queries, model=embedding_model
    )

    seen: set[str] = set()
    results: list[str] = []

    for query_vector in query_vectors:
        if not query_vector:
            continue

        response = await qdrant_client.aquery_points(
            collection_name=collection_name,
            query_vector=query_vector,
            limit=max_results_per_query,
        )

        for point in response.get("result", {}).get("points", []):
            title = point.get("payload", {}).get("title", "")
            if title and title not in seen:
                seen.add(title)
                results.append(title)

    return results
