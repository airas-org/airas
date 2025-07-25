import logging
from difflib import SequenceMatcher
from typing import Any

from airas.types.paper_provider_schema import PaperProviderSchema

logger = logging.getLogger(__name__)


def _normalize_title(title: str) -> str:
    """Normalize title for comparison by removing punctuation and converting to lowercase."""
    if not title:
        return ""

    # Convert to lowercase and remove common punctuation
    normalized = title.lower()

    # Remove common punctuation and extra spaces
    chars_to_remove = ".,!?;:()[]{}\"'-"
    for char in chars_to_remove:
        normalized = normalized.replace(char, " ")

    # Replace multiple spaces with single space and strip
    normalized = " ".join(normalized.split())

    return normalized


def _calculate_similarity(title1: str, title2: str) -> float:
    """Calculate similarity ratio between two titles using SequenceMatcher."""
    if not title1 or not title2:
        return 0.0

    norm1 = _normalize_title(title1)
    norm2 = _normalize_title(title2)

    if not norm1 or not norm2:
        return 0.0

    return SequenceMatcher(None, norm1, norm2).ratio()


def verify_title_match(
    original_title: str,
    paper_info: dict[str, Any] | PaperProviderSchema,
    similarity_threshold: float = 0.8,
) -> bool:
    """
    Verify if the retrieved paper information matches the original title.

    Args:
        original_title: The original paper title to match against
        paper_info: Retrieved paper information (dict or PaperProviderSchema)
        similarity_threshold: Minimum similarity ratio to consider a match (0.0-1.0)

    Returns:
        True if the titles match above the threshold, False otherwise
    """
    if not original_title or not paper_info:
        logger.warning("Missing original title or paper info for verification")
        return False

    # Extract title from paper_info
    if isinstance(paper_info, dict):
        retrieved_title = paper_info.get("title", "")
    elif isinstance(paper_info, PaperProviderSchema):
        retrieved_title = paper_info.title
    else:
        logger.warning(f"Unsupported paper_info type: {type(paper_info)}")
        return False

    if not retrieved_title:
        logger.warning("No title found in retrieved paper info")
        return False

    # Calculate similarity
    similarity = _calculate_similarity(original_title, retrieved_title)

    logger.info(f"Title similarity: {similarity:.3f}")
    logger.info(f"Original: '{original_title}'")
    logger.info(f"Retrieved: '{retrieved_title}'")

    is_match = similarity >= similarity_threshold

    if is_match:
        logger.info("Title match verified successfully")
    else:
        logger.warning(
            f"Title match failed (similarity: {similarity:.3f} < {similarity_threshold})"
        )

    return is_match


if __name__ == "__main__":
    # Test the function
    original = "Attention Is All You Need"

    # Test case 1: Exact match
    paper1 = {"title": "Attention Is All You Need"}
    result1 = verify_title_match(original, paper1)
    print(f"Exact match: {result1}")

    # Test case 2: Similar match
    paper2 = {"title": "Attention is all you need"}
    result2 = verify_title_match(original, paper2)
    print(f"Case variation: {result2}")

    # Test case 3: Partial match
    paper3 = {
        "title": "Attention Is All You Need: Transformers for Machine Translation"
    }
    result3 = verify_title_match(original, paper3)
    print(f"Extended title: {result3}")

    # Test case 4: No match
    paper4 = {"title": "BERT: Pre-training of Deep Bidirectional Transformers"}
    result4 = verify_title_match(original, paper4)
    print(f"Different paper: {result4}")
