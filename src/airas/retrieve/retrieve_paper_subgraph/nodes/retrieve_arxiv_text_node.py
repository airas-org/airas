import os
import re
import shutil
import requests
from logging import getLogger
from requests.exceptions import RequestException
from langchain_community.document_loaders import PyPDFLoader

logger = getLogger(__name__)


class RetrievearXivTextNode:
    def __init__(
        self,
        papers_dir: str,
    ):
        self.papers_dir = papers_dir

    def execute(self, arxiv_url: str) -> str:
        arxiv_id = re.sub(r"^https?://arxiv\.org/abs/", "", arxiv_url)

        text_path = os.path.join(self.papers_dir, f"{arxiv_id}.txt")
        pdf_path = os.path.join(self.papers_dir, f"{arxiv_id}.pdf")

        if os.path.exists(text_path):
            with open(text_path, "r", encoding="utf-8") as text_file:
                full_text = text_file.read()
            logger.info(f"Loaded text from {text_path}")

        else:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
            try:
                response = requests.get(pdf_url, stream=True)
                response.raise_for_status()
            except RequestException as e:
                logger.error(f"Failed to download {pdf_url}: {e}")
                return ""
            # NOTE：以下のようにパスが想定外のディレクトとなり，astro-phというディレクトリはないためエラーになる
            # FileNotFoundError: [Errno 2] No such file or directory: '/workspaces/researchgraph/data/20250401_171315/papers/astro-ph/9511008v1.pdf'
            try:
                with open(pdf_path, "wb") as file:
                    shutil.copyfileobj(response.raw, file)
            except Exception as e:
                logger.error(f"Failed to save {pdf_path}: {e}")
                return ""
            loader = PyPDFLoader(pdf_path)
            pages = loader.load_and_split()
            full_text = "".join(page.page_content.replace("\n", "") for page in pages)
            with open(text_path, "w", encoding="utf-8", errors="replace") as text_file:
                text_file.write(full_text)

        return full_text


if __name__ == "__main__":
    papers_dir = "/workspaces/researchgraph/data"
    arxiv_url = "https://arxiv.org/abs/2106.06869"
    retrieve_arxiv_text_node = RetrievearXivTextNode(papers_dir)
    full_text = retrieve_arxiv_text_node.execute(arxiv_url)
    print(type(full_text))
    # print(full_text)
