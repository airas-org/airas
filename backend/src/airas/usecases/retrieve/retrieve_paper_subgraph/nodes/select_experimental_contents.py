"""Select experimental files from repository based on paper summary and code structure.

# Processing Flow:
# 1. Receive RepositoryCodeStructure (lightweight: file paths, class/function names, docstrings)
#    and RepositoryContents (full file contents)
#
# 2. Send RepositoryCodeStructure.to_prompt_string() + PaperSummary to LLM
#    - LLM sees only code structure (not full contents) to stay within context limits
#    - LLM returns list of file paths relevant to the paper's method
#
# 3. Use selected file paths as keys to retrieve full contents from RepositoryContents
#    - file_lookup = {f.path: f for f in contents.files}
#    - For each selected path, get full content: file_lookup[path].content
#
# 4. Categorize and return:
#    - .py files -> experimental_code
#    - .yaml, .json, .toml, .md, .txt files -> experimental_info

# Example:
# Input:
#   code_structure.to_prompt_string() = "## src/model.py\n  class Transformer\n  def forward..."
#   LLM output: ["src/model.py", "config/train.yaml"]
#
# Output:
#   experimental_code = "# File: src/model.py\nimport torch\nclass Transformer:..."
#   experimental_info = "# File: config/train.yaml\nmodel:\n  d_model: 512..."
"""

import asyncio
import logging
from typing import cast

from jinja2 import Environment
from pydantic import BaseModel, Field

from airas.core.llm_config import NodeLLMConfig
from airas.infra.langchain_client import LangChainClient
from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.extract_code_structure import (
    RepositoryCodeStructure,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.retrieve_repository_contents import (
    RepositoryContents,
)
from airas.usecases.retrieve.retrieve_paper_subgraph.nodes.summarize_paper import (
    PaperSummary,
)

logger = logging.getLogger(__name__)


class SelectedFiles(BaseModel):
    file_paths: list[str] = Field(
        description="List of file paths that are relevant to the method and experimental settings"
    )


def _build_selected_content(
    contents: RepositoryContents, selected_paths: list[str]
) -> tuple[str, str]:
    code_parts: list[str] = []
    info_parts: list[str] = []

    file_lookup = {f.path: f for f in contents.files}

    for path in selected_paths:
        file = file_lookup.get(path)
        if not file:
            logger.warning(f"Selected file not found: {path}")
            continue

        file_content = f"# File: {path}\n{file.content}"

        if file.extension == ".py":
            code_parts.append(file_content)
        elif file.extension == ".sh":
            code_parts.append(file_content)
        elif file.extension in (".yaml", ".yml", ".json", ".toml", ".md", ".txt"):
            info_parts.append(file_content)
        else:
            code_parts.append(file_content)

    experimental_code = "\n\n".join(code_parts)
    experimental_info = "\n\n".join(info_parts)

    return experimental_info, experimental_code


async def _select_files_from_study(
    paper_summary: PaperSummary,
    contents: RepositoryContents,
    code_structure: RepositoryCodeStructure,
    template: str,
    llm_client: LangChainClient,
    llm_config: NodeLLMConfig,
) -> tuple[str, str]:
    if not contents.files:
        logger.warning("No files in repository contents")
        return "", ""

    code_structure_str = code_structure.to_prompt_string()

    env = Environment()
    jinja_template = env.from_string(template)
    message = jinja_template.render(
        {
            "paper_summary": paper_summary,
            "repository_code_structure": code_structure_str,
        }
    )

    try:
        response = await llm_client.structured_outputs(
            llm_name=llm_config.llm_name,
            message=message,
            data_model=SelectedFiles,
            params=llm_config.params,
        )

        selected_files = cast(SelectedFiles, response)

        valid_paths = {f.path for f in contents.files}
        selected_paths = [p for p in selected_files.file_paths if p in valid_paths]

        logger.info(f"LLM selected {len(selected_paths)} files from repository")

        return _build_selected_content(contents, selected_paths)

    except Exception as e:
        logger.error(f"Error selecting files: {e}")
        return "", ""


async def select_experimental_contents(
    llm_config: NodeLLMConfig,
    llm_client: LangChainClient,
    prompt_template: str,
    paper_summary_list: list[PaperSummary],
    repository_contents_list: list[RepositoryContents],
    repository_code_structure_list: list[RepositoryCodeStructure],
    max_workers: int = 3,
) -> tuple[list[str], list[str]]:
    if not (
        len(paper_summary_list)
        == len(repository_contents_list)
        == len(repository_code_structure_list)
    ):
        raise ValueError(
            "paper_summary_list, repository_contents_list, and repository_code_structure_list must have the same length."
        )

    semaphore = asyncio.Semaphore(max(1, max_workers))

    async def _run_task(
        paper_summary: PaperSummary,
        contents: RepositoryContents,
        code_structure: RepositoryCodeStructure,
    ) -> tuple[str, str]:
        async with semaphore:
            return await _select_files_from_study(
                paper_summary,
                contents,
                code_structure,
                prompt_template,
                llm_client,
                llm_config,
            )

    results = await asyncio.gather(
        *(
            _run_task(summary, contents, code_structure)
            for summary, contents, code_structure in zip(
                paper_summary_list,
                repository_contents_list,
                repository_code_structure_list,
                strict=True,
            )
        )
    )

    experimental_info_list = [info for info, _ in results]
    experimental_code_list = [code for _, code in results]

    return experimental_info_list, experimental_code_list
