import asyncio
import logging
from typing import Any

from airas.services.api_client.hugging_face_client import (
    HF_RESOURCE_TYPE,
    HuggingFaceClient,
)
from airas.types.hugging_face import (
    HuggingFace,
    HuggingFaceCardData,
    HuggingFaceResource,
    HuggingFaceSibling,
)
from airas.types.research_hypothesis import ResearchHypothesis

logger = logging.getLogger(__name__)


async def search_hugging_face(
    new_method: ResearchHypothesis,
    max_results_per_search: int = 10,
    hf_client: HuggingFaceClient | None = None,
) -> HuggingFace:
    if not new_method.experimental_design or (
        not new_method.experimental_design.expected_models
        and not new_method.experimental_design.expected_datasets
    ):
        logger.warning("No expected models or datasets found in experimental design")
        return HuggingFace(models=[], datasets=[])

    hf_client = hf_client or HuggingFaceClient()

    search_tasks = [
        ("models", model.strip())
        for model in new_method.experimental_design.expected_models
    ] + [
        ("datasets", dataset.strip())
        for dataset in new_method.experimental_design.expected_datasets
    ]

    logger.info(f"Starting {len(search_tasks)} Hugging Face API searches")

    # Execute all searches in parallel
    models_list: list[HuggingFaceResource] = []
    datasets_list: list[HuggingFaceResource] = []

    tasks = [
        _search_resources(hf_client, search_type, query, max_results_per_search)
        for search_type, query in search_tasks
    ]

    results_list = await asyncio.gather(*tasks, return_exceptions=True)

    for i, result in enumerate(results_list):
        search_type, query = search_tasks[i]

        if isinstance(result, Exception):
            logger.error(f"Error in search task for {search_type}:{query}: {result}")
        else:
            if search_type == "models":
                models_list.extend(result)
            else:
                datasets_list.extend(result)

    logger.info(
        f"Hugging Face API search completed. Found {len(models_list)} model results, "
        f"{len(datasets_list)} dataset results"
    )

    return HuggingFace(
        models=models_list,
        datasets=datasets_list,
    )


async def _search_resources(
    hf_client: HuggingFaceClient,
    search_type: HF_RESOURCE_TYPE,
    query: str,
    max_results: int,
) -> list[HuggingFaceResource]:
    try:
        search_response = await hf_client.asearch(
            search_type=search_type,
            search_query=query,
            limit=max_results,
            sort="downloads",
        )

        if not search_response:
            logger.warning(f"No search results found for {search_type}: {query}")
            return []

        resources = search_response if isinstance(search_response, list) else []
        if not resources:
            logger.warning(f"Empty results for {search_type}: {query}")
            return []

        logger.info(f"Found {len(resources)} {search_type} for query: {query}")

        enriched_resources = []

        for resource in resources:
            try:
                enriched_resource = await _enrich_resource(
                    hf_client, search_type, resource
                )
                if enriched_resource:
                    enriched_resources.append(enriched_resource)
            except Exception as e:
                logger.warning(
                    f"Failed to enrich resource {resource.get('id', 'unknown')}: {e}"
                )
                basic_resource = HuggingFaceResource(
                    id=resource.get("id", "unknown"),
                    author=resource.get("author"),
                    downloads=resource.get("downloads", 0),
                    likes=resource.get("likes", 0),
                    readme=f"Error during enrichment: {str(e)}",
                )
                enriched_resources.append(basic_resource)

        return enriched_resources

    except Exception as e:
        logger.error(f"Error searching {search_type} for '{query}': {e}")
        return []


async def _enrich_resource(
    hf_client: HuggingFaceClient,
    search_type: HF_RESOURCE_TYPE,
    resource: dict[str, Any],
) -> HuggingFaceResource | None:
    resource_id = resource.get("id")
    if not resource_id:
        logger.warning(f"Resource missing ID: {resource}")
        return None

    try:
        details_task = hf_client.aget_details(search_type, resource_id)
        readme_task = hf_client.aget_readme(search_type, resource_id)
        results = await asyncio.gather(
            details_task, readme_task, return_exceptions=True
        )

        detailed_resource: dict[str, Any] = {}
        readme_content = ""

        if not isinstance(results[0], Exception):
            detailed_resource = results[0]
        else:
            logger.warning(f"Failed to get details for {resource_id}: {results[0]}")

        if not isinstance(results[1], Exception):
            readme_content = results[1]
        else:
            logger.warning(f"Failed to get README for {resource_id}: {results[1]}")

        hf_resource = _apply_hf_resource_type(
            resource, detailed_resource, readme_content
        )

        # Filter out inaccessible resources - only return accessible ones
        if hf_resource.private or hf_resource.gated or hf_resource.disabled:
            logger.info(
                f"Skipping inaccessible resource: {resource_id} (private={hf_resource.private}, gated={hf_resource.gated}, disabled={hf_resource.disabled})"
            )
            return None

        return hf_resource

    except Exception as e:
        logger.error(f"Error enriching resource {resource_id}: {e}")
        return None


def _apply_hf_resource_type(
    resource: dict,
    detailed_resource: dict,
    readme_content: str,
) -> HuggingFaceResource:
    merged_data = {**resource, **detailed_resource}

    siblings_data = merged_data.get("siblings", [])
    siblings = [
        HuggingFaceSibling(**sibling)
        for sibling in siblings_data[
            :10
        ]  # NOTE: Limit siblings to first 10 to prevent huge JSON output
        if isinstance(sibling, dict) and "rfilename" in sibling
    ]

    card_data_raw = merged_data.get("cardData", {})
    card_data = HuggingFaceCardData(**card_data_raw) if card_data_raw else None

    return HuggingFaceResource(
        id=merged_data.get("id", ""),
        author=merged_data.get("author"),
        sha=merged_data.get("sha"),
        created_at=merged_data.get("createdAt"),
        last_modified=merged_data.get("lastModified"),
        private=merged_data.get("private", False),
        gated=merged_data.get("gated", False),
        disabled=merged_data.get("disabled", False),
        downloads=merged_data.get("downloads", 0),
        likes=merged_data.get("likes", 0),
        siblings=siblings,
        card_data=card_data,
        tags=merged_data.get("tags", []),
        pipeline_tag=merged_data.get("pipeline_tag"),
        library_name=merged_data.get("library_name"),
        readme=readme_content[:5000]
        if readme_content
        else "",  # NOTE: Limit README to first 5k to prevent huge data
        model_index=merged_data.get("model_index"),
    )


async def main():
    from airas.types.research_hypothesis import ExperimentalDesign

    new_method = ResearchHypothesis(
        method="A novel approach to image classification using vision transformers",
        experimental_design=ExperimentalDesign(
            expected_models=["ResNet-50", "Vision Transformer"],
            expected_datasets=["CIFAR-10", "ImageNet"],
        ),
    )

    result = await search_hugging_face(new_method, max_results_per_search=2)

    print("\n" + "=" * 80)
    print("HUGGING FACE SEARCH RESULTS SUMMARY")
    print("=" * 80 + "\n")

    # -------------------------
    # MODELSの全フィールドを出力
    # -------------------------
    if result.models:
        for _, model in enumerate(result.models):
            print(f"  id: {model.id}")
            print(f"  author: {model.author}")
            print(f"  sha: {model.sha}")
            print(f"  created_at: {model.created_at}")
            print(f"  last_modified: {model.last_modified}")
            print(f"  private: {model.private}")
            print(f"  gated: {model.gated}")
            print(f"  disabled: {model.disabled}")
            print(f"  downloads: {model.downloads}")
            print(f"  likes: {model.likes}")
            print(f"  tags: {model.tags}")
            print(f"  pipeline_tag: {model.pipeline_tag}")
            print(f"  library_name: {model.library_name}")
            print("  siblings (First 5 files):")
            if model.siblings:
                for sibling in model.siblings[:5]:
                    print(f"    - {sibling.rfilename}")
            else:
                print("    (No files listed)")
            print("  card_data:")
            if model.card_data:
                for key, value in model.card_data.model_dump().items():
                    if value:
                        print(f"    - {key}: {value}")
            else:
                print("    (No card data available)")

            print(f"  model_index: {model.model_index}")

            print("  readme (Snippet):")
            if model.readme:
                snippet = model.readme.replace("\n", " ").strip()
                print(f'    "{snippet[:250]}..."')
            else:
                print("    (README not found or failed to load)")
            print("-" * 50)
    else:
        print("\nNo models found for the given queries.")

    # -------------------------
    # DATASETSの全フィールドを出力
    # -------------------------
    if result.datasets:
        for _, dataset in enumerate(result.datasets):
            print(f"  id: {dataset.id}")
            print(f"  author: {dataset.author}")
            print(f"  sha: {dataset.sha}")
            print(f"  created_at: {dataset.created_at}")
            print(f"  last_modified: {dataset.last_modified}")
            print(f"  private: {dataset.private}")
            print(f"  gated: {dataset.gated}")
            print(f"  disabled: {dataset.disabled}")
            print(f"  downloads: {dataset.downloads}")
            print(f"  likes: {dataset.likes}")
            print(f"  tags: {dataset.tags}")
            print(f"  pipeline_tag: {dataset.pipeline_tag}")
            print(f"  library_name: {dataset.library_name}")
            print("  siblings (First 5 files):")
            if dataset.siblings:
                for sibling in dataset.siblings[:5]:
                    print(f"    - {sibling.rfilename}")
            else:
                print("    (No files listed)")

            print("  card_data:")
            if dataset.card_data:
                for key, value in dataset.card_data.model_dump().items():
                    if value:
                        print(f"    - {key}: {value}")
            else:
                print("    (No card data available)")

            print(f"  model_index: {dataset.model_index}")

            print("  readme (Snippet):")
            if dataset.readme:
                snippet = dataset.readme.replace("\n", " ").strip()
                print(f'    "{snippet[:250]}..."')
            else:
                print("    (README not found or failed to load)")
            print("-" * 50)
    else:
        print("\nNo datasets found for the given queries.")


if __name__ == "__main__":
    asyncio.run(main())
