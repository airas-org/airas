from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

from airas.core.papers_db_config import (
    AIRAS_PAPERS_REPO_BASE_URL,
    CONFERENCES_AND_YEARS,
)
from airas.infra.base_http_client import BaseHTTPClient

logger = logging.getLogger(__name__)

_CONCURRENT_FETCHES = 10


class AirasDbClient(BaseHTTPClient):
    def __init__(
        self,
        *,
        base_url: str | None = None,
        sync_session: httpx.Client | None = None,
        async_session: httpx.AsyncClient | None = None,
    ):
        super().__init__(
            base_url=base_url or AIRAS_PAPERS_REPO_BASE_URL,
            sync_session=sync_session,
            async_session=async_session,
        )

    async def papers(self) -> list[dict[str, Any]]:
        semaphore = asyncio.Semaphore(_CONCURRENT_FETCHES)
        paths = [
            f"{conference}/{year}.json"
            for conference, years in CONFERENCES_AND_YEARS.items()
            for year in years
        ]

        async def fetch(path: str) -> list[dict[str, Any]]:
            async with semaphore:
                response = await self.aget(path, timeout=60.0)
                response.raise_for_status()
                return response.json()

        results = await asyncio.gather(*map(fetch, paths), return_exceptions=True)
        papers: list[dict[str, Any]] = []
        failed = 0
        for path, result in zip(paths, results, strict=True):
            if isinstance(result, BaseException) and not isinstance(result, Exception):
                raise result  # a cancellation is not a file that failed to load
            if isinstance(result, Exception):
                failed += 1
                logger.warning(f"airas-papers-db: {path} not loaded: {result}")
                continue
            papers.extend(result)
        if failed:
            logger.warning(f"airas-papers-db: {failed}/{len(paths)} files not loaded")
        return papers
