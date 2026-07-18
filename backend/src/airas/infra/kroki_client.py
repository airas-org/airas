import os
from logging import getLogger

import httpx

from airas.infra.base_http_client import BaseHTTPClient
from airas.infra.retry_policy import make_retry_policy, raise_for_status

logger = getLogger(__name__)

KROKI_RETRY = make_retry_policy()

DEFAULT_KROKI_BASE_URL = "https://kroki.io"


class KrokiClient(BaseHTTPClient):
    """Client for a Kroki diagram-rendering service.

    Kroki renders text diagram notations (mermaid, graphviz, d2, plantuml,
    and 20+ more) into images through a single API. The endpoint defaults
    to the public instance and can be pointed at a self-hosted one via
    KROKI_BASE_URL, which keeps unpublished diagrams on-premises.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        sync_session: httpx.Client | None = None,
        async_session: httpx.AsyncClient | None = None,
    ):
        super().__init__(
            base_url=(
                base_url or os.getenv("KROKI_BASE_URL") or DEFAULT_KROKI_BASE_URL
            ).rstrip("/"),
            sync_session=sync_session,
            async_session=async_session,
        )

    @KROKI_RETRY
    async def arender(
        self,
        diagram_type: str,
        diagram_source: str,
        output_format: str = "svg",
    ) -> bytes:
        path = ""
        resp = await self.apost(
            path=path,
            json={
                "diagram_source": diagram_source,
                "diagram_type": diagram_type,
                "output_format": output_format,
            },
            timeout=60.0,
        )
        raise_for_status(resp, path=f"{diagram_type}/{output_format}")
        return resp.content
