# %%
import os
import json
import shutil
import requests
import re
import pyalex
from langchain_community.document_loaders import PyPDFLoader
from datetime import datetime
from pydantic import BaseModel, ValidationError
from airas.core.node import Node
from airas.nodes.retrievenode.base.paper_search import PaperSearch


class OpenAlexResponse(BaseModel):
    title: str
    paper_abstract: str
    author: str
    public_date: datetime


class OpenAlexNode(Node, PaperSearch):
    def __init__(
        self,
        input_key: list[str],
        output_key: list[str],
        save_dir: str,
        num_keywords: int,
        num_retrieve_paper: int,
    ):
        super().__init__(input_key, output_key)
        self.save_dir = save_dir
        self.num_keywords = num_keywords
        self.num_retrieve_paper = num_retrieve_paper

    def search_paper(
        self, keywords: str | list[str], num_retrieve_paper: int
    ) -> list[dict]:
        """Search papers using OpenAlex API."""
        works = pyalex.Works().filter(publication_year=">2011", is_oa=True)
        search_results = []
        for keyword in keywords:
            results = works.search(keyword).get(page=1, per_page=num_retrieve_paper)

            # Validate each result using Pydantic
            validated_results = []
            for item in results:
                try:
                    validated_result = OpenAlexResponse(
                        paper_abstract=item.get("abstract", ""),
                        author=item.get("author", "Unknown"),
                        public_date=datetime.strptime(
                            item.get("publication_date", "1970-01-01"), "%Y-%m-%d"
                        ),
                    )
                    validated_results.append(validated_result)
                except ValidationError as e:
                    print(f"Validation error for item {item}: {e}")

            search_results.append(validated_results)
        return search_results

    def download_from_arxiv_id(self, arxiv_id: str) -> None:
        """Download PDF file from arXiv

        Args:
            arxiv_id (_type_): _description_
            save_dir (_type_): _description_
        """

        url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            with open(os.path.join(self.save_dir, f"{arxiv_id}.pdf"), "wb") as file:
                shutil.copyfileobj(response.raw, file)
            print(f"Downloaded {arxiv_id}.pdf to {self.save_dir}")
        else:
            print(f"Failed to download {arxiv_id}.pdf")

    def download_from_arxiv_ids(self, arxiv_ids: list[str]) -> None:
        """Download PDF files from arXiv

        Args:
            arxiv_ids (_type_): _description_
            save_dir (_type_): _description_
        """
        # save_dirが存在しない場合、ディレクトリを作成
        if not os.path.exists(self.save_dir):
            os.makedirs(self.save_dir)
        else:
            shutil.rmtree(self.save_dir)
            os.makedirs(self.save_dir)

        for arxiv_id in arxiv_ids:
            self.download_from_arxiv_id(arxiv_id)

    def convert_pdf_to_text(self, pdf_path):
        """Convert PDF file to text

        Args:
            pdf_path (_type_): _description_

        Returns:
            _type_: _description_
        """

        loader = PyPDFLoader(pdf_path)
        pages = loader.load_and_split()
        content = ""
        for page in pages[:20]:
            content += page.page_content

        return content

    def execute(self, state) -> dict:
        """Retriever

        Args:
            state (_type_): _description_
        """
        keywords = json.loads(state[self.input_key[0]])
        keywords = [keywords[: self.num_keywords]]

        search_results = self.search_paper(
            keywords, num_retrieve_paper=self.num_retrieve_paper
        )

        def _get_arxiv_id_from_url(url: str) -> str | None:
            match = re.search(r"\d{4}\.\d{5}", url)
            if match:
                return match.group()

        for results in search_results:
            arxiv_ids = []

            for item in results:
                print(item.title)
                print(item.id)

                if "arxiv" not in item.indexed_in:
                    continue
                ind_loc = item.indexed_in.index("arxiv")

                arxiv_url = item.locations[ind_loc].landing_page_url
                arxiv_id = _get_arxiv_id_from_url(arxiv_url)
                if arxiv_id is None:
                    continue

                arxiv_ids.append(arxiv_id)
            self.download_from_arxiv_ids(arxiv_ids[: self.num_retrieve_paper])

        return {
            self.output_key[0]: {
                f"paper_{idx + 1}": {
                    "full_text": self.convert_pdf_to_text(
                        os.path.join(self.save_dir, filename)
                    )
                }
                for idx, filename in enumerate(os.listdir(self.save_dir))
                if filename.endswith(".pdf")
            }
        }
