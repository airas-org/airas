from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.features.analysis.analytic_subgraph.prompt.analytic_node_prompt import (
    analytic_node_prompt,
)
from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    analysis_report: str


def analytic_node(
    llm_name: LLM_MODEL,
    new_method,
    client: LLMFacadeClient | None = None,
) -> str | None:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(analytic_node_prompt)

    # Extract data from new_method object with null checks
    method_text = new_method.method if hasattr(new_method, "method") else ""
    experiment_strategy = (
        new_method.experimental_design.experiment_strategy
        if new_method.experimental_design
        else ""
    )
    experiment_code = (
        new_method.experimental_design.experiment_code
        if new_method.experimental_design
        else ""
    )
    output_text_data = (
        new_method.experimental_results.result
        if new_method.experimental_results
        else ""
    )

    data = {
        "new_method": method_text,
        "experiment_strategy": experiment_strategy,
        "experiment_code": experiment_code,
        "output_text_data": output_text_data,
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(message=messages, data_model=LLMOutput)
    if output is None:
        raise ValueError("No response from LLM in analytic_node.")
    return output["analysis_report"]
