from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL, LLMFacadeClient

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    paper_titles: list[str]


def extract_paper_title(
    llm_name: LLM_MODEL,
    queries: list,
    scraped_results: list,
    prompt_template: str,
    client: LLMFacadeClient | None = None, 
) -> list[str]:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)

    aggregated_titles = []
    for result in scraped_results:
        data = {"queries": queries, "result": result}
        messages = template.render(data)

        output, cost = client.structured_outputs(message=messages, data_model=LLMOutput)
        if output is None:
            logger.warning("Error: No response from LLM in extract_paper_title_node.")
            continue
        else:
            if "paper_titles" in output:
                titles_list = output["paper_titles"]
                aggregated_titles.extend(titles_list)
    return aggregated_titles
