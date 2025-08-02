import base64
import logging
from typing import cast

from airas.services.api_client.github_client import GithubClient
from airas.types.latex import LATEX_TEMPLATE

logger = logging.getLogger(__name__)


def retrieve_latex_template(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    latex_template: LATEX_TEMPLATE,
) -> str:
    client = GithubClient()
    file_data = client.get_repository_content(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        file_path=f".research/latex/{latex_template}/template.tex",
    )

    file_data_dict = cast(dict, file_data)
    decoded_bytes = base64.b64decode(file_data_dict["content"])
    latex_content = decoded_bytes.decode("utf-8")
    return latex_content


if __name__ == "__main__":
    latex_template = retrieve_latex_template(
        github_owner="auto-res2",
        repository_name="tanaka-20250729-v3",
        branch_name="main",
        latex_template="iclr2024",
    )
    print(latex_template)
