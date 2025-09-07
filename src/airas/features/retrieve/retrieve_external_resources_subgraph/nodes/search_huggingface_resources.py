# import logging
# from concurrent.futures import ThreadPoolExecutor, as_completed
# from urllib.parse import quote

# import requests
# from bs4 import BeautifulSoup

# from airas.types.research_hypothesis import ResearchHypothesis

# logger = logging.getLogger(__name__)


# def _search_huggingface_page(search_type: str, query: str) -> list[dict[str, str]]:
#     try:
#         base_url = f"https://huggingface.co/{search_type}"
#         encoded_query = quote(query)
#         search_url = f"{base_url}?sort=trending&search={encoded_query}"

#         logger.info(f"Searching HuggingFace {search_type} for: {query}")
#         logger.info(f"URL: {search_url}")

#         headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
#         }
#         response = requests.get(search_url, headers=headers, timeout=30)
#         response.raise_for_status()

#         soup = BeautifulSoup(response.content, "html.parser")
#         results = []

#         # Find search result items (this may need adjustment based on HuggingFace's current HTML structure)
#         # Looking for common patterns in HuggingFace search results
#         search_items = soup.find_all("article") or soup.find_all(
#             "div", class_=lambda x: x and "search" in x.lower()
#         )

#         for item in search_items[:10]:  # Limit to first 10 results
#             title_element = (
#                 item.find("h3")
#                 or item.find("h4")
#                 or item.find(
#                     "a",
#                     class_=lambda x: x
#                     and any(cls in x.lower() for cls in ["title", "name"]),
#                 )
#                 or item.find("a")
#             )

#             if title_element:
#                 title = title_element.get_text(strip=True)

#                 link_element = (
#                     title_element
#                     if title_element.name == "a"
#                     else title_element.find("a")
#                 )
#                 link = link_element.get("href", "") if link_element else ""

#                 if link and not link.startswith("http"):
#                     link = f"https://huggingface.co{link}"

#                 desc_element = item.find("p") or item.find(
#                     "div", class_=lambda x: x and "desc" in x.lower()
#                 )
#                 description = desc_element.get_text(strip=True) if desc_element else ""

#                 if title and link:
#                     results.append(
#                         {
#                             "title": title,
#                             "link": link,
#                             "description": description,
#                             "search_query": query,
#                             "search_type": search_type,
#                         }
#                     )

#         logger.info(f"Found {len(results)} results for {search_type} search: {query}")
#         return results

#     except Exception as e:
#         logger.error(f"Error searching HuggingFace {search_type} for '{query}': {e}")
#         return []


# def search_huggingface_resources(
#     new_method: ResearchHypothesis,
# ) -> dict[str, list[dict[str, str]]]:
#     if not new_method.experimental_design or (
#         not new_method.experimental_design.expected_models
#         and not new_method.experimental_design.expected_datasets
#     ):
#         logger.warning("No expected models or datasets found in experimental design")
#         return {"models": [], "datasets": []}

#     search_results = {"models": [], "datasets": []}

#     search_tasks = []

#     if new_method.experimental_design.expected_models:
#         for model in new_method.experimental_design.expected_models:
#             search_tasks.append(("models", model.strip()))

#     if new_method.experimental_design.expected_datasets:
#         for dataset in new_method.experimental_design.expected_datasets:
#             search_tasks.append(("datasets", dataset.strip()))

#     if not search_tasks:
#         logger.warning("No search tasks to execute")
#         return search_results

#     logger.info(f"Starting {len(search_tasks)} HuggingFace searches in parallel")

#     with ThreadPoolExecutor(max_workers=5) as executor:
#         # Submit all search tasks
#         future_to_task = {
#             executor.submit(_search_huggingface_page, search_type, query): (
#                 search_type,
#                 query,
#             )
#             for search_type, query in search_tasks
#         }

#         for future in as_completed(future_to_task):
#             search_type, query = future_to_task[future]
#             try:
#                 results = future.result()
#                 search_results[search_type].extend(results)
#             except Exception as e:
#                 logger.error(f"Error in search task for {search_type}:{query}: {e}")

#     logger.info(
#         f"HuggingFace search completed. Found {len(search_results['models'])} model results, "
#         f"{len(search_results['datasets'])} dataset results"
#     )

#     return search_results
