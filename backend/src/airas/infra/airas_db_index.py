import asyncio
import re
from logging import getLogger
from typing import Any, cast

import httpx
from nltk.stem import PorterStemmer
from rank_bm25 import BM25Okapi

from airas.core.papers_db_config import (
    AIRAS_PAPERS_REPO_BASE_URL,
    CONFERENCES_AND_YEARS,
)

logger = getLogger(__name__)

# Concurrent request limit to avoid overwhelming the server
MAX_CONCURRENT_REQUESTS = 10


class AirasDbPaperSearchIndex:
    def __init__(self) -> None:
        self._papers: list[dict[str, Any]] | None = None
        self._titles: list[str] | None = None
        self._bm25: BM25Okapi | None = None
        self._stemmer = PorterStemmer()

    def _tokenize_with_stem(self, text: str) -> list[str]:
        tokens = re.findall(r"\w+", text.lower())
        return [self._stemmer.stem(token) for token in tokens]

    async def _fetch_papers_from_url(
        self, client: httpx.AsyncClient, url: str
    ) -> list[dict[str, Any]]:
        logger.info(f"Fetching paper data from {url}...")
        try:
            response = await client.get(url, timeout=60)
            response.raise_for_status()
            papers = response.json()
            logger.info(f"  -> Successfully fetched {len(papers)} papers from {url}")
            return papers
        except httpx.HTTPStatusError as e:
            logger.error(f"  -> HTTP error while fetching data from {url}: {e}")
            raise
        except httpx.RequestError as e:
            logger.error(f"  -> Network error while fetching data from {url}: {e}")
            raise
        except ValueError as e:
            logger.error(f"  -> Failed to parse JSON from {url}: {e}")
            raise

    async def _fetch_all_papers(self) -> list[dict[str, Any]]:
        async with httpx.AsyncClient() as client:
            semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

            async def _bounded_fetch(url: str) -> list[dict[str, Any]]:
                async with semaphore:
                    return await self._fetch_papers_from_url(client, url)

            tasks = []
            urls = []
            for conference, years in CONFERENCES_AND_YEARS.items():
                for year in years:
                    url = f"{AIRAS_PAPERS_REPO_BASE_URL}/{conference}/{year}.json"
                    task = _bounded_fetch(url)
                    tasks.append(task)
                    urls.append(url)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_papers: list[dict[str, Any]] = []
            failed_count = 0
            for url, result in zip(urls, results, strict=True):
                if isinstance(result, Exception):
                    failed_count += 1
                    logger.warning(f"  -> Failed to fetch {url}: {result}")
                    continue
                papers = cast(list[dict[str, Any]], result)
                all_papers.extend(papers)

            if failed_count > 0:
                logger.warning(
                    f"Failed to fetch {failed_count}/{len(urls)} URLs. "
                    f"Successfully loaded {len(all_papers)} papers from {len(urls) - failed_count} URLs."
                )

        return all_papers

    async def _ensure_loaded(self) -> None:
        if self._papers is not None:
            return

        logger.info("Loading AIRAS paper database and building search index...")
        self._papers = await self._fetch_all_papers()

        if not self._papers:
            logger.warning("No papers loaded from AIRAS database")
            self._titles = []
            self._bm25 = None
            return

        self._titles = [paper.get("title", "") for paper in self._papers]
        tokenized_titles = [self._tokenize_with_stem(title) for title in self._titles]
        self._bm25 = BM25Okapi(tokenized_titles)

        logger.info(f"Search index built with {len(self._papers)} papers")

    async def get(self, record_id: str) -> dict[str, Any] | None:
        await self._ensure_loaded()
        return next(
            (p for p in self._papers or [] if str(p.get("id")) == record_id), None
        )

    async def search(self, query: str, max_results: int) -> list[str]:
        return [
            paper.get("title", "")
            for paper in await self.search_papers(query, max_results)
        ]

    async def search_papers(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """Return the full paper records (not just titles) for the best matches."""
        await self._ensure_loaded()

        if not self._bm25 or not self._papers:
            return []

        tokenized_query = self._tokenize_with_stem(query)
        scores = self._bm25.get_scores(tokenized_query)

        scored_indices = [
            (score, index) for index, score in enumerate(scores) if score > 0
        ]
        scored_indices.sort(key=lambda x: x[0], reverse=True)

        return [self._papers[index] for _, index in scored_indices[:max_results]]
