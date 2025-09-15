import logging

from jinja2 import Environment
from pydantic import BaseModel

from airas.config.runner_type_info import RunnerType, runner_info_dict
from airas.features.create.create_code_subgraph.nodes.plan_architecture_design import (
    ArchitectureDesign,
)
from airas.features.create.create_code_subgraph.nodes.plan_logic_design import (
    LogicDesign,
)
from airas.features.create.create_code_subgraph.prompt.plan_file_details_prompt import (
    plan_file_details_prompt,
)
from airas.services.api_client.llm_client.openai_client import (
    OPENAI_MODEL,
    OpenAIClient,
)
from airas.types.research_hypothesis import ResearchHypothesis

logger = logging.getLogger(__name__)


class FileImplementationDetail(BaseModel):
    file_path: str
    purpose: str
    core_logic: str
    key_functions_and_classes: str
    inputs: str
    outputs: str
    implementation_notes: str


class FileDetails(BaseModel):
    file_implementations: list[FileImplementationDetail]
    shared_utilities: str
    configuration_requirements: str


def plan_file_details(
    llm_name: OPENAI_MODEL,
    new_method: ResearchHypothesis,
    runner_type: RunnerType,
    architecture_design: ArchitectureDesign,
    logic_design: LogicDesign,
    prompt_template: str = plan_file_details_prompt,
    client: OpenAIClient | None = None,
) -> FileDetails:
    client = OpenAIClient(reasoning_effort="high")

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(
        {
            "runner_type_prompt": runner_info_dict[runner_type]["prompt"],
            "new_method": new_method.model_dump(),
            "architecture_design": architecture_design.model_dump(),
            "logic_design": logic_design.model_dump(),
        }
    )

    logger.info("Generating detailed file implementation specifications using LLM...")

    output, cost = client.structured_outputs(
        model_name=llm_name, message=messages, data_model=FileDetails
    )
    if output is None:
        raise ValueError("Error: No response from LLM in plan_file_details.")

    file_details = FileDetails(**output)

    logger.info(
        f"Generated detailed specifications for {len(file_details.file_implementations)} files"
    )

    return file_details
