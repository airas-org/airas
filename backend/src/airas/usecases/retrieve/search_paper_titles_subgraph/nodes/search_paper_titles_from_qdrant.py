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

    try:
        query_vectors = await litellm_client.embedding(
            non_empty_queries, model=embedding_model
        )
    except Exception as e:
        logger.error(f"Failed to generate embeddings: {e}", exc_info=True)
        return []

    seen: set[str] = set()
    results: list[str] = []

    for query_vector in query_vectors:
        if not query_vector:
            continue

        try:
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
        except Exception as e:
            logger.warning(f"Failed to query Qdrant for a query vector: {e}")
            continue

    return results
