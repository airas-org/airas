import json
import logging
import re
from time import sleep

from jinja2 import Environment
from openai import OpenAI

logger = logging.getLogger(__name__)

_EXCLUDE_KEYWORDS = ("survey", "review", "overview", "systematic review")


def _is_excluded_title(title: str) -> bool:
    """Check if title contains excluded keywords."""
    lowered = title.lower()
    return any(word in lowered for word in _EXCLUDE_KEYWORDS)


def _extract_json(text: str) -> dict:
    """
    Extract JSON object from text, handling code fences if present.
    """
    text = text.strip()

    # Remove code fences if present
    if text.startswith("```"):
        fenced = text.splitlines()
        if fenced[0].startswith("```"):
            fenced = fenced[1:]
        if fenced and fenced[-1].startswith("```"):
            fenced = fenced[:-1]
        text = "\n".join(fenced).strip()

    return json.loads(text)


# Default prompt template (should match openai_websearch_titles_prompt.py)
_DEFAULT_PROMPT_TEMPLATE = """\
You are a research assistant.
Task: Find recent academic papers related to: {{ query }}
{% if conference_preference -%}
Focus on papers from these conferences/venues: {{ conference_preference }}
{%- endif %}
Return **exactly {{ max_results }}** paper titles in JSON format.

Required output — **only** this JSON, nothing else:
{
  "titles": [
    "Paper title 1",
    "Paper title 2",
    "Paper title 3"
  ]
}
"""


def openai_websearch_titles(
    queries: list[str],
    *,
    max_results: int = 5,
    sleep_sec: float = 60.0,
    prompt_template: str | None = None,
    conference_preference: str | None = None,
    client: OpenAI | None = None,
) -> list[str] | None:
    """
    Search for paper titles using OpenAI API web search.
    
    Args:
        queries: List of search queries
        max_results: Maximum number of results to return
        sleep_sec: Sleep time between queries (default 60 seconds)
        prompt_template: Custom prompt template (uses default if None)
        conference_preference: Preferred conferences/venues (e.g., "NeurIPS, ICML, ICLR")
        client: OpenAI client instance
        
    Returns:
        List of paper titles or None if no results found
    """
    if client is None:
        client = OpenAI()
    
    # Use default prompt template if none provided
    if prompt_template is None:
        prompt_template = _DEFAULT_PROMPT_TEMPLATE
    
    # Initialize Jinja2 environment
    env = Environment()
    template = env.from_string(prompt_template)

    collected: set[str] = set()

    for i, query in enumerate(queries):
        logger.info(f"Searching papers with OpenAI web search for query: '{query}'")
        
        # Create prompt using template
        prompt = template.render(
            query=query,
            max_results=max_results,
            conference_preference=conference_preference
        )
        
        try:
            response = client.responses.create(
                model="gpt-4o",
                tools=[{"type": "web_search_preview"}],
                input=prompt
            )
            
            # Extract assistant messages
            assistant_msgs = [
                o for o in response.output
                if getattr(o, "type", None) == "message" 
                and getattr(o, "role", None) == "assistant"
            ]
            
            if not assistant_msgs:
                logger.warning(f"No assistant response for query: '{query}'")
                continue
                
            json_text = assistant_msgs[-1].content[0].text
            titles_data = _extract_json(json_text)
            
            titles = titles_data.get("titles", [])
            if not titles:
                logger.warning(f"No titles found for query: '{query}'")
                continue
                
            # Filter out excluded titles and add to collection
            for title in titles:
                title = title.strip()
                if title and not _is_excluded_title(title):
                    collected.add(title)
                    if len(collected) >= max_results:
                        return sorted(collected)
                        
        except Exception as exc:
            logger.warning(f"OpenAI web search failed for '{query}': {exc}")
            continue
        
        # Sleep between queries (except for the last query)
        if i < len(queries) - 1:
            logger.info(f"Waiting {sleep_sec} seconds before next query...")
            sleep(sleep_sec)

    if not collected:
        logger.warning("No paper titles obtained from OpenAI web search")
        return None
    
    return sorted(collected)


if __name__ == "__main__":
    # Test the function
    results = openai_websearch_titles(
        queries=["vision transformer image recognition"],
        max_results=5,
    )
    if results:
        for title in results:
            print(f"- {title}")
    else:
        print("No results found")
