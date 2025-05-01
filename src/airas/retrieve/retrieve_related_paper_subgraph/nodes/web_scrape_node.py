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
                markdown = (
                    (response.get("data") or {}).get("markdown") if response else None
                )
                if markdown:
                    scraped_results.append(markdown)
                else:
                    logger.warning("'markdown' not found in response data")
            except Exception as e:
                logger.error(f"Error with FireCrawl API: {e}")
    return scraped_results


if __name__ == "__main__":
    queries = ["deep learning"]
    scrape_urls = ["https://iclr.cc/virtual/2024/papers.html?filter=title"]

    scraped_results = web_scrape_node(queries, scrape_urls=scrape_urls)
    print(f"Scraped results: {scraped_results}")
