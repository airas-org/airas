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
    new_method: str,
    verification_policy: str,
    experiment_code: str,
    output_text_data: str,
    client: LLMFacadeClient | None = None,
) -> str | None:
    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    env = Environment()
    template = env.from_string(analytic_node_prompt)
    data = {
        "new_method": new_method,
        "verification_policy": verification_policy,
        "experiment_code": experiment_code,
        "output_text_data": output_text_data,
    }
    messages = template.render(data)
    output, cost = client.structured_outputs(message=messages, data_model=LLMOutput)
    if output is None:
        logger.error("Error: No response from LLM.")
        return None
    else:
        analysis_report = output.get("analysis_report")
        return analysis_report
