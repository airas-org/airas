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
            logger.error(f"  -> An error occurred while fetching data from {url}: {e}")
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
            for conference, years in CONFERENCES_AND_YEARS.items():
                for year in years:
                    url = f"{AIRAS_PAPERS_REPO_BASE_URL}/{conference}/{year}.json"
                    task = _bounded_fetch(url)
                    tasks.append(task)

            results = await asyncio.gather(*tasks, return_exceptions=True)

            all_papers: list[dict[str, Any]] = []
            for result in results:
                if isinstance(result, Exception):
                    continue
                papers = cast(list[dict[str, Any]], result)
                all_papers.extend(papers)

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

    async def search(self, query: str, max_results: int) -> list[str]:
        await self._ensure_loaded()

        if not self._bm25 or not self._titles:
            return []

        tokenized_query = self._tokenize_with_stem(query)
        scores = self._bm25.get_scores(tokenized_query)

        scored_papers = [
            (score, title)
            for score, title in zip(scores, self._titles, strict=True)
            if score > 0
        ]
        scored_papers.sort(key=lambda x: x[0], reverse=True)

        return [title for _, title in scored_papers[:max_results]]


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


async def main() -> None:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    logger.info("=" * 80)
    logger.info("Starting AIRAS DB paper search test...")
    logger.info("=" * 80)

    search_index = AirasDbPaperSearchIndex()

    test_queries = [
        "transformer",
        "attention mechanism",
        "neural network",
    ]

    logger.info(f"\nTest queries: {test_queries}")
    logger.info("-" * 80)

    results = await search_paper_titles_from_airas_db(
        queries=test_queries,
        max_results_per_query=5,
        search_index=search_index,
    )

    logger.info(f"\n{'=' * 80}")
    logger.info(f"Found {len(results)} unique papers:")
    logger.info(f"{'=' * 80}")
    for i, title in enumerate(results, 1):
        logger.info(f"{i:3d}. {title}")

    logger.info(f"\n{'=' * 80}")
    logger.info("Test completed successfully!")
    logger.info(f"{'=' * 80}")


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
