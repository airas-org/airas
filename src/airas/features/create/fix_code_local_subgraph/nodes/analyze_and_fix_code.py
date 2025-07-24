import json
import logging
from typing import Dict

from jinja2 import Environment

from airas.services.api_client.llm_client.llm_facade_client import (
    LLM_MODEL,
    LLMFacadeClient,
)

logger = logging.getLogger(__name__)


def analyze_and_fix_code(
    llm_name: LLM_MODEL,
    output_text_data: str,
    error_text_data: str,
    current_files: Dict[str, str],
    prompt_template: str,
    client: LLMFacadeClient | None = None,
) -> Dict[str, str]:
    """Analyze errors and generate fixed code using LLM"""

    if client is None:
        client = LLMFacadeClient(llm_name=llm_name)

    # Prepare template data
    data = {
        "output_text_data": output_text_data,
        "error_text_data": error_text_data,
        "current_files": current_files,
    }

    # Render prompt template
    env = Environment()
    template = env.from_string(prompt_template)
    messages = template.render(data)

    logger.info("Analyzing errors and generating fixed code using LLM...")

    try:
        # Use regular generate method for JSON parsing
        response, cost = client.generate(message=messages)

        # Try to extract JSON from the response
        # Look for JSON block in the response
        start_idx = response.find("{")
        end_idx = response.rfind("}") + 1

        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON found in LLM response")

        json_str = response[start_idx:end_idx]
        fixed_files = json.loads(json_str)

        logger.info(f"Successfully generated fixes for {len(fixed_files)} files")
        return fixed_files

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from LLM response: {e}")
        logger.error(f"Response: {response}")
        raise ValueError(f"Failed to parse JSON from LLM response: {e}") from e
    except Exception as e:
        logger.error(f"Error analyzing and fixing code: {e}")
        raise ValueError(f"Error analyzing and fixing code: {e}") from e


def should_fix_code(output_text_data: str, error_text_data: str) -> bool:
    """Determine if code needs fixing based on error data"""

    # If there are clear error indicators, we should fix
    error_indicators = [
        "Error:",
        "Exception:",
        "Traceback",
        "ImportError",
        "ModuleNotFoundError",
        "SyntaxError",
        "NameError",
        "AttributeError",
        "TypeError",
        "ValueError",
        "FileNotFoundError",
    ]

    # Check if error_text_data contains actual errors
    if error_text_data and error_text_data.strip():
        for indicator in error_indicators:
            if indicator in error_text_data:
                return True

    # If both output and error are empty, something went wrong
    if not output_text_data.strip() and not error_text_data.strip():
        return True

    # If output contains error messages
    if output_text_data:
        for indicator in error_indicators:
            if indicator in output_text_data:
                return True

    # Otherwise, assume it's working
    return False


if __name__ == "__main__":
    # Test the function
    from airas.features.create.fix_code_local_subgraph.prompt.code_fix_prompt import (
        code_fix_prompt,
    )

    llm_name = "gpt-4o-mini-2024-07-18"
    output_text_data = "Process started..."
    error_text_data = "ImportError: No module named 'numpy'"
    current_files = {
        "src/main.py": "import numpy as np\nprint('Hello')",
        "requirements.txt": "pandas==1.3.0",
    }

    # Test should_fix_code
    should_fix = should_fix_code(output_text_data, error_text_data)
    print(f"Should fix code: {should_fix}")

    if should_fix:
        result = analyze_and_fix_code(
            llm_name=llm_name,
            output_text_data=output_text_data,
            error_text_data=error_text_data,
            current_files=current_files,
            prompt_template=code_fix_prompt,
        )
        print(json.dumps(result, indent=2))
