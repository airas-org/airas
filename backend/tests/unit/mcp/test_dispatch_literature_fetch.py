import json
from typing import Any

import pytest

from airas.mcp.tools import literature


class Github:
    def __init__(self):
        self.calls: list[dict[str, Any]] = []

    async def acreate_workflow_dispatch(self, *args, **kwargs):
        self.calls.append(kwargs)
        return {"workflow_run_id": 123, "html_url": "https://example.org/run/123"}


async def test_direct_identifiers_reach_the_workflow_without_a_search(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Github()
    monkeypatch.setattr(literature, "_github_client", lambda: client)
    result = await literature.dispatch_literature_fetch(
        "owner",
        "repo",
        "research",
        arxiv_ids=["1706.03762v1"],
        dois=["10.18653/v1/N18-3011"],
    )
    assert result["workflow_run_id"] == 123
    call = client.calls[0]
    assert call["ref"] == "research"
    assert call["inputs"]["query"] == ""
    assert json.loads(call["inputs"]["arxiv_ids"]) == ["1706.03762v1"]
    assert json.loads(call["inputs"]["dois"]) == ["10.18653/v1/N18-3011"]


async def test_query_dispatch_keeps_the_search_options(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = Github()
    monkeypatch.setattr(literature, "_github_client", lambda: client)
    await literature.dispatch_literature_fetch("owner", "repo", "research", "attention")
    assert client.calls[0]["inputs"] == {
        "query": "attention",
        "sources": "arxiv,airas_records",
        "max_results_per_source": "5",
        "year": "",
        "openalex_semantic": "false",
        "arxiv_ids": "[]",
        "dois": "[]",
    }


async def test_ambiguous_input_is_rejected_before_dispatch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        literature, "_github_client", lambda: pytest.fail("must not dispatch")
    )
    with pytest.raises(ValueError, match="either"):
        await literature.dispatch_literature_fetch(
            "owner", "repo", "research", "attention", arxiv_ids=["1706.03762"]
        )
