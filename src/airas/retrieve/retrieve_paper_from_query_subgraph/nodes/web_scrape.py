import os
import urllib.parse
from logging import getLogger

from airas.utils.api_client.firecrawl_client import FireCrawlClient

logger = getLogger(__name__)

FIRE_CRAWL_API_KEY = os.getenv("FIRE_CRAWL_API_KEY")


def web_scrape(
    queries: list,
    scrape_urls: list,
    client: FireCrawlClient | None = None
) -> list[str]:
    if client is None:
        client = FireCrawlClient()
    logger.info("Executing FireCrawl API scraping...")

    scraped_results = []
    for query in queries:
        for url in scrape_urls:
            full_url = f"{url}&search={urllib.parse.quote_plus(query)}"
            logger.info(f"Scraping URL: {full_url}")

            try:
                response = client.scrape(full_url)
            except ValueError as e:
                logger.warning(f"Empty content for {full_url}: {e}")
                continue 
            data = response.get("data") if isinstance(response, dict) else None
            if not data:
                logger.warning(f"No data returned for URL: {full_url}")
                continue
            markdown = data.get("markdown")
            if not markdown.strip():
                logger.warning(f"'markdown' missing in data for URL: {full_url}")
                continue
            scraped_results.append(markdown)

    if not scraped_results:
        raise RuntimeError("No markdown obtained for any URL")
    return scraped_results