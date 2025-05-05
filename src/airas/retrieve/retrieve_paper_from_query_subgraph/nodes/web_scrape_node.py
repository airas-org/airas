import os
import urllib.parse
from logging import getLogger

from airas.utils.api_client.firecrawl_client import FireCrawlClient

logger = getLogger(__name__)

FIRE_CRAWL_API_KEY = os.getenv("FIRE_CRAWL_API_KEY")


def web_scrape_node(
    queries: list,
    scrape_urls: list,
) -> list[str]:
    client = FireCrawlClient()
    logger.info("Executing FireCrawl API scraping...")

    scraped_results = []
    for query in queries:
        for url in scrape_urls:
            full_url = f"{url}&search={urllib.parse.quote_plus(query)}"
            logger.info(f"Scraping URL: {full_url}")

            try:
                response = client.scrape(full_url)
            except Exception as e:
                logger.error(f"Error with FireCrawl API: {e}")
                raise RuntimeError(f"FireCrawl API error for URL: {full_url}") from e
            data = response.get("data") if isinstance(response, dict) else None
            if not data:
                logger.warning(f"No data returned for URL: {full_url}")
                continue
            markdown = data.get("markdown")
            if not markdown:
                logger.warning(f"'markdown' missing in data for URL: {full_url}")
                continue
            scraped_results.append(markdown)

    if not scraped_results:
        raise RuntimeError("No markdown obtained for any URL")
    return scraped_results


if __name__ == "__main__":
    queries = ["deep learning"]
    scrape_urls = ["https://iclr.cc/virtual/2024/papers.html?filter=title"]

    scraped_results = web_scrape_node(queries, scrape_urls=scrape_urls)
    print(f"Scraped results: {scraped_results}")
