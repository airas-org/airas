import os
import re
import shutil
from logging import getLogger
from urllib.parse import urlparse

import requests
from langchain_community.document_loaders import PyPDFLoader

logger = getLogger(__name__)


def _extract_text_from_pdf(pdf_path: str) -> str | None:
    try:
        loader = PyPDFLoader(pdf_path)
        pages = loader.load_and_split()
        return "".join(p.page_content.replace("\n", "") for p in pages)
    except Exception as e:
        logger.error(f"Failed to extract text from {pdf_path}: {e}")
        return None


def retrieve_text_from_url(
    papers_dir: str,
    pdf_url: str,
) -> str:
    if not pdf_url:
        logger.warning("Empty URL provided")
        return ""

    # Generate cache key from URL
    parsed_url = urlparse(pdf_url)
    if "arxiv.org" in pdf_url:
        # Extract ArXiv ID for better cache key
        arxiv_id = re.sub(r"^https?://arxiv\.org/abs/", "", pdf_url)
        cache_key = f"arxiv_{arxiv_id}"
    else:
        # Use URL-based cache key for non-ArXiv URLs
        cache_key = f"pdf_{parsed_url.netloc}_{parsed_url.path.replace('/', '_')}"
        # Clean up the cache key
        cache_key = re.sub(r"[^\w_-]", "_", cache_key)

    text_path = os.path.join(papers_dir, f"{cache_key}.txt")
    pdf_path = os.path.join(papers_dir, f"{cache_key}.pdf")

    # 1) If text cache exists, load and return immediately
    if os.path.exists(text_path):
        try:
            with open(text_path, "r", encoding="utf-8") as f:
                text = f.read()
            logger.info(f"Loaded cached text from {text_path}")
            return text
        except Exception as e:
            logger.warning(f"Failed to read cached text: {e}")

    # 2) Download the PDF
    try:
        # Convert arXiv abstract URL to PDF URL if needed
        if "arxiv.org/abs/" in pdf_url:
            pdf_url = pdf_url.replace("/abs/", "/pdf/") + ".pdf"
        else:
            pdf_url = pdf_url

        response = requests.get(pdf_url, stream=True, timeout=30)
        response.raise_for_status()

        os.makedirs(papers_dir, exist_ok=True)
        with open(pdf_path, "wb") as fp:
            shutil.copyfileobj(response.raw, fp)
        logger.info(f"Downloaded PDF from {pdf_url} to {pdf_path}")

    except Exception as e:
        logger.error(f"Failed to download PDF from {pdf_url}: {e}")
        return ""

    # 3) Extract text from the downloaded PDF
    full_text = _extract_text_from_pdf(pdf_path)
    if full_text is None:
        return ""

    # 4) Save the extracted text to cache
    try:
        os.makedirs(papers_dir, exist_ok=True)
        with open(text_path, "w", encoding="utf-8", errors="replace") as f:
            f.write(full_text)
        logger.info(f"Saved extracted text to {text_path}")
    except Exception as e:
        logger.warning(f"Failed to save text cache: {e}")

    return full_text
