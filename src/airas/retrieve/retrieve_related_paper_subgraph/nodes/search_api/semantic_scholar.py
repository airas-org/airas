# %%
import os
import json
import shutil
import requests
from langchain_community.document_loaders import PyPDFLoader
from semanticscholar import SemanticScholar
from pydantic import BaseModel, ValidationError, validate_call

from airas.core.node import Node
from airas.nodes.retrievenode.base.paper_search import PaperSearch


class SemanticScholarResponse(BaseModel):
    paper_title: str
    paper_abstract: str
    authors: list[str]
    publication_date: str


class SemanticScholarNode(Node, PaperSearch):
    @validate_call
    def __init__(
        self,
        input_key: list[str],
        output_key: list[str],
        save_dir: str,
        num_retrieve_paper: int,
    ):
        super().__init__(input_key, output_key)
        self.save_dir = save_dir
        self.num_retrieve_paper = num_retrieve_paper

    def search_paper(
        self, keywords: str | list[str], num_retrieve_paper: int
    ) -> list[dict]:
        """Search papers using Semantic Scholar API."""

        sch = SemanticScholar()
        search_results = []
        for keyword in keywords:
            results = sch.search_paper(keyword, limit=num_retrieve_paper)
            for item in results:
                try:
                    validated_result = SemanticScholarResponse(
                        paper_title=getattr(item, "title", "Unknown Title"),
                        paper_abstract=getattr(
                            item, "abstract", "No abstract available."
                        ),
                        authors=getattr(item, "authors", []),
                        publication_date=getattr(
                            item, "publicationDate", "Unknown date"
                        ),
                    )
                    search_results.append(validated_result.model_dump())
                except ValidationError as e:
                    print(f"Validation error for item {item}: {e}")
        return search_results

    def _download_from_arxiv_id(self, arxiv_id: str) -> None:
        """Download PDF file from arXiv

        Args:
            arxiv_id (_type_): _description_
        """

        url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
        response = requests.get(url, stream=True)

        if response.status_code == 200:
            with open(os.path.join(self.save_dir, f"{arxiv_id}.pdf"), "wb") as file:
                shutil.copyfileobj(response.raw, file)
            print(f"Downloaded {arxiv_id}.pdf to {self.save_dir}")
        else:
            print(f"Failed to download {arxiv_id}.pdf")

    def _download_from_arxiv_ids(self, arxiv_ids: list[str]) -> None:
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
            self._download_from_arxiv_id(arxiv_id)

    def _convert_pdf_to_text(self, pdf_path: str) -> str:
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
        search_results = self.search_paper(
            keywords=keywords, num_retrieve_paper=self.num_retrieve_paper
        )

        arxiv_ids = [
            item.get("externalIds", {}).get("ArXiv")
            for item in search_results
            if item.get("externalIds", {}).get("ArXiv")
        ]

        self._download_from_arxiv_ids(arxiv_ids[: self.num_retrieve_paper])

        paper_list_dict = {}
        for idx, filename in enumerate(os.listdir(self.save_dir)):
            if filename.endswith(".pdf"):
                pdf_path = os.path.join(self.save_dir, filename)
                paper_content = self._convert_pdf_to_text(pdf_path)
                paper_key = f"paper_{idx+1}"
                paper_list_dict[paper_key] = paper_content

        return {self.output_key[0]: paper_list_dict}
