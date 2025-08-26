from logging import getLogger

from jinja2 import Environment

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)
from airas.types.paper import PaperContent
from airas.types.research_hypothesis import ExperimentalResults, ResearchHypothesis

logger = getLogger(__name__)


def check_experimental_results(
    llm_name: LLM_MODEL,
    prompt_template: str,
    paper_content: PaperContent,
    new_method: ResearchHypothesis,
    client: LLMFacadeClient | None = None,
) -> ResearchHypothesis:
    client = client or LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(prompt_template)

    paper_data = paper_content.model_dump()
    data = {"paper_content": paper_data}

    messages = template.render(data)
    llm_output, _cost = client.structured_outputs(
        message=messages, data_model=ExperimentalResults
    )

    if llm_output is None:
        raise ValueError("No response from LLM in check_experimental_results node.")

    if new_method.experimental_results is None:
        new_method.experimental_results = ExperimentalResults()

    new_method.experimental_results.was_experiment_executed = llm_output[
        "was_experiment_executed"
    ]
    new_method.experimental_results.is_better_than_baseline = llm_output[
        "is_better_than_baseline"
    ]

    return new_method
