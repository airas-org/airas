from airas.services.api_client.llm_client.llm_facade_client import LLMFacadeClient
from airas.services.api_client.qdrant_client import QdrantClient


async def get_paper_titles_from_qdrant(
    queries: list[str],
    num_retrieve_paper: int,
    qdrant_client: QdrantClient,
    llm_client: LLMFacadeClient,
) -> list[str]:
    COLLECTION_NAME = "airas_database"
    results = []
    for query in queries:
        query_vector = await llm_client.text_embedding(message=query)
        if query_vector:
            result = qdrant_client.query_points(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                limit=num_retrieve_paper,
            )
            for i in result["result"]["points"]:
                results.append(i["payload"]["title"])
    return results
