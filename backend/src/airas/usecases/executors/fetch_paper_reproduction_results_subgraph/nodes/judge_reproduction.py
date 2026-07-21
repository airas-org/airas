import json
from logging import getLogger
from typing import Literal

from jinja2 import Environment
from pydantic import BaseModel

from airas.core.llm_config import NodeLLMConfig
from airas.infra.litellm_client import LiteLLMClient
from airas.usecases.executors.fetch_paper_reproduction_results_subgraph.prompts.validate_reproduction_prompt import (
    validate_reproduction_prompt,
)

logger = getLogger(__name__)


class LLMOutput(BaseModel):
    severity: Literal["ok", "warning", "critical"]
    reproduction_level: Literal["high", "partial", "low"]
    text: str


async def judge_reproduction(
    llm_config: NodeLLMConfig,
    litellm_client: LiteLLMClient,
    paper_text: str | None,
    result: dict,
    evidence: str,
) -> dict:
    template = Environment().from_string(validate_reproduction_prompt)
    message = template.render(
        {
            "paper_text": paper_text or "(paper text unavailable)",
            "result": json.dumps(result, ensure_ascii=False, indent=2),
            "evidence": evidence,
        }
    )
    output = await litellm_client.structured_output(
        message=message,
        data_model=LLMOutput,
        llm_name=llm_config.llm_name,
        params=llm_config.params,
    )
    if output is None:
        raise ValueError("No response from LLM in judge_reproduction.")
    return {
        "severity": output.severity,
        "reproduction_level": output.reproduction_level,
        "text": output.text,
    }
