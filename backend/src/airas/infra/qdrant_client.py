import os
from logging import getLogger
from typing import Any

import httpx

from airas.core.types.qdrant import QdrantDistance
from airas.infra.base_http_client import BaseHTTPClient
from airas.infra.response_parser import ResponseParser
from airas.infra.retry_policy import make_retry_policy, raise_for_status

logger = getLogger(__name__)

QDRANT_RETRY = make_retry_policy()


class QdrantClient(BaseHTTPClient):
    def __init__(
        self,
        default_headers: dict[str, str] | None = None,
        sync_session: httpx.Client | None = None,
        async_session: httpx.AsyncClient | None = None,
    ):
        api_key = os.getenv("QDRANT_API_KEY")
        if not api_key:
            raise EnvironmentError("QDRANT_API_KEY is not set")

        base_url = os.getenv("QDRANT_BASE_URL")
        if not base_url:
            raise EnvironmentError("QDRANT_BASE_URL is not set")

        auth_headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        super().__init__(
            base_url=base_url,
            default_headers={**auth_headers, **(default_headers or {})},
            sync_session=sync_session,
            async_session=async_session,
        )
        self._parser = ResponseParser()

    @QDRANT_RETRY
    def create_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: QdrantDistance = "Cosine",
        timeout: float = 60,
    ) -> dict[str, Any]:
        # https://api.qdrant.tech/api-reference/collections/create-collection
        payload = {"vectors": {"size": vector_size, "distance": distance}}
        response = self.put(
            path=f"/collections/{collection_name}", json=payload, timeout=timeout
        )
        raise_for_status(response, path=f"create_collection/{collection_name}")
        return self._parser.parse(response, as_="json")

    @QDRANT_RETRY
    def upsert_points(
        self,
        collection_name: str,
        data_sets: list[dict[str, Any]],
        timeout: float = 600,
    ) -> dict[str, Any]:
        # https://api.qdrant.tech/api-reference/points/upsert-points
        payload = {"points": data_sets}
        response = self.put(
            path=f"/collections/{collection_name}/points", json=payload, timeout=timeout
        )
        raise_for_status(response, path=f"upsert_points/{collection_name}")
        return self._parser.parse(response, as_="json")

    @QDRANT_RETRY
    def query_points(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        # https://api.qdrant.tech/api-reference/search/query-points
        limit = max(1, min(limit, 1000))
        payload = {
            "query": {
                "nearest": query_vector,
            },
            "limit": limit,
            "with_payload": True,
        }
        response = self.post(
            path=f"/collections/{collection_name}/points/query",
            json=payload,
            timeout=timeout,
        )
        raise_for_status(response, path=f"query_points/{collection_name}")
        return self._parser.parse(response, as_="json")

    @QDRANT_RETRY
    def retrieve_point(
        self,
        collection_name: str,
        point_id: int | str,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        # https://api.qdrant.tech/api-reference/points/get-point
        response = self.get(
            path=f"/collections/{collection_name}/points/{point_id}",
            timeout=timeout,
        )
        raise_for_status(response, path=f"retrieve_point/{collection_name}")
        return self._parser.parse(response, as_="json")

    @QDRANT_RETRY
    def delete_collection(
        self,
        collection_name: str,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        response = self.request(
            method="DELETE",
            path=f"/collections/{collection_name}",
            timeout=timeout,
        )
        raise_for_status(response, path=f"delete_collection/{collection_name}")
        return self._parser.parse(response, as_="json")

    @QDRANT_RETRY
    def get_collection_info(
        self,
        collection_name: str,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        response = self.get(
            path=f"/collections/{collection_name}",
            timeout=timeout,
        )
        raise_for_status(response, path=f"get_collection_info/{collection_name}")
        return self._parser.parse(response, as_="json")

    @QDRANT_RETRY
    async def acreate_collection(
        self,
        collection_name: str,
        vector_size: int,
        distance: QdrantDistance = "Cosine",
        timeout: float = 60,
    ) -> dict[str, Any]:
        payload = {"vectors": {"size": vector_size, "distance": distance}}
        response = await self.aput(
            path=f"/collections/{collection_name}", json=payload, timeout=timeout
        )
        raise_for_status(response, path=f"create_collection/{collection_name}")
        return self._parser.parse(response, as_="json")

    @QDRANT_RETRY
    async def aupsert_points(
        self,
        collection_name: str,
        data_sets: list[dict[str, Any]],
        timeout: float = 600,
    ) -> dict[str, Any]:
        payload = {"points": data_sets}
        response = await self.aput(
            path=f"/collections/{collection_name}/points", json=payload, timeout=timeout
        )
        raise_for_status(response, path=f"upsert_points/{collection_name}")
        return self._parser.parse(response, as_="json")

    @QDRANT_RETRY
    async def aquery_points(
        self,
        collection_name: str,
        query_vector: list[float],
        limit: int = 10,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        limit = max(1, min(limit, 1000))
        payload = {
            "query": {
                "nearest": query_vector,
            },
            "limit": limit,
            "with_payload": True,
        }
        response = await self.apost(
            path=f"/collections/{collection_name}/points/query",
            json=payload,
            timeout=timeout,
        )
        raise_for_status(response, path=f"query_points/{collection_name}")
        return self._parser.parse(response, as_="json")

    @QDRANT_RETRY
    async def aretrieve_point(
        self,
        collection_name: str,
        point_id: int | str,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        response = await self.aget(
            path=f"/collections/{collection_name}/points/{point_id}",
            timeout=timeout,
        )
        raise_for_status(response, path=f"retrieve_point/{collection_name}")
        return self._parser.parse(response, as_="json")

    @QDRANT_RETRY
    async def adelete_collection(
        self,
        collection_name: str,
        timeout: float = 60.0,
    ) -> dict[str, Any]:
        response = await self.arequest(
            method="DELETE",
            path=f"/collections/{collection_name}",
            timeout=timeout,
        )
        raise_for_status(response, path=f"delete_collection/{collection_name}")
        return self._parser.parse(response, as_="json")

    @QDRANT_RETRY
    async def aget_collection_info(
        self,
        collection_name: str,
        timeout: float = 15.0,
    ) -> dict[str, Any]:
        response = await self.aget(
            path=f"/collections/{collection_name}",
            timeout=timeout,
        )
        raise_for_status(response, path=f"get_collection_info/{collection_name}")
        return self._parser.parse(response, as_="json")
