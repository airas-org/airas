import httpx
import pymupdf

from airas.infra.retry_policy import make_retry_policy, raise_for_status

REQUEST_TIMEOUT_SECONDS = 60.0


@make_retry_policy()
async def _download_pdf(pdf_url: str) -> bytes:
    async with httpx.AsyncClient(follow_redirects=True) as client:
        response = await client.get(pdf_url, timeout=REQUEST_TIMEOUT_SECONDS)
    raise_for_status(response, path=pdf_url)
    return response.content


async def fetch_fulltext_from_url(pdf_url: str) -> list[str]:
    with pymupdf.open(stream=await _download_pdf(pdf_url), filetype="pdf") as document:
        return [page.get_text("text") for page in document]


def parser_version() -> str:
    return f"pymupdf {pymupdf.__version__}"
