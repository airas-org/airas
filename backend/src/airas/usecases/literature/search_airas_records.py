"""Searching the research AIRAS itself produced — the records collected in
airas-records-db — by what it hypothesized, claimed and found."""

from __future__ import annotations

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Any

from nltk.stem import PorterStemmer
from pydantic import ValidationError
from rank_bm25 import BM25Okapi

from airas.core.types.paper_search import PaperSearchResult
from airas.core.types.research_record import ResearchRecord
from airas.infra.airas_records_client import AirasRecordsClient

logger = logging.getLogger(__name__)

_TITLE = re.compile(r"\\title\{([^}]*)\}")
_CONCURRENT_FETCHES = 10


@dataclass(frozen=True)
class RecordEntry:
    id: str  # "owner/repo@sha"
    url: str
    commit: str
    stage: str
    collected_at: str
    title: str
    record: ResearchRecord

    @property
    def owner_repo(self) -> str:
        return self.id.rsplit("@", 1)[0]


def searchable_text(entry: RecordEntry) -> str:
    """What a query is matched against: not the paper's prose but the
    record's — plus the titles it built on, so a paper's title finds the
    research that rests on it."""
    record = entry.record
    return "\n".join(
        [
            entry.title,
            *(h.statement for h in record.active_hypotheses()),
            *(c.statement for _, c in record.active_claims()),
            *(s.title for s in record.active_literature()),
        ]
    )


def _matches(entry: RecordEntry, verdict: str | None, stage: str | None) -> bool:
    if stage is not None and entry.stage != stage:
        return False
    return verdict is None or any(
        c.verdict == verdict for _, c in entry.record.active_claims()
    )


class AirasRecordsIndex:
    """BM25 over the store, built on first use for the life of the process."""

    def __init__(self, client: AirasRecordsClient) -> None:
        self._client = client
        self._entries: list[RecordEntry] | None = None
        self._tokens: list[set[str]] = []
        self._bm25: BM25Okapi | None = None
        self._stemmer = PorterStemmer()

    def _tokenize(self, text: str) -> list[str]:
        return [self._stemmer.stem(t) for t in re.findall(r"\w+", text.lower())]

    async def _load(self, item: dict[str, Any]) -> RecordEntry | None:
        record_id = str(item["id"])
        raw = await self._client.record_file(record_id, "record.json")
        if raw is None:
            logger.warning(f"airas-records-db: {record_id} has no record.json")
            return None
        try:
            record = ResearchRecord.model_validate_json(raw)
        except ValidationError as e:
            logger.warning(f"airas-records-db: {record_id}: {e}")
            return None
        main_tex = await self._client.record_file(record_id, "main.tex")
        title = (
            match.group(1).strip()
            if main_tex and (match := _TITLE.search(main_tex))
            else ""
        )
        hypotheses = record.active_hypotheses()
        owner_repo, sha = record_id.rsplit("@", 1)
        return RecordEntry(
            id=record_id,
            url=item.get("url") or f"https://github.com/{owner_repo}",
            commit=item.get("commit") or sha,
            stage=item.get("stage") or "",
            collected_at=item.get("collected_at") or "",
            title=title or (hypotheses[0].statement if hypotheses else record_id),
            record=record,
        )

    async def _ensure_loaded(self) -> None:
        if self._entries is not None:
            return
        semaphore = asyncio.Semaphore(_CONCURRENT_FETCHES)

        async def bounded(item: dict[str, Any]) -> RecordEntry | None:
            async with semaphore:
                return await self._load(item)

        loaded = await asyncio.gather(
            *(bounded(i) for i in await self._client.manifest())
        )
        self._entries = [e for e in loaded if e is not None]
        if self._entries:
            tokenized = [self._tokenize(searchable_text(e)) for e in self._entries]
            self._tokens = [set(t) for t in tokenized]
            self._bm25 = BM25Okapi(tokenized)

    async def search(
        self,
        query: str,
        max_results: int,
        *,
        verdict: str | None = None,
        stage: str | None = None,
    ) -> list[RecordEntry]:
        await self._ensure_loaded()
        if self._bm25 is None or self._entries is None:
            return []
        terms = self._tokenize(query)
        scores = self._bm25.get_scores(terms)
        # Matched on overlap, not on score: BM25's idf of a term is zero when
        # it appears in half the store, which a store of two studies makes
        # the common case.
        ranked = sorted(
            (
                (score, i)
                for i, score in enumerate(scores)
                if self._tokens[i].intersection(terms)
            ),
            reverse=True,
        )
        hits = (self._entries[i] for _, i in ranked)
        return [e for e in hits if _matches(e, verdict, stage)][:max_results]

    async def get(self, record_id: str) -> RecordEntry | None:
        await self._ensure_loaded()
        return next((e for e in self._entries or [] if e.id == record_id), None)


def _abstract(entry: RecordEntry) -> str:
    lines = []
    for hypothesis in entry.record.active_hypotheses():
        lines.append(f"{hypothesis.id}: {hypothesis.statement}")
        for claim in hypothesis.claims:
            lines.append(
                f"  {claim.id} [{claim.verdict or 'pending'}]: {claim.statement}"
            )
    return "\n".join(lines)


def to_search_result(entry: RecordEntry) -> PaperSearchResult:
    return PaperSearchResult(
        title=entry.title,
        authors=[f"{entry.owner_repo} (AIRAS)"],
        abstract=_abstract(entry),
        url=entry.url,
        published_date=entry.collected_at[:10] or None,
        venue="airas",
        source="airas_records",
        external_ids={"airas_record": entry.id},
    )


async def search_airas_records(
    index: AirasRecordsIndex,
    query: str,
    max_results: int,
    *,
    verdict: str | None = None,
    stage: str | None = None,
) -> list[PaperSearchResult]:
    return [
        to_search_result(e)
        for e in await index.search(query, max_results, verdict=verdict, stage=stage)
    ]
