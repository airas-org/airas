from typing import Any

import httpx
import pytest

import airas.infra.airas_db_client as client_module
from airas.infra.airas_db_client import AirasDbClient
from airas.infra.airas_db_index import AirasDbPaperSearchIndex

# Three titles: BM25's idf of a term is zero when it appears in half the store.
FILES = {
    "/data/iclr/2020.json": [
        {"id": "1", "title": "Attention Is All You Need"},
        {"id": "2", "title": "Deep Residual Learning for Image Recognition"},
    ],
    "/data/acl/2021.json": [{"id": "1", "title": "Label Smoothing Meets Noisy Labels"}],
}


def _client(monkeypatch: pytest.MonkeyPatch, files: dict[str, Any]) -> AirasDbClient:
    monkeypatch.setattr(
        client_module, "CONFERENCES_AND_YEARS", {"iclr": ["2020"], "acl": ["2021"]}
    )

    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path in files:
            return httpx.Response(200, json=files[request.url.path])
        return httpx.Response(404)

    return AirasDbClient(
        base_url="https://example.org/data",
        async_session=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
    )


async def test_every_configured_file_is_fetched_and_a_missing_one_is_skipped(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = _client(monkeypatch, {k: v for k, v in FILES.items() if "iclr" in k})
    assert [p["id"] for p in await client.papers()] == ["1", "2"]


async def test_the_index_ranks_titles_from_what_the_client_fetched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = AirasDbPaperSearchIndex(_client(monkeypatch, FILES))
    assert await index.search("label smoothing", 5) == [
        "Label Smoothing Meets Noisy Labels"
    ]
    assert [p["id"] for p in await index.search_papers("attention", 5)] == ["1"]
    assert await index.search("quantum chromodynamics", 5) == []
