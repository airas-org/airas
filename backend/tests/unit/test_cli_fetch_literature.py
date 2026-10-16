import sys
from typing import Any

import pytest

from airas import cli
from airas.mcp import context
from airas.usecases.literature import fetch_literature as module


def test_cli_forwards_identifier_arrays(
    tmp_path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []

    async def fetch(query, output_dir, **kwargs: Any) -> None:
        calls.append({"query": query, "output_dir": output_dir, **kwargs})

    for name in ("_openalex_client", "_semantic_scholar_client", "_arxiv_client"):
        monkeypatch.setattr(context, name, lambda: None)
    monkeypatch.setattr(module, "fetch_literature", fetch)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "airas",
            "fetch-literature",
            "--output-dir",
            str(tmp_path),
            "--arxiv-ids",
            '["1706.03762v1"]',
            "--dois",
            '["10.18653/v1/N18-3011"]',
        ],
    )
    cli.main()
    assert calls[0]["query"] is None
    assert calls[0]["arxiv_ids"] == ["1706.03762v1"]
    assert calls[0]["dois"] == ["10.18653/v1/N18-3011"]
    assert calls[0]["output_dir"] == tmp_path


@pytest.mark.parametrize(
    "value", ['["1706.03762v1"', "{}", '"1706.03762"', "[1]", "null"]
)
def test_cli_rejects_invalid_identifier_arrays(
    tmp_path, monkeypatch: pytest.MonkeyPatch, value: str
) -> None:
    monkeypatch.setattr(
        cli, "_run_fetch_literature", lambda args: pytest.fail("must not fetch")
    )
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "airas",
            "fetch-literature",
            "--output-dir",
            str(tmp_path),
            "--arxiv-ids",
            value,
        ],
    )
    with pytest.raises(SystemExit) as error:
        cli.main()
    assert error.value.code == 2
