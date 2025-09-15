import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.nodes.plan_architecture_design import (
    ArchitectureDesign,
)
from airas.features.create.create_code_subgraph.prompt.plan_logic_design_prompt import (
    plan_logic_design_prompt,
)
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
)
from airas.types.research_hypothesis import ResearchHypothesis

logger = logging.getLogger(__name__)


class LogicTask(BaseModel):
    name: str
    description: str
    dependencies: str


class LogicDesign(BaseModel):
    logic_task: list[LogicTask]
    generation_order: str


def plan_logic_design(
    llm_name: OPENAI_MODEL,
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    architecture_design: ArchitectureDesign,
    prompt_template: str = plan_logic_design_prompt,
    client: OpenAIClient | None = None,
) -> LogicDesign:
    client = OpenAIClient(reasoning_effort="high")

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(
        {
            "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
            "new_method": new_method.model_dump(),
            "architecture_design": architecture_design.model_dump(),
        }
    )

    logger.info("Generating logic design and task breakdown using LLM...")

    output, cost = client.structured_outputs(
        model_name=llm_name, message=messages, data_model=LogicDesign
    )
    if output is None:
        raise ValueError("Error: No response from LLM in plan_logic_design.")

    logic_design = LogicDesign(**output)

    logger.info(f"Generated {len(logic_design.logic_task)} tasks in breakdown")

    return logic_design
