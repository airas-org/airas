"""Confirming a paper exists, through the registry behind each identifier."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import feedparser
import httpx

from airas.infra.arxiv_client import ArxivClient
from airas.usecases.retrieve.search_papers_subgraph.nodes.search_airas_db import (
    _parse_authors,
)


def airas_db_metadata(record: dict[str, Any]) -> dict[str, Any]:
    year = record.get("year")
    paper_url = record.get("paper_url")
    return {
        "title": record.get("title") or "",
        "authors": _parse_authors(record.get("authors")),
        "year": int(year) if year else None,
        "venue": record.get("conference") or "",
        "url": paper_url if paper_url and paper_url != "None" else None,
    }


async def verify_existence(
    *,
    airas_db_record: dict[str, Any] | None,
    doi: str | None,
    arxiv_id: str | None,
    arxiv: ArxivClient,
    http: httpx.AsyncClient,
) -> tuple[dict[str, str], str]:
    """registry -> found | not_found | 'error: ...' for the registry behind
    each identifier given, and when it was asked. The same check for a paper
    from airas-papers-db and for one the agent found on the web."""
    # TODO: OpenAlex / Semantic Scholar could confirm and enrich too; skipped
    # because the indexers miss papers the resolvers know.
    registries: dict[str, str] = {}
    if airas_db_record is not None:
        registries["airas_db"] = "found" if airas_db_record else "not_found"

    if doi:
        try:
            response = await http.head(
                f"https://doi.org/{doi}", timeout=30.0, follow_redirects=False
            )
            registries["doi.org"] = (
                "found"
                if response.is_redirect or response.is_success
                else "not_found"
                if response.status_code == 404
                else f"error: {response.status_code}"
            )
        except httpx.HTTPError as e:
            registries["doi.org"] = f"error: {e}"

    if arxiv_id:
        try:
            feed = feedparser.parse(await arxiv.aget_paper_by_id(arxiv_id))
            registries["arxiv"] = "found" if feed.entries else "not_found"
        except Exception as e:
            registries["arxiv"] = f"error: {e}"
    return registries, datetime.now(timezone.utc).isoformat(timespec="seconds")
