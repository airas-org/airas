import os
import time
import httpx
import urllib.parse
from logging import getLogger

logger = getLogger(__name__)

FIRE_CRAWL_API_KEY = os.getenv("FIRE_CRAWL_API_KEY")


def web_scrape_node(queries: list, scrape_urls: list) -> list[dict]:
    if not FIRE_CRAWL_API_KEY:
        logger.warning("FIRE_CRAWL_API_KEY environment variable is not set")
        return []

    logger.info("Executing FireCrawl API scraping...")
    scrape_params = {
        "formats": ["markdown"],
        "onlyMainContent": True,
        "waitFor": 5000,
        "timeout": 15000,
    }

    scraped_results = []
    for query in queries:
        for url in scrape_urls:
            full_url = f"{url}&search={urllib.parse.quote_plus(query)}"
            logger.info(f"Scraping URL: {full_url}")
            try:
                response = firecrawl_scrape(url=full_url, params=scrape_params)
                data = response.get("data")
                if data and isinstance(data, dict):
                    scraped_result = data.get("markdown", "")
                    if scraped_result:
                        scraped_results.append(scraped_result)
                    else:
                        logger.warning("'markdown' not found in response data")
                else:
                    logger.warning("Unexpected response format or no data")
            except Exception as e:
                logger.error(f"Error with FireCrawl API: {e}")
                logger.error("FireCrawl API failed - returning empty results")
    return scraped_results


def firecrawl_scrape(
    url: str,
    params: dict,
    api_url: str = "https://api.firecrawl.dev/v1",
    initial_wait_time: int = 1,
    max_wait_time: int = 10,
    max_retries: int = 3,
) -> dict:
    endpoint = f"{api_url}/scrape"
    headers = {
        "Authorization": f"Bearer {FIRE_CRAWL_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {"url": url, **params}

    retry_count = 0
    wait_time = initial_wait_time
    while retry_count < max_retries:
        try:
            with httpx.Client(timeout=httpx.Timeout(60.0)) as client:
                response = client.post(endpoint, json=data, headers=headers)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"Attempt {retry_count+1} failed with HTTP error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error on attempt {retry_count+1}: {e}")

        logger.info(f"Retrying in {wait_time} seconds...")
        time.sleep(wait_time)
        wait_time = min(wait_time * 2, max_wait_time)
        retry_count += 1
    raise Exception("Max retries reached. Scrape URL API request failed.")


if __name__ == "__main__":
    queries = ["deep learning"]
    scrape_urls = ["https://iclr.cc/virtual/2024/papers.html?filter=title"]

    scraped_results = web_scrape_node(queries, scrape_urls=scrape_urls)
    print(f"Scraped results: {scraped_results}")
