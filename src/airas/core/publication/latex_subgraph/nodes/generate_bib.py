from logging import getLogger
from typing import Any

from jinja2 import Environment
from pydantic import BaseModel, create_model

from airas.services.api_client.llm_client.llm_facade_client import LLM_MODEL, LLMFacadeClient

logger = getLogger(__name__)



def _build_bib_entry_model(n: int) -> type[BaseModel]:
    fields = {f"bib_entry_{i+1}": (str, ...) for i in range(n)}
    return create_model("LLMOutput", **fields)

def generate_bib(
    llm_name: LLM_MODEL,
    prompt_template: str,
    references: dict[str, dict[str, Any]], 
    client: LLMFacadeClient | None = None, 
) -> dict[str, str]:
    client = client or LLMFacadeClient(llm_name)

    data = {
        "refs": [
            {"placeholder": k, "reference": v}
            for k, v in references.items()
        ]
    }

    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    DynamicLLMOutput = _build_bib_entry_model(len(references))
    output, cost = client.structured_outputs(
        message=messages,
        data_model=DynamicLLMOutput,
    )
    if output is None:
        raise ValueError("Error: No response from the model in convert_to_latex.")
    
    references_bib = {
        key: output[f"bib_entry_{i+1}"]
        for i, key in enumerate(references)
    }
    return references_bib
