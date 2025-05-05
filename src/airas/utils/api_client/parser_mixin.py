import logging

import requests

logger = logging.getLogger(__name__)


class ResponseParserMixIn:
    @staticmethod
    def _parse_response(resp: requests.Response) -> dict | str | bytes | None:
        content_type = resp.headers.get("Content-Type", "").lower()
        # JSON response
        if "application/json" in content_type:
            return resp.json() if resp.text.strip() else {}

        # No Content
        if resp.status_code == 204:
            return None

        # Binary (ZIP or octet-stream)
        if any(
            bin_ct in content_type
            for bin_ct in [
                "application/zip",
                "application/octet-stream",
                "application/x-zip-compressed",
            ]
        ):
            if resp.raw:
                return resp
            return resp.content

        # XML/Atom
        if "xml" in content_type:
            return resp

        # Text response
        if "text/" in content_type:
            return resp.text.strip()

        # Unknown format
        logger.warning(f"Unknown Content-Type '{content_type}', returning raw bytes.")
        return resp.content
