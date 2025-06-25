import os
import re
import shutil
from logging import getLogger

from langchain_community.document_loaders import PyPDFLoader

from airas.services.api_client.arxiv_client import (
    ArxivClient,
    ArxivClientFatalError,
    ArxivClientRetryableError,
)

logger = getLogger(__name__)


def _extract_text_from_pdf(pdf_path: str) -> str | None:
    try:
        loader = PyPDFLoader(pdf_path)
        pages = loader.load_and_split()
        return "".join(p.page_content.replace("\n", "") for p in pages)
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return None


def retrieve_arxiv_text_from_url(
    papers_dir: str,
    arxiv_url: str,
    client: ArxivClient | None = None,
) -> str:
    if client is None:
        client = ArxivClient()

    arxiv_id = re.sub(r"^https?://arxiv\.org/abs/", "", arxiv_url)
    text_path = os.path.join(papers_dir, f"{arxiv_id}.txt")
    pdf_path = os.path.join(papers_dir, f"{arxiv_id}.pdf")

    # 1) If text cache exists, load and return immediately
    if os.path.exists(text_path):
        with open(text_path, "r", encoding="utf-8") as f:
            text = f.read()
        logger.info(f"Loaded text from {text_path}")
        return text

    # 2) Download the PDF
    try:
        response = client.fetch_pdf(arxiv_id)
    except (ArxivClientRetryableError, ArxivClientFatalError):
        logger.error("Failed to fetch PDF, aborting")
        return ""

    try:
        os.makedirs(os.path.dirname(pdf_path), exist_ok=True)
        with open(pdf_path, "wb") as fp:
            shutil.copyfileobj(response.raw, fp)
        logger.info(f"Saved PDF to {pdf_path}")
    except Exception as e:
        logger.error(f"Failed to save PDF: {e}")
        return ""

    # 3) Extract text from the downloaded PDF
    full_text = _extract_text_from_pdf(pdf_path)
    if full_text is None:
        return ""

    # 4) Save the extracted text to cache
    try:
        os.makedirs(os.path.dirname(text_path), exist_ok=True)
        with open(text_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(full_text)
        logger.info(f"Saved extracted text to {text_path}")
    except Exception as e:
        logger.warning(f"Failed to save text cache: {e}")

    return full_text
