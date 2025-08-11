from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.paper import PaperContent

logger = getLogger(__name__)


class PaperReviewOutput(BaseModel):
    novelty_score: int
    significance_score: int
    reproducibility_score: int
    experimental_quality_score: int


def review_paper(
    llm_name: LLM_MODEL,
    prompt_template: str,
    paper_content: PaperContent,
    client: LLMFacadeClient | None = None,
) -> dict[str, int]:
    client = client or LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)

    # Dynamically extract all fields from PaperContent and make them available for template
    paper_data = paper_content.model_dump()
    data = {"paper_content": paper_data}

    messages = template.render(data)
    output, _cost = client.structured_outputs(
        message=messages, data_model=PaperReviewOutput
    )

    if output is None:
        raise ValueError("No response from LLM in paper_review_node.")

    return {
        "novelty_score": output["novelty_score"],
        "significance_score": output["significance_score"],
        "reproducibility_score": output["reproducibility_score"],
        "experimental_quality_score": output["experimental_quality_score"],
    }
