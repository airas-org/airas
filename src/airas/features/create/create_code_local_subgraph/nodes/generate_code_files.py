import json
import logging
from typing import Dict

from jinja2 import Environment
from pydantic import BaseModel

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

logger = logging.getLogger(__name__)


class GeneratedFiles(BaseModel):
    files: Dict[str, str]


def generate_code_files(
    llm_name: LLM_MODEL,
    new_method: str,
    experiment_code: str,
    experiment_iteration: int,
    prompt_template: str,
    client: LLMFacadeClient | None = None,
) -> Dict[str, str]:
    """Generate code files using LLM based on new method and experiment code"""

    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    # Prepare template data
    data = {
        "new_method": new_method,
        "experiment_code": experiment_code,
        "experiment_iteration": experiment_iteration,
    }

    # Render prompt template
    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    logger.info("Generating code files using LLM...")

    try:
        # Use regular generate method instead of structured_outputs for JSON parsing
        response, cost = client.generate(message=messages)

        # Try to extract JSON from the response
        # Look for JSON block in the response
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1

        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON found in LLM response")

        json_str = response[start_idx:end_idx]
        files_dict = json.loads(json_str)

        logger.info(f"Successfully generated {len(files_dict)} files")
        return files_dict

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        logger.error(f"Response: {response}")
        raise ValueError(f"Failed to parse JSON from LLM response: {e}") from e
    except Exception as e:
        logger.error(f"Error generating code files: {e}")
        raise ValueError(f"Error generating code files: {e}") from e


if __name__ == "__main__":
    # Test the function
    from airas.features.create.create_code_local_subgraph.prompt.code_generation_prompt import (
        code_generation_prompt,
    )

    llm_name = "gpt-4o-mini-2024-07-18"
    new_method = "Test method"
    experiment_code = "print('Hello, world!')"
    experiment_iteration = 1

    result = generate_code_files(
        llm_name=llm_name,
        new_method=new_method,
        experiment_code=experiment_code,
        experiment_iteration=experiment_iteration,
        prompt_template=code_generation_prompt,
    )
    print(json.dumps(result, indent=2))
