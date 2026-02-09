import argparse
import asyncio
import sys
import uuid
from logging import getLogger
from pathlib import Path
from typing import Any, cast

import httpx

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from airas.core.papers_db_config import (
    AIRAS_PAPERS_REPO_BASE_URL,
    CONFERENCES_AND_YEARS,
)
from airas.infra.litellm_client import LiteLLMClient
from airas.infra.qdrant_client import QdrantClient
from airas.infra.retry_policy import HTTPClientFatalError

logger = getLogger(__name__)

# Embedding model configuration
# https://ai.google.dev/gemini-api/docs/embeddings?hl=ja
EMBEDDING_MODEL = "gemini/gemini-embedding-001"
VECTOR_SIZE = 3072  # Dimension for gemini-embedding-001

# Concurrent request limit to avoid overwhelming the server
MAX_CONCURRENT_REQUESTS = 10


def _generate_paper_id(paper: dict[str, Any]) -> str:
    title = paper.get("title", "").strip()
    conference = paper.get("conference", "").strip()
    year = paper.get("year", "").strip()

    unique_string = f"{title}|{conference}|{year}"

    namespace = uuid.NAMESPACE_DNS
    paper_uuid = uuid.uuid5(namespace, unique_string)

    return str(paper_uuid)


async def _fetch_papers_from_url(
    client: httpx.AsyncClient,
    url: str,
    conference: str,
    year: str,
) -> list[dict[str, Any]]:
    try:
        logger.info(f"Fetching data from {url}...")
        response = await client.get(url, timeout=60)
        response.raise_for_status()
        papers = response.json()

        # Add metadata to each paper
        for paper in papers:
            paper["conference"] = conference
            paper["year"] = year

        logger.info(f"  -> Successfully fetched {len(papers)} papers")
        return papers
    except httpx.HTTPStatusError as e:
        logger.error(f"  -> HTTP error fetching {url}: {e}")
        raise
    except ValueError as e:
        logger.error(f"  -> JSON parse error from {url}: {e}")
        raise


async def _fetch_all_papers() -> list[dict[str, Any]]:
    async with httpx.AsyncClient() as client:
        semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)

        async def _bounded_fetch(
            url: str,
            conference: str,
            year: str,
        ) -> list[dict[str, Any]]:
            async with semaphore:
                try:
                    return await _fetch_papers_from_url(client, url, conference, year)
                except Exception as exc:
                    logger.warning(f"  -> Skipping due to error for {url}: {exc}")
                    raise

        tasks = []
        for conference, years in CONFERENCES_AND_YEARS.items():
            for year in years:
                url = f"{AIRAS_PAPERS_REPO_BASE_URL}/{conference}/{year}.json"
                task = _bounded_fetch(url, conference, year)
                tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        all_papers: list[dict[str, Any]] = []
        for result in results:
            if isinstance(result, Exception):
                logger.warning(f"  -> Skipping due to error: {result}")
            else:
                papers = cast(list[dict[str, Any]], result)
                all_papers.extend(papers)

    logger.info(f"Total papers fetched: {len(all_papers)}")
    return all_papers


async def _create_qdrant_collection(
    qdrant_client: QdrantClient,
    collection_name: str,
) -> None:
    try:
        collection_info = await qdrant_client.aget_collection_info(collection_name)
        points_count = collection_info.get("result", {}).get("points_count", 0)
        existing_vector_size = (
            collection_info.get("result", {})
            .get("config", {})
            .get("params", {})
            .get("vectors", {})
            .get("size")
        )

        logger.error(f"Collection '{collection_name}' already exists")
        logger.error(f"  -> Existing points: {points_count}")
        logger.error(f"  -> Vector size: {existing_vector_size}")

        raise ValueError(
            f"Collection '{collection_name}' already exists with {points_count} points. "
            f"Please specify a different collection name using --collection-name option."
        )

    except HTTPClientFatalError as e:
        if e.status_code == 404:
            logger.info(f"Collection '{collection_name}' does not exist, creating...")
        else:
            logger.error(f"HTTP error while checking collection: {e}")
            raise

    except httpx.RequestError as e:
        logger.error(f"Network error while checking collection: {e}")
        raise

    except Exception as e:
        logger.error(f"Unexpected error while checking collection: {e}", exc_info=True)
        raise

    try:
        logger.info(
            f"Creating collection '{collection_name}' with vector size {VECTOR_SIZE}..."
        )
        response = await qdrant_client.acreate_collection(
            collection_name=collection_name,
            vector_size=VECTOR_SIZE,
            distance="Cosine",
        )
        logger.info(f"Collection created successfully: {response}")
    except Exception as e:
        logger.error(f"Failed to create collection: {e}", exc_info=True)
        raise


async def _upload_papers_to_qdrant(
    litellm_client: LiteLLMClient,
    qdrant_client: QdrantClient,
    collection_name: str,
    papers: list[dict[str, Any]],
    batch_size: int = 100,
    start_index: int = 0,
) -> None:
    total_papers = len(papers)
    logger.info(f"Starting upload of {total_papers} papers from index {start_index}")

    for i in range(start_index, total_papers, batch_size):
        batch_end = min(i + batch_size, total_papers)
        batch_papers = papers[i:batch_end]
        logger.info(
            f"Processing batch {i // batch_size + 1}: papers {i + 1}-{batch_end} of {total_papers}"
        )

        abstracts = [paper.get("abstract", "") for paper in batch_papers]

        valid_indices = [
            idx
            for idx, abstract in enumerate(abstracts)
            if abstract and not abstract.isspace()
        ]

        if not valid_indices:
            logger.warning(
                f"  -> No valid abstracts in batch {i // batch_size + 1}, skipping"
            )
            continue

        valid_abstracts = [abstracts[idx] for idx in valid_indices]

        try:
            logger.info(
                f"  -> Generating embeddings for {len(valid_abstracts)} papers..."
            )
            embeddings = await litellm_client.embedding(
                texts=valid_abstracts,
                model=EMBEDDING_MODEL,
            )

            data_points = []
            for local_idx, global_idx in enumerate(valid_indices):
                paper = batch_papers[global_idx]

                # Generate unique ID based on paper content
                paper_id = _generate_paper_id(paper)

                data_points.append(
                    {
                        "id": paper_id,
                        "vector": embeddings[local_idx],
                        "payload": {
                            "title": paper.get("title", ""),
                            "conference": paper.get("conference", ""),
                            "year": paper.get("year", ""),
                            "abstract": paper.get("abstract", ""),
                        },
                    }
                )

            logger.info(f"  -> Uploading {len(data_points)} points to Qdrant...")
            await qdrant_client.aupsert_points(
                collection_name=collection_name,
                data_sets=data_points,
            )

            logger.info(f"  -> Batch {i // batch_size + 1} completed successfully")

        except Exception as e:
            logger.error(
                f"  -> Error processing batch {i // batch_size + 1}: {e}", exc_info=True
            )
            logger.error(
                f"  -> Failed at index {i}. You can resume with --start-index {i}"
            )
            raise

    logger.info(
        f"Upload completed! Total papers uploaded: {total_papers - start_index}"
    )


async def main(
    collection_name: str = "airas_papers_db",
    batch_size: int = 100,
    start_index: int = 0,
) -> None:
    import logging

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("=" * 80)
    logger.info("AIRAS Papers to Qdrant Upload Script")
    logger.info("=" * 80)
    logger.info(f"Collection name: {collection_name}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Start index: {start_index}")
    logger.info(f"Embedding model: {EMBEDDING_MODEL}")
    logger.info("ID scheme: uuid5(title|conference|year)")
    logger.warning(
        "If the collection already contains points created with a different ID scheme, "
        "new uploads will not match existing IDs and may create duplicates."
    )
    logger.info("=" * 80)

    async with httpx.AsyncClient() as session:
        litellm_client = LiteLLMClient()
        qdrant_client = QdrantClient(async_session=session)

        await _create_qdrant_collection(qdrant_client, collection_name)

        logger.info("\nFetching papers from database...")
        papers = await _fetch_all_papers()

        if not papers:
            logger.error("No papers fetched. Exiting.")
            return

        logger.info("\nUploading papers to Qdrant...")
        await _upload_papers_to_qdrant(
            litellm_client=litellm_client,
            qdrant_client=qdrant_client,
            collection_name=collection_name,
            papers=papers,
            batch_size=batch_size,
            start_index=start_index,
        )

    logger.info("\n" + "=" * 80)
    logger.info("Process completed successfully!")
    logger.info("=" * 80)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Upload AIRAS papers to Qdrant vector database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create new collection and upload all papers
  uv run python scripts/upload_papers_to_qdrant.py

  # Upload to specific collection
  uv run python scripts/upload_papers_to_qdrant.py --collection-name my_papers

  # Upload with specific batch size
  uv run python scripts/upload_papers_to_qdrant.py --batch-size 50

  # Resume from specific index (if previous run failed)
  uv run python scripts/upload_papers_to_qdrant.py --start-index 1000
        """,
    )
    parser.add_argument(
        "--collection-name",
        type=str,
        default="airas_papers_db",
        help="Name of the Qdrant collection (default: airas_papers_db)",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of papers to process in each batch (default: 100)",
    )
    parser.add_argument(
        "--start-index",
        type=int,
        default=0,
        help="Index to start from, useful for resuming (default: 0)",
    )

    args = parser.parse_args()

    asyncio.run(
        main(
            collection_name=args.collection_name,
            batch_size=args.batch_size,
            start_index=args.start_index,
        )
    )
