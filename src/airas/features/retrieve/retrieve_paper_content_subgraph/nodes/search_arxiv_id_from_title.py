import logging

from jinja2 import Environment

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

logger = logging.getLogger(__name__)


def search_arxiv_id_from_title(
    llm_name: LLM_MODEL,
    prompt_template: str,
    title: str,
    conference_preference: str | None = None,
    client: LLMFacadeClient | None = None,
) -> str | None:
    client = client or LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)

    logger.info(f"OpenAI web search for title: '{title}'")
    data = {
        "title": title,
        "conference_preference": conference_preference,
    }
    prompt = template.render(data)

    try:
        output, cost = client.web_search(message=prompt)
    except Exception as e:
        logger.warning(f"OpenAI web search failed for '{title}': {e}")
        return None

    if not output:
        logger.warning(f"No web search response for title: '{title}'")
        return None

    arxiv_id = output["arxiv_id"].strip()
    logger.info(f"Extracted arXiv ID: '{arxiv_id}'")

    if not arxiv_id:
        logger.warning(f"Empty arXiv ID for title: '{title}'")
        return None

    return arxiv_id


if __name__ == "__main__":
    from airas.features.retrieve.retrieve_paper_content_subgraph.prompt.openai_websearch_arxiv_ids_prompt import (
        openai_websearch_arxiv_ids_prompt,
    )

    # test_title = "Attention Is All You Need"
    title = "TSDiT: Traffic Scene Diffusion Models With Transformers"

    result = search_arxiv_id_from_title(
        llm_name="gpt-4o-2024-11-20",
        prompt_template=openai_websearch_arxiv_ids_prompt,
        title=title,
    )
    if result:
        print(f"arXiv ID: {result}")
    else:
        print("No arXiv ID found")
