import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.prompt.plan_architecture_design_prompt import (
    plan_architecture_design_prompt,
)
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
)
from airas.types.research_hypothesis import ResearchHypothesis

logger = logging.getLogger(__name__)


class ArchitectureComponent(BaseModel):
    name: str
    purpose: str
    responsibilities: str
    interfaces: str
    internal_dependencies: str


class ArchitectureDesign(BaseModel):
    core_components: list[ArchitectureComponent]
    data_flow_design: str
    external_dependencies: str


def plan_architecture_design(
    llm_name: OPENAI_MODEL,
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    prompt_template: str = plan_architecture_design_prompt,
    client: OpenAIClient | None = None,
) -> ArchitectureDesign:
    client = OpenAIClient(reasoning_effort="high")

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(
        {
            "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
            "new_method": new_method.model_dump(),
        }
    )

    logger.info("Generating architecture design for research method using LLM...")

    output, cost = client.structured_outputs(
        model_name=llm_name, message=messages, data_model=ArchitectureDesign
    )
    if output is None:
        raise ValueError("Error: No response from LLM in plan_architecture_design.")

    architecture_design = ArchitectureDesign(**output)

    logger.info(
        f"Generated architecture with {len(architecture_design.core_components)} components"
    )

    return architecture_design
