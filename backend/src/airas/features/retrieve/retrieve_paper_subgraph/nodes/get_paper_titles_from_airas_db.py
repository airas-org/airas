from logging import getLogger
from typing import Any

import httpx

logger = getLogger(__name__)

DB_BASE_URL = "https://raw.githubusercontent.com/airas-org/airas-papers-db/main/data"

# TODO: Allow filtering by conference name.
CONFERENCES_AND_YEARS = {
    "cvpr": ["2023", "2024"],
    "iclr": ["2020", "2021", "2022", "2023", "2024"],
    "icml": ["2020", "2021", "2022", "2023", "2024"],
    "neurips": ["2020", "2021", "2022", "2023", "2024"],
}


def _fetch_all_papers() -> list[dict[str, Any]]:
    all_papers = []
    with httpx.Client() as client:
        for conference, years in CONFERENCES_AND_YEARS.items():
            for year in years:
                url = f"{DB_BASE_URL}/{conference}/{year}.json"
                logger.info(f"Fetching paper data from {url}...")
                try:
                    response = client.get(url, timeout=60)
                    response.raise_for_status()
                    papers = response.json()
                    all_papers.extend(papers)
                except httpx.HTTPStatusError as e:
                    logger.error(
                        f"  -> An error occurred while fetching data from {url}: {e}"
                    )
                except ValueError as e:
                    logger.error(f"  -> Failed to parse JSON from {url}: {e}")
    return all_papers


def get_paper_titles_from_airas_db() -> list[dict[str, Any]]:
    all_papers = _fetch_all_papers()
    if not all_papers:
        return []

    return all_papers
