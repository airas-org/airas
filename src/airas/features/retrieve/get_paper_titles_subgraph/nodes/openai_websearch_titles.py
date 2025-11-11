import logging
from typing import Annotated

from jinja2 import Environment
from pydantic import Field

from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
)

logger = logging.getLogger(__name__)

_EXCLUDE_KEYWORDS = ("survey", "review", "overview", "systematic review")


def _is_excluded_title(title: str) -> bool:
    """Check if title contains excluded keywords."""
    lowered = title.lower()
    return any(word in lowered for word in _EXCLUDE_KEYWORDS)


async def openai_websearch_titles(
    llm_name: OPENAI_MODEL,
    openai_client: OpenAIClient,
    prompt_template: str,
    queries: list[str],
    max_results: Annotated[int, Field(gt=0)] = 5,
    # sleep_sec: float = 60.0,
    conference_preference: str | None = None,
) -> list[str] | None:
    llm_client = openai_client(reasoning_effort="high")

    env = Environment()
    template = env.from_string(prompt_template)
    collected: set[str] = set()

    for _i, query in enumerate(queries):
        logger.info(f"Searching papers with OpenAI web search for query: '{query}'")

        data = {
            "query": query,
            "max_results": max_results,
            "conference_preference": conference_preference,
        }
        prompt = template.render(data)

        try:
            output, cost = await llm_client.web_search(
                message=prompt, llm_name=llm_name
            )
        except Exception as exc:
            logger.warning(f"OpenAI web search failed for '{query}': {exc}")
            continue

        if not output or not isinstance(output, dict):
            logger.warning(f"No response for query: '{query}'")
            continue

        titles = output.get("titles", [])
        for title in titles:
            title = title.strip()
            if title and not _is_excluded_title(title):
                collected.add(title)
                if len(collected) >= max_results:
                    return sorted(collected)

        # if i < len(queries) - 1:
        #     logger.info(f"Waiting {sleep_sec} seconds before next query...")
        #     sleep(sleep_sec)

    if not collected:
        logger.warning("No paper titles obtained from OpenAI web search")
        return None

    return sorted(collected)


if __name__ == "__main__":
    from airas.features.retrieve.get_paper_titles_subgraph.prompt.openai_websearch_titles_prompt import (
        openai_websearch_titles_prompt,
    )

    results = openai_websearch_titles(
        llm_name="gpt-4o-2024-11-20",
        prompt_template=openai_websearch_titles_prompt,
        queries=["vision transformer image recognition"],
        max_results=10,
    )
    print(f"results: {results}")
