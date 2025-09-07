# import logging
# from concurrent.futures import ThreadPoolExecutor, as_completed

# import requests
# from bs4 import BeautifulSoup

# from airas.types.research_hypothesis import ResearchHypothesis

# logger = logging.getLogger(__name__)


# def _fetch_huggingface_page_details(resource: dict[str, str]) -> dict[str, str]:
#     try:
#         url = resource["url"]
#         logger.info(f"Fetching details for: {url}")

#         headers = {
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
#         }
#         response = requests.get(url, headers=headers, timeout=30)
#         response.raise_for_status()

#         soup = BeautifulSoup(response.content, "html.parser")

#         # Extract README/Model Card content
#         readme_content = ""
#         readme_section = (
#             soup.find("div", class_=lambda x: x and "readme" in x.lower())
#             or soup.find("article")
#             or soup.find("div", {"id": "readme"})
#             or soup.find("div", class_=lambda x: x and "model-card" in x.lower())
#         )

#         if readme_section:
#             readme_content = readme_section.get_text(strip=True)

#         # Extract code examples
#         code_examples = []
#         code_blocks = soup.find_all("code") + soup.find_all("pre")
#         for code_block in code_blocks:
#             code_text = code_block.get_text(strip=True)
#             if code_text and len(code_text) > 20:  # Filter out very short code snippets
#                 code_examples.append(code_text)

#         # Extract usage information
#         usage_info = ""
#         usage_section = soup.find("div", class_=lambda x: x and "usage" in x.lower())
#         if usage_section:
#             usage_info = usage_section.get_text(strip=True)

#         # Extract tags/labels for better understanding
#         tags = []
#         tag_elements = soup.find_all("span", class_=lambda x: x and "tag" in x.lower())
#         for tag_elem in tag_elements:
#             tag_text = tag_elem.get_text(strip=True)
#             if tag_text:
#                 tags.append(tag_text)

#         # Extract download/install instructions
#         install_info = ""
#         install_section = soup.find(
#             "div", class_=lambda x: x and "install" in x.lower()
#         )
#         if install_section:
#             install_info = install_section.get_text(strip=True)

#         detailed_info = {
#             "title": resource.get("title", ""),
#             "url": url,
#             "justification": resource.get("justification", ""),
#             "resource_type": resource.get("resource_type", ""),
#             "readme_content": readme_content[:2000],  # Limit to avoid too much content
#             "code_examples": code_examples[:3],  # Limit to first 3 examples
#             "usage_info": usage_info[:1000] if usage_info else "",
#             "tags": tags[:10],  # Limit tags
#             "install_info": install_info[:500] if install_info else "",
#         }

#         logger.info(f"Successfully fetched details for: {resource.get('title', url)}")
#         return detailed_info

#     except Exception as e:
#         logger.error(
#             f"Error fetching details for {resource.get('url', 'unknown URL')}: {e}"
#         )
#         return {
#             "title": resource.get("title", ""),
#             "url": resource.get("url", ""),
#             "justification": resource.get("justification", ""),
#             "resource_type": resource.get("resource_type", ""),
#             "error": str(e),
#             "readme_content": "",
#             "code_examples": [],
#             "usage_info": "",
#             "tags": [],
#             "install_info": "",
#         }


# def fetch_resource_details(
#     new_method: ResearchHypothesis,
#     selected_resources: dict[str, list[dict[str, str]]],
# ) -> ResearchHypothesis:
#     if not selected_resources or (
#         not selected_resources.get("models") and not selected_resources.get("datasets")
#     ):
#         logger.warning("No selected resources to fetch details for")
#         return {"models": [], "datasets": []}

#     detailed_resources = {"models": [], "datasets": []}

#     # Collect all resources to fetch
#     all_resources = []
#     for resource_type in ["models", "datasets"]:
#         if selected_resources.get(resource_type):
#             for resource in selected_resources[resource_type]:
#                 all_resources.append((resource_type, resource))

#     if not all_resources:
#         logger.warning("No resources to fetch details for")
#         return detailed_resources

#     logger.info(f"Fetching details for {len(all_resources)} resources in parallel")

#     with ThreadPoolExecutor(
#         max_workers=3
#     ) as executor:  # Limit to 3 to be respectful to HuggingFace
#         # Submit all fetch tasks
#         future_to_resource = {
#             executor.submit(_fetch_huggingface_page_details, resource): (
#                 resource_type,
#                 resource,
#             )
#             for resource_type, resource in all_resources
#         }

#         # Collect results as they complete
#         for future in as_completed(future_to_resource):
#             resource_type, original_resource = future_to_resource[future]
#             try:
#                 detailed_info = future.result()
#                 detailed_resources[resource_type].append(detailed_info)
#             except Exception as e:
#                 logger.error(
#                     f"Error fetching details for {original_resource.get('title', 'unknown')}: {e}"
#                 )
#                 # Add error resource to maintain structure
#                 error_resource = original_resource.copy()
#                 error_resource["error"] = str(e)
#                 detailed_resources[resource_type].append(error_resource)

#     logger.info(
#         f"Fetched details for {len(detailed_resources['models'])} models and "
#         f"{len(detailed_resources['datasets'])} datasets"
#     )

#     # Update the new_method with the retrieved external resources information
#     updated_method = new_method.model_copy(deep=True)
#     if updated_method.experimental_design:
#         # Format the detailed resources into a text format for external_resources field
#         formatted_text = "# Retrieved External Resources\\n\\n"

#         for resource_type in ["models", "datasets"]:
#             if detailed_resources.get(resource_type):
#                 formatted_text += f"## {resource_type.title()}\\n\\n"
#                 for resource in detailed_resources[resource_type]:
#                     formatted_text += f"### {resource.get('title', 'Unknown')}\\n"
#                     formatted_text += f"- URL: {resource.get('url', '')}\\n"
#                     formatted_text += (
#                         f"- Justification: {resource.get('justification', '')}\\n"
#                     )
#                     if resource.get("usage_info"):
#                         formatted_text += (
#                             f"- Usage: {resource['usage_info'][:200]}...\\n"
#                         )
#                     if resource.get("code_examples"):
#                         formatted_text += f"- Code Examples: {len(resource['code_examples'])} examples available\\n"
#                     formatted_text += "\\n"

#         updated_method.experimental_design.external_resources = formatted_text

#     return updated_method
