import requests
import feedparser
import pytz
import time
from datetime import datetime, timedelta
from typing import Optional
from pydantic import BaseModel, ValidationError, Field
from logging import getLogger

logger = getLogger(__name__)


class ArxivResponse(BaseModel):
    arxiv_id: str
    arxiv_url: str
    title: str
    authors: list[str]
    published_date: str
    summary: str = Field(default="No summary")


class ArxivNode:
    def __init__(
        self,
        num_retrieve_paper: int = 5,
        period_days: Optional[int] = None,
        max_retries: int = 20,
        initial_wait_time=1,
        max_wait_time=180,
    ):
        self.num_retrieve_paper = num_retrieve_paper
        self.period_days = period_days
        self.start_indices: dict[str, int] = {}  # TODO: stateに持たせる？
        self.max_retries = max_retries
        self.initial_wait_time = initial_wait_time
        self.max_wait_time = max_wait_time

    def _build_arxiv_query(self, query: str) -> str:
        sanitized_query = query.replace(":", "")
        now_utc = datetime.now(pytz.utc)
        if self.period_days is None:
            return f"all:{sanitized_query}"

        from_date = now_utc - timedelta(days=self.period_days)
        from_str = from_date.strftime("%Y-%m-%d")
        to_str = now_utc.strftime("%Y-%m-%d")
        return f"(all:{sanitized_query}) AND submittedDate:[{from_str} TO {to_str}]"

    def _validate_and_convert(self, entry) -> Optional[ArxivResponse]:
        try:
            paper = ArxivResponse(
                arxiv_id=entry.id.split("/")[-1],
                arxiv_url=entry.id,
                title=entry.title or "No Title",
                authors=[a.name for a in entry.authors]
                if hasattr(entry, "authors")
                else [],
                published_date=entry.published
                if hasattr(entry, "published")
                else "Unknown date",
                summary=entry.summary if hasattr(entry, "summary") else "No summary",
            )
            return paper
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return None

    def search_paper(self, query: str) -> list[ArxivResponse]:
        base_url = "http://export.arxiv.org/api/query"
        search_query = self._build_arxiv_query(query)
        start_index = self.start_indices.get(query, 0)

        params = {
            "search_query": search_query,
            "start": start_index,
            "max_results": self.num_retrieve_paper,
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        retry_count = 0
        wait_time = self.initial_wait_time
        response = None
        while retry_count < self.max_retries:
            try:
                response = requests.get(base_url, params=params, timeout=15)
                response.raise_for_status()
                break
            except requests.exceptions.RequestException as exc:
                logger.error(
                    f"Error fetching from arXiv API: {exc}. Retrying in {wait_time} seconds..."
                )
                time.sleep(wait_time)
                retry_count += 1
                wait_time = min(wait_time * 2, self.max_wait_time)
        else:
            logger.warning("Maximum retries reached. Failed to fetch data.")
            return []  # ここで空リストを返すことで例外を防ぐ

        feed = feedparser.parse(response.text)

        validated_list = []
        for entry in feed.entries:
            paper = self._validate_and_convert(entry)
            if paper:
                validated_list.append(paper.model_dump())

        if len(validated_list) == self.num_retrieve_paper:
            if query not in self.start_indices:
                self.start_indices[query] = 0
            self.start_indices[query] += self.num_retrieve_paper

        return validated_list

    def execute(self, queries) -> list[dict]:
        if not queries or not isinstance(queries, list):
            logger.warning("No valid queries. Return empty.")
            return []

        all_papers = []
        for q in queries:
            results = self.search_paper(q)
            all_papers.extend(results)
        return all_papers


if __name__ == "__main__":
    queries = [
        "deep learning",
    ]
    arxiv_node = ArxivNode()
    search_results = arxiv_node.execute(queries)
    print(search_results)
