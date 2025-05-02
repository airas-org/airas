from jinja2 import Environment
from pydantic import BaseModel
from airas.utils.api_client.llm_facade_client import LLMFacadeClient, LLM_MODEL
from airas.retrieve.retrieve_paper_subgraph.prompt.extract_paper_title_node_prompt import (
    extract_paper_title_node_prompt,
)
from logging import getLogger

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    paper_titles: list[str]


def extract_paper_title_node(
    llm_name: LLM_MODEL,
    queries: list,
    scraped_results: list,
) -> list[str]:
    env = Environment()
    template = env.from_string(extract_paper_title_node_prompt)

    aggregated_titles = []
    for result in scraped_results:
        data = {"queries": queries, "result": result}
        messages = template.render(data)

        output, cost = LLMFacadeClient(llm_name=llm_name).structured_outputs(
            message=messages, data_model=LLMOutput
        )
        if output is None:
            logger.warning("Error: No response from LLM in extract_paper_title_node.")
            continue
        else:
            if "paper_titles" in output:
                titles_list = output["paper_titles"]
                aggregated_titles.extend(titles_list)
    return aggregated_titles


if __name__ == "__main__":
    llm_name = "gemini-2.0-flash-001"
    queries = ["deep leanning"]
    scraped_results = [
        "# ICLR 2024 - Deep Learning Advances\n\nThis paper discusses recent advances in deep learning architectures and training techniques...",
        "# ICLR 2024 - Neural Networks for Vision\n\nIn this study, novel convolutional neural network designs are introduced to improve image recognition...",
    ]
    extracted_paper_titles = extract_paper_title_node(
        llm_name=llm_name, queries=queries, scraped_results=scraped_results
    )
    print(f"Extracted paper titles: {extracted_paper_titles}")
