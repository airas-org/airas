from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    selected_arxiv_id: str


def select_best_paper(
    llm_name: LLM_MODEL,
    prompt_template: str,
    candidate_papers,
    selected_base_paper_info=None,
    add_paper_num: int = 3,
    client: LLMFacadeClient | None = None,
) -> list[str]:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)
    if selected_base_paper_info is None:
        data = {
            "candidate_papers": candidate_papers,
            "add_paper_num": add_paper_num,
        }
    else:
        data = {
            "candidate_papers": candidate_papers,
            "selected_base_paper": selected_base_paper_info,
            "add_paper_num": add_paper_num,
        }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)
    output, cost = client.structured_outputs(message=messages, data_model=LLMOutput)

    if "selected_arxiv_id" in output:
        arxiv_id_str = output["selected_arxiv_id"]
        arxiv_id_list = [
            arxiv_id.strip()
            for arxiv_id in arxiv_id_str.split("\n")
            if arxiv_id.strip()
        ]
        return arxiv_id_list
    else:
        logger.warning("No 'selected_arxiv_id' found in the response.")
        return []
