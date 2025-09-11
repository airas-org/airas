import asyncio
import logging
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

from airas.types.research_hypothesis import ResearchHypothesis

logger = logging.getLogger(__name__)


def _extract_resources_from_html(
    soup, query: str, max_results: int = 10
) -> list[dict[str, str]]:
    results = []

    # Find search items using multiple fallback strategies
    search_items = (
        soup.find_all("article", class_=lambda x: x and "overview-card-wrapper" in x)
        or soup.find_all("article")
        or soup.find_all("div", class_=lambda x: x and "search" in x.lower())
    )

    for item in search_items[:max_results]:
        try:
            main_link = item.find(
                "a", class_=lambda x: x and "flex" in x and "items-center" in x
            )
            if not main_link:
                continue

            link = main_link.get("href", "")
            if not link:
                continue

            item_id = link.strip("/")
            if not link.startswith("http"):
                link = f"https://huggingface.co{link}"

            logger.debug(f"Extracted item_id: '{item_id}' from link: '{link}'")

            title_element = main_link.find(
                "h4", class_=lambda x: x and "font-mono" in x
            )
            if not title_element:
                continue

            title = title_element.get_text(strip=True)
            if not title:
                continue

            metadata = {
                "title": title,
                "link": link,
                "item_id": item_id,
                "search_query": query,
                "readme": "",
            }
            results.append(metadata)

        except Exception as e:
            logger.warning(f"Error extracting resource from item: {e}")
            continue

    return results


async def _get_readme(results: list[dict[str, str]]) -> list[dict[str, str]]:
    enriched_results = []

    async with httpx.AsyncClient(follow_redirects=True) as client:
        for result in results:
            try:
                item_id = result.get("item_id", "")
                if not item_id:
                    enriched_results.append(result)
                    continue

                readme_url = f"https://huggingface.co/{item_id}/resolve/main/README.md"
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }

                response = await client.get(readme_url, headers=headers, timeout=15.0)

                if response.status_code == 200:
                    readme_content = response.text
                    result["readme"] = readme_content[
                        :5000
                    ]  # NOTE: Limit to 5000 chars

            except Exception as e:
                logger.debug(f"Error fetching README for {item_id}: {e}")
                result["readme"] = ""

            enriched_results.append(result)

    return enriched_results


async def _search_huggingface_page(
    search_type: str, query: str, max_results: int = 30
) -> list[dict[str, str]]:
    try:
        base_url = f"https://huggingface.co/{search_type}"
        encoded_query = quote(query)
        search_url = f"{base_url}?sort=likes&search={encoded_query}"

        logger.info(
            f"Searching HuggingFace {search_type} for: {query} (max_results={max_results})"
        )
        logger.info(f"URL: {search_url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(search_url, headers=headers, timeout=30.0)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")

        results = _extract_resources_from_html(soup, query, max_results)
        enriched_results = await _get_readme(results)

        logger.info(
            f"Found {len(enriched_results)} enriched results for {search_type} search: {query}"
        )
        return enriched_results

    except Exception as e:
        logger.error(f"Error searching HuggingFace {search_type} for '{query}': {e}")
        return []


async def search_huggingface_resources(
    new_method: ResearchHypothesis, max_results_per_search: int
) -> dict[str, list[dict[str, str]]]:
    if not new_method.experimental_design or (
        not new_method.experimental_design.expected_models
        and not new_method.experimental_design.expected_datasets
    ):
        logger.warning("No expected models or datasets found in experimental design")
        return {"models": [], "datasets": []}

    search_tasks = [
        ("models", model.strip())
        for model in new_method.experimental_design.expected_models
    ] + [
        ("datasets", dataset.strip())
        for dataset in new_method.experimental_design.expected_datasets
    ]

    logger.info(f"Starting {len(search_tasks)} HuggingFace searches")

    tasks = [
        _search_huggingface_page(search_type, query, max_results_per_search)
        for search_type, query in search_tasks
    ]
    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    search_results: dict[str, list[dict[str, str]]] = {"models": [], "datasets": []}
    for i, result in enumerate(results_list):
        search_type, query = search_tasks[i]
        if isinstance(result, Exception):
            logger.error(f"Error in search task for {search_type}:{query}: {result}")
        else:
            search_results[search_type].extend(result)

    logger.info(
        f"HuggingFace search completed. Found {len(search_results['models'])} model results, "
        f"{len(search_results['datasets'])} dataset results"
    )

    return search_results


async def main():
    from airas.types.research_hypothesis import ExperimentalDesign

    new_method = ResearchHypothesis(
        method="A novel approach to image classification using vision transformers",
        experimental_design=ExperimentalDesign(
            expected_models=["ResNet-50", "Vision Transformer", "BERT"],
            expected_datasets=["CIFAR-10", "ImageNet", "IMDB"],
        ),
    )
    result = await search_huggingface_resources(new_method)
    print(f"result: {result}")


if __name__ == "__main__":
    asyncio.run(main())
