"""The research AIRAS produced is searched by what it hypothesized, claimed
and found — and by the papers it built on — never by paper prose."""

import asyncio
import json
from typing import Any

import pytest

from airas.core.types.research_record import (
    Criterion,
    Hypothesis,
    LiteratureSource,
    Prediction,
    ResearchRecord,
    SeyvalClaim,
    SeyvalDesign,
    SeyvalRun,
    SeyvalVerifier,
    VerifierKind,
)
from airas.infra.airas_records_index import AirasRecordsIndex
from airas.usecases.literature.nodes.search_airas_records import search_airas_records
from airas.usecases.literature.search_papers import search_papers

SEYVAL = SeyvalVerifier(kind=VerifierKind.SEYVAL)


def _record(
    hypothesis: str,
    claim: str,
    verdict: str | None,
    source_title: str | None,
    doi: str | None = None,
) -> str:
    record = ResearchRecord(
        literature=[
            LiteratureSource(id="s1", title=source_title, bibkey="x-2020-y", doi=doi)
        ]
        if source_title
        else [],
        hypotheses=[
            Hypothesis(
                id="h1",
                statement=hypothesis,
                claims=[
                    SeyvalClaim(
                        verifier=SEYVAL,
                        id="c1",
                        statement=claim,
                        rationale="r",
                        verdict=verdict,
                        criterion=Criterion(
                            metric="acc", subject="a", reference="b", op=">=", margin=0
                        ),
                        prediction=Prediction(low=0, high=1, basis="p"),
                        designs=[
                            SeyvalDesign(
                                id="d1", summary="s", runs=[SeyvalRun(run_id="a")]
                            )
                        ],
                    )
                ],
            )
        ],
    )
    return record.model_dump_json()


SAM = "auto-res2/sam-cifar@" + "a" * 40
SPARSE = "auto-res2/sparse-attn@" + "b" * 40
LOOKALIKE = "auto-res2/lookalike@" + "d" * 40

STORE: dict[str, Any] = {
    "manifest.json": [
        {"id": SAM, "stage": "results", "collected_at": "2026-09-10T00:00:00+00:00"},
        {"id": SPARSE, "stage": "prereg"},
        {"id": "auto-res2/broken@" + "c" * 40, "stage": "results"},
        {"id": LOOKALIKE, "stage": "prereg"},
    ],
    # Shares the DOI prefix tokens with SPARSE's paper, and nothing else.
    f"records/{LOOKALIKE.replace('@', '/')}/record.json": _record(
        "Something unrelated about optimizers.",
        "Adam beats SGD here.",
        None,
        "Another arXiv paper",
        "10.48550/arXiv.9999.00001",
    ),
    f"records/{SAM.replace('@', '/')}/record.json": _record(
        "Sharpness-aware minimization improves generalization on CIFAR-10.",
        "SAM beats SGD on CIFAR-10 accuracy.",
        "refuted",
        None,
    ),
    f"records/{SAM.replace('@', '/')}/main.tex": "\\title{SAM on CIFAR, revisited}\n",
    f"records/{SPARSE.replace('@', '/')}/record.json": _record(
        "Sparse attention keeps perplexity within 1% of dense attention.",
        "Sparse attention matches dense attention perplexity.",
        None,
        "Attention Is All You Need",
        "10.48550/arXiv.1706.03762",
    ),
    "records/auto-res2/broken/" + "c" * 40 + "/record.json": json.dumps(
        {"hypotheses": "no"}
    ),
}


class _Store:
    async def manifest(self) -> list[dict[str, Any]]:
        return STORE["manifest.json"]

    async def record_file(self, record_id: str, name: str) -> str | None:
        owner_repo, sha = record_id.rsplit("@", 1)
        return STORE.get(f"records/{owner_repo}/{sha}/{name}")


def _index() -> AirasRecordsIndex:
    return AirasRecordsIndex(_Store())


def test_a_study_is_found_by_its_hypothesis_and_titled_from_its_paper() -> None:
    (hit,) = asyncio.run(search_airas_records(_index(), "sharpness generalization", 5))
    assert hit.title == "SAM on CIFAR, revisited"
    assert hit.authors == ["auto-res2/sam-cifar (AIRAS)"]
    assert hit.external_ids == {"airas_record": SAM}
    assert hit.abstract is not None and "c1 [refuted]: SAM beats SGD" in hit.abstract
    assert hit.published_date == "2026-09-10"


def test_a_study_without_a_paper_is_titled_by_its_hypothesis() -> None:
    (hit,) = asyncio.run(search_airas_records(_index(), "sparse attention", 5))
    assert hit.title.startswith("Sparse attention keeps perplexity")
    assert hit.abstract is not None and "[pending]" in hit.abstract


def test_the_papers_a_study_built_on_find_it_by_title_or_identifier() -> None:
    index = _index()
    for query in ("attention is all you need", "10.48550/arXiv.1706.03762"):
        hits = asyncio.run(search_airas_records(index, query, 5))
        assert [h.external_ids["airas_record"] for h in hits][:1] == [SPARSE], query


def test_verdict_and_stage_narrow_without_eating_max_results() -> None:
    index = _index()
    assert [
        h.external_ids["airas_record"]
        for h in asyncio.run(
            search_airas_records(index, "cifar attention", 1, verdict="refuted")
        )
    ] == [SAM]
    assert [
        h.external_ids["airas_record"]
        for h in asyncio.run(
            search_airas_records(index, "cifar attention", 1, stage="prereg")
        )
    ] == [SPARSE]


def test_a_record_that_does_not_parse_is_left_out() -> None:
    index = _index()
    assert asyncio.run(index.get("auto-res2/broken@" + "c" * 40)) is None
    entry = asyncio.run(index.get(SAM))
    assert entry is not None and entry.record.hypotheses[0].id == "h1"


def test_the_endpoint_runs_the_source_and_refuses_filters_elsewhere() -> None:
    unused: Any = None

    def run(**kw: Any) -> dict[str, Any]:
        return asyncio.run(
            search_papers(
                "sharpness",
                max_results_per_source=5,
                openalex_client=unused,
                semantic_scholar_client=unused,
                arxiv_client=unused,
                airas_db_index=unused,
                airas_records_index=_index(),
                **kw,
            )
        )

    result = run(sources=["airas_records"], verdict="refuted")
    assert [p.external_ids["airas_record"] for p in result["papers"]] == [SAM]
    assert result["source_results"] == {"airas_records": 1}
    assert result["search_errors"] == {}
    with pytest.raises(ValueError, match="airas_records only"):
        run(sources=["arxiv", "airas_records"], verdict="refuted")


def test_an_identifier_finds_exactly_the_study_that_cites_it() -> None:
    hits = asyncio.run(search_airas_records(_index(), "10.48550/arXiv.1706.03762", 1))
    assert [h.external_ids["airas_record"] for h in hits] == [SPARSE]


def test_a_superseded_claim_is_left_out_of_the_abstract() -> None:
    from airas.infra.airas_records_index import RecordEntry
    from airas.usecases.literature.nodes.search_airas_records import _abstract

    record = ResearchRecord.model_validate_json(_record("H", "old wording", None, None))
    record.hypotheses[0].claims.append(
        record.hypotheses[0].claims[0].model_copy(update={"statement": "new wording"})
    )
    entry = RecordEntry(
        id=SAM,
        url="u",
        commit="a" * 40,
        stage="prereg",
        collected_at="",
        title="t",
        record=record,
    )
    abstract = _abstract(entry)
    assert "new wording" in abstract and "old wording" not in abstract
