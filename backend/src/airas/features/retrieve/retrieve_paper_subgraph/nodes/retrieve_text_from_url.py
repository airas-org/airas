import asyncio
from io import BytesIO
from logging import getLogger

import httpx
from pypdf import PdfReader

from airas.types.arxiv import ArxivInfo

logger = getLogger(__name__)

MAX_CONCURRENT_REQUESTS = 5
REQUEST_TIMEOUT_SECONDS = 30.0


async def retrieve_text_from_url(
    arxiv_info_list: list[ArxivInfo],
) -> list[str]:
    """Fetch each arXiv PDF and return extracted text asynchronously."""

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

    async def _fetch_for_info(arxiv_info: ArxivInfo) -> str:
        arxiv_id = (arxiv_info.id or "").strip()
        if not arxiv_id:
            logger.warning("Missing arXiv ID; skipping PDF fetch.")
            return ""
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
        return await _fetch_pdf_text(
            client=client,
            semaphore=semaphore,
            pdf_url=pdf_url,
            arxiv_id=arxiv_id,
        )

    async with httpx.AsyncClient(follow_redirects=True) as client:
        text_list: list[str] = list(
            await asyncio.gather(*(_fetch_for_info(info) for info in arxiv_info_list))
        )

    return text_list


async def _fetch_pdf_text(
    client: httpx.AsyncClient,
    semaphore: asyncio.Semaphore,
    pdf_url: str,
    arxiv_id: str,
) -> str:
    async with semaphore:
        try:
            response = await client.get(pdf_url, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()

            pdf_reader = PdfReader(BytesIO(response.content))
            text = "".join((page.extract_text() or "") for page in pdf_reader.pages)
            cleaned = text.replace("\n", " ").strip()
            logger.info(f"Successfully extracted text from arXiv ID '{arxiv_id}'")
            return cleaned
        except Exception as e:  # pragma: no cover - network/IO errors
            logger.error(f"Failed to extract text from PDF {pdf_url}: {e}")
            return ""


if __name__ == "__main__":
    sample_info = ArxivInfo(
        id="1706.03762",
        title="Attention Is All You Need",
        authors=["Vaswani et al."],
        published_date="2017-06-12",
        summary="",
        journal=None,
        doi=None,
        affiliation=None,
    )

    async def _main() -> None:
        results = await retrieve_text_from_url([sample_info])
        extracted_text = results[0]
        print(
            f"Extracted {len(extracted_text)} characters"
            if extracted_text
            else "No text extracted"
        )

    asyncio.run(_main())
