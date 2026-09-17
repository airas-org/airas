import re
from logging import getLogger
from typing import Any

from nltk.stem import PorterStemmer
from rank_bm25 import BM25Okapi

from airas.infra.airas_db_client import AirasDbClient

logger = getLogger(__name__)


class AirasDbPaperSearchIndex:
    def __init__(self, client: AirasDbClient) -> None:
        self._client = client
        self._papers: list[dict[str, Any]] | None = None
        self._bm25: BM25Okapi | None = None
        self._stemmer = PorterStemmer()

    def _tokenize_with_stem(self, text: str) -> list[str]:
        tokens = re.findall(r"\w+", text.lower())
        return [self._stemmer.stem(token) for token in tokens]

    async def _ensure_loaded(self) -> None:
        if self._papers is not None:
            return
        self._papers = await self._client.papers()
        if not self._papers:
            logger.warning("No papers loaded from AIRAS database")
            return
        self._bm25 = BM25Okapi(
            [self._tokenize_with_stem(p.get("title", "")) for p in self._papers]
        )
        logger.info(f"Search index built with {len(self._papers)} papers")

    async def search(self, query: str, max_results: int) -> list[str]:
        return [
            paper.get("title", "")
            for paper in await self.search_papers(query, max_results)
        ]

    async def search_papers(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """The full paper records (not just titles) for the best matches."""
        await self._ensure_loaded()
        if not self._bm25 or not self._papers:
            return []
        scores = self._bm25.get_scores(self._tokenize_with_stem(query))
        # Stable: equal scores keep the store's own order.
        ranked = sorted(
            ((score, i) for i, score in enumerate(scores) if score > 0),
            key=lambda item: item[0],
            reverse=True,
        )
        return [self._papers[i] for _, i in ranked[:max_results]]
