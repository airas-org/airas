from typing import Literal

from typing_extensions import TypedDict


class FixCodeLocalSubgraphInputState(TypedDict):
    github_repository: str
    branch_name: str
    output_text_data: str
    error_text_data: str
    executed_flag: Literal[
        True
    ]  # This should be True if the GitHub Actions workflow was executed successfully
