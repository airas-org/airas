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
    max_results_per_search: int = 20,  # TODO: Add logic to rescan if no resources meeting the conditions are found.
    hf_client: HuggingFaceClient | None = None,
    include_gated: bool = False,
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
        _search_resources(
            hf_client, search_type, query, max_results_per_search, include_gated
        )
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
    include_gated: bool = False,
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
                    hf_client, search_type, resource, include_gated
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
    include_gated: bool = False,
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

        # Filter out inaccessible resources based on include_gated setting
        if hf_resource.private or hf_resource.disabled:
            logger.info(
                f"Skipping inaccessible resource: {resource_id} (private={hf_resource.private}, disabled={hf_resource.disabled})"
            )
            return None

        if hf_resource.gated and not include_gated:
            logger.info(
                f"Skipping gated resource: {resource_id} (gated={hf_resource.gated}, include_gated={include_gated})"
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
