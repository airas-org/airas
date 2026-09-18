"""Analysis of the finished runs against the preregistered claims."""

from typing import Any

from airas.core.llm_config import NodeLLMConfig
from airas.mcp.app import mcp
from airas.mcp.context import _litellm_client
from airas.usecases.analysis.analyze_experiment import (
    analyze_experiment as analyze_experiment_usecase,
)


@mcp.tool()
async def analyze_experiment(local_path: str, model: str) -> dict[str, Any]:
    """Draft the analysis of a study from its record and run outputs.

    Reads `.research/record.json` and `.research/results/` in the clone at
    `local_path`: every live hypothesis and claim with its frozen criterion
    and predicted interval, the observed difference, and the verdict the
    criterion derives. `model` (required; see `get_available_llms`) reads
    them and returns `analysis` — per claim, then the hypothesis, then
    limitations and open questions — plus each claim's verdict and observed
    difference. Nothing is written: the analysis is a draft for the
    Discussion, to be checked against the numbers like any other prose.
    Without an LLM key, `get_generation_prompt(step="experiment_analysis",
    inputs={"local_path": ...})` renders the same prompt for you to answer.
    """
    return await analyze_experiment_usecase(
        local_path,
        litellm_client=_litellm_client(),
        llm_config=NodeLLMConfig(llm_name=model),
    )
