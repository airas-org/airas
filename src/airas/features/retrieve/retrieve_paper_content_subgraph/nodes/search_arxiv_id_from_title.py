import logging

from jinja2 import Environment

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.research_study import MetaData, ResearchStudy

logger = logging.getLogger(__name__)


def search_arxiv_id_from_title(
    llm_name: LLM_MODEL,
    prompt_template: str,
    research_study_list: list[ResearchStudy],
    conference_preference: str | None = None,
    client: LLMFacadeClient | None = None,
) -> list[ResearchStudy]:
    client = client or LLMFacadeClient(llm_name=llm_name)
    template = Environment().from_string(prompt_template)

    for idx, research_study in enumerate(research_study_list):
        logger.info(
            "Processing research study %d/%d", idx + 1, len(research_study_list)
        )
        prompt = template.render(
            {
                "title": research_study.title,
                "conference_preference": conference_preference,
            }
        )
        try:
            output, _ = client.web_search(message=prompt)
        except Exception as e:
            logger.error(
                f"Web search failed for '{research_study.title}': {e}. Skipping to the next."
            )
            continue

        if not output:
            logger.warning(
                f"No output received for '{research_study.title}'. Skipping."
            )
            continue

        arxiv_id = output.get("arxiv_id", "").strip()
        if not arxiv_id:
            logger.warning(f"No arXiv ID found for '{research_study.title}'.")
            continue

        if not research_study.meta_data:
            research_study.meta_data = MetaData()
        research_study.meta_data.arxiv_id = arxiv_id
        logger.info(f"Found arXiv ID for '{research_study.title}': {arxiv_id}")

    return research_study_list


if __name__ == "__main__":
    from airas.features.retrieve.retrieve_paper_content_subgraph.prompt.openai_websearch_arxiv_ids_prompt import (
        openai_websearch_arxiv_ids_prompt,
    )

    research_study = ResearchStudy(title="Attention Is All You Need")

    result = search_arxiv_id_from_title(
        llm_name="gpt-4o-2024-11-20",
        prompt_template=openai_websearch_arxiv_ids_prompt,
        research_study_list=[research_study],
    )

    if result and result[0].meta_data and result[0].meta_data.arxiv_id:
        print(f"arXiv ID found: {result[0].meta_data.arxiv_id}")
    else:
        print("No arXiv ID found")
