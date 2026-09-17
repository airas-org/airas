from airas.core.types.paper_search import PaperSearchResult
from airas.core.types.research_record import active
from airas.infra.airas_records_index import AirasRecordsIndex, RecordEntry


def _abstract(entry: RecordEntry) -> str:
    lines = []
    for hypothesis in entry.record.active_hypotheses():
        lines.append(f"{hypothesis.id}: {hypothesis.statement}")
        for claim in active(hypothesis.claims, "id"):
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
