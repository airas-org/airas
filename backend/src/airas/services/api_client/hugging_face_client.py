import os
from logging import getLogger
from typing import Any, Literal

import httpx

from airas.services.api_client.base_http_client import BaseHTTPClient
from airas.services.api_client.response_parser import ResponseParser
from airas.services.api_client.retry_policy import make_retry_policy, raise_for_status

logger = getLogger(__name__)

HF_RETRY = make_retry_policy()
HF_RESOURCE_TYPE = Literal["models", "datasets"]


# https://huggingface.co/docs/hub/api
class HuggingFaceClient(BaseHTTPClient):
    def __init__(
        self,
        base_url: str = "https://huggingface.co/api",
        default_headers: dict[str, str] | None = None,
        sync_session: httpx.Client | None = None,
        async_session: httpx.AsyncClient | None = None,
    ):
        # HuggingFace API token is optional for public models/datasets
        api_key = os.getenv("HF_TOKEN")
        auth_headers = {
            "Content-Type": "application/json",
        }
        if api_key:
            auth_headers["Authorization"] = f"Bearer {api_key}"

        super().__init__(
            base_url=base_url,
            default_headers={**auth_headers, **(default_headers or {})},
            sync_session=sync_session,
            async_session=async_session,
        )
        self._parser = ResponseParser()

    @HF_RETRY
    def search(
        self,
        search_type: HF_RESOURCE_TYPE,
        search_query: str = "",
        limit: int = 10,
        sort: str = "downloads",
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        params = {
            "limit": limit,
            "sort": sort,
        }
        if search_query:
            params["search"] = search_query

        response = self.get(path=f"/{search_type}", params=params, timeout=timeout)
        raise_for_status(response, path=f"search_{search_type}")
        return self._parser.parse(response, as_="json")

    @HF_RETRY
    def get_details(
        self,
        search_type: HF_RESOURCE_TYPE,
        item_id: str,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        response = self.get(path=f"/{search_type}/{item_id}", timeout=timeout)
        raise_for_status(response, path=f"get_{search_type[:-1]}_info")
        return self._parser.parse(response, as_="json")

    @HF_RETRY
    def get_readme(
        self,
        search_type: HF_RESOURCE_TYPE,
        item_id: str,
        timeout: float = 30.0,
    ) -> str:
        if search_type == "models":
            readme_url = f"https://huggingface.co/{item_id}/resolve/main/README.md"
        else:  # datasets
            readme_url = (
                f"https://huggingface.co/{search_type}/{item_id}/resolve/main/README.md"
            )

        response = self.get(path="", full_url=readme_url, timeout=timeout)

        if response.status_code == 404:
            logger.warning(f"README not found for {search_type[:-1]}: {item_id}")
            return ""

        raise_for_status(response, path=f"get_{search_type[:-1]}_readme")
        return response.text

    # Async methods
    @HF_RETRY
    async def asearch(
        self,
        search_type: HF_RESOURCE_TYPE,
        search_query: str = "",
        limit: int = 10,
        sort: str = "downloads",
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        params = {
            "limit": limit,
            "sort": sort,
        }
        if search_query:
            params["search"] = search_query

        response = await self.aget(
            path=f"/{search_type}", params=params, timeout=timeout
        )
        raise_for_status(response, path=f"search_{search_type}")
        return self._parser.parse(response, as_="json")

    @HF_RETRY
    async def aget_details(
        self,
        search_type: HF_RESOURCE_TYPE,
        item_id: str,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        response = await self.aget(path=f"/{search_type}/{item_id}", timeout=timeout)
        raise_for_status(response, path=f"get_{search_type[:-1]}_info")
        return self._parser.parse(response, as_="json")

    @HF_RETRY
    async def aget_readme(
        self,
        search_type: HF_RESOURCE_TYPE,
        item_id: str,
        timeout: float = 30.0,
    ) -> str:
        if search_type == "models":
            readme_url = f"https://huggingface.co/{item_id}/resolve/main/README.md"
        else:  # datasets
            readme_url = (
                f"https://huggingface.co/{search_type}/{item_id}/resolve/main/README.md"
            )

        response = await self.aget(path="", full_url=readme_url, timeout=timeout)

        if response.status_code == 404:
            logger.warning(f"README not found for {search_type[:-1]}: {item_id}")
            return ""

        raise_for_status(response, path=f"get_{search_type[:-1]}_readme")
        return response.text
