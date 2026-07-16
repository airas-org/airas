from io import BytesIO
from logging import getLogger

import httpx
from pypdf import PdfReader

logger = getLogger(__name__)

REQUEST_TIMEOUT_SECONDS = 60.0


async def download_pdf_text(pdf_url: str) -> str:
    """Download a PDF and return its extracted text ("" on failure)."""
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await client.get(pdf_url, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()

        pdf_reader = PdfReader(BytesIO(response.content))
        text = "".join((page.extract_text() or "") for page in pdf_reader.pages)
        return text.replace("\n", " ").strip()
    except Exception as e:  # pragma: no cover - network/IO errors
        logger.warning(f"Failed to extract text from PDF {pdf_url}: {e}")
        return ""
