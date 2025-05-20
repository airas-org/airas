from logging import getLogger

from jinja2 import Environment
from pydantic import BaseModel

from airas.utils.api_client.llm_facade_client import LLM_MODEL, LLMFacadeClient

logger = getLogger(__name__)


class PaperContent(BaseModel):
    Title: str
    Abstract: str
    Introduction: str
    Related_Work: str
    Background: str
    Method: str
    Experimental_Setup: str
    Results: str
    Conclusions: str


def _replace_underscores_in_keys(paper_dict: dict[str, str]) -> dict[str, str]:
    return {key.replace("_", " "): value for key, value in paper_dict.items()}


def convert_to_latex(
    llm_name: LLM_MODEL,
    paper_content: dict[str, str],
    prompt_template: str,
    figure_relative_path: str = "../images",  
) -> dict[str, str]:
    client = LLMFacadeClient(llm_name)

    data = {
        "figure_relative_path": figure_relative_path,
        "sections": [
            {"name": section, "content": paper_content[section]}
            for section in paper_content.keys()
        ]
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    output, cost = client.structured_outputs(
        message=messages,
        data_model=PaperContent,
    )
    if output is None:
        raise ValueError("Error: No response from the model in convert_to_latex.")

    missing_fields = [
        field
        for field in PaperContent.model_fields
        if field not in output or not output[field].strip()
    ]
    if missing_fields:
        raise ValueError(f"Missing or empty fields in model response: {missing_fields}")

    return _replace_underscores_in_keys(output)


