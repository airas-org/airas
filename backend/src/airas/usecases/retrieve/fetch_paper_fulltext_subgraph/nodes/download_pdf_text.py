from logging import getLogger

import httpx
import pymupdf

logger = getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 60.0


async def download_pdf_pages(pdf_url: str) -> list[str]:
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(pdf_url, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
        with pymupdf.open(stream=response.content, filetype="pdf") as document:
            return [page.get_text("text") for page in document]
    except Exception as e:  # pragma: no cover - network/IO errors
        logger.warning(f"Failed to extract text from PDF {pdf_url}: {e}")
        return []


def parser_version() -> str:
    return f"pymupdf {pymupdf.__version__}"
