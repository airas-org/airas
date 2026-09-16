from __future__ import annotations

import os
from typing import Any

import httpx

from airas.core.papers_db_config import AIRAS_RECORDS_REPO_BASE_URL
from airas.infra.base_http_client import BaseHTTPClient


class AirasRecordsClient(BaseHTTPClient):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        sync_session: httpx.Client | None = None,
        async_session: httpx.AsyncClient | None = None,
    ):
        super().__init__(
            base_url=base_url
            or os.getenv("AIRAS_RECORDS_BASE_URL")
            or AIRAS_RECORDS_REPO_BASE_URL,
            sync_session=sync_session,
            async_session=async_session,
        )

    async def manifest(self) -> list[dict[str, Any]]:
        response = await self.aget("manifest.json", timeout=60.0)
        response.raise_for_status()
        return response.json()

    async def record_file(self, record_id: str, name: str) -> str | None:
        owner_repo, sha = record_id.rsplit("@", 1)
        response = await self.aget(f"records/{owner_repo}/{sha}/{name}", timeout=60.0)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.text
