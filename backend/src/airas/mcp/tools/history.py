"""Research history persistence (GitHub)."""

from typing import Any

from pydantic import ConfigDict, model_validator

from airas.core.types.github import GitHubConfig
from airas.core.types.research_history import ResearchHistory
from airas.mcp.app import mcp
from airas.mcp.context import (
    _dump,
    _github_client,
)
from airas.usecases.github.github_download_subgraph import GithubDownloadSubgraph
from airas.usecases.github.github_upload_subgraph import GithubUploadSubgraph


def _reject_unknown_history_keys(research_history: dict[str, Any]) -> None:
    """Refuse a key the model would drop, instead of dropping it.

    ResearchHistory leaves pydantic's default `extra="ignore"` in place, so
    an undeclared top-level key vanishes during validation and the upload
    still reports success. A caller who passed eight keys and had six
    silently discarded learns nothing until a later session restores an
    empty-looking history.

    The strictness belongs here rather than on the model: the same model
    parses `.research/research_history.json` back out of the repository,
    where a file written by hand — which the skills instruct agents to
    do — must not make the whole restore fail.
    """
    if not isinstance(research_history, dict):
        raise ValueError(
            "research_history must be a JSON object keyed by field name, not "
            f"{type(research_history).__name__}."
        )
    unknown = sorted(set(research_history) - set(ResearchHistory.model_fields))
    if not unknown:
        return
    raise ValueError(
        f"research_history has {len(unknown)} key(s) that would be discarded "
        f"without warning: {', '.join(unknown)}. Accepted fields are "
        f"{', '.join(ResearchHistory.model_fields)}. Anything that does not "
        "map onto one of them belongs under `additional_data`, which takes "
        "an arbitrary dict; call get_input_schema('research_history') for "
        "the full shape."
    )


class _ResearchHistoryInput(ResearchHistory):
    """The upload-side view of ResearchHistory: same fields, nothing dropped.

    Typing the tool parameter as this rather than `dict[str, Any]` is what
    puts the field list into the schema the MCP client already reads from
    `tools/list` — a plain dict publishes `additionalProperties: true` and
    no properties at all, which tells the caller nothing. `extra="forbid"`
    both refuses the keys that used to vanish and shows up in that schema,
    so the boundary advertises that it is strict.

    ResearchHistory itself stays lenient: it also parses
    `.research/research_history.json` back out of the repository, where a
    file written by hand — which the skills instruct agents to do — must
    not make the whole restore fail.
    """

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def _reject_dropped_keys(cls, data: Any) -> Any:
        # pydantic's own "Extra inputs are not permitted" does not mention
        # additional_data, and a caller who is not told about the escape
        # hatch just deletes the data instead of moving it.
        if isinstance(data, dict):
            _reject_unknown_history_keys(data)
        return data


@mcp.tool()
async def upload_research_history(
    github_owner: str,
    repository_name: str,
    branch_name: str,
    research_history: _ResearchHistoryInput,
    commit_message: str | None = None,
) -> dict[str, Any]:
    """Save research history (hypothesis, design, results, ...) to the experiment repository.

    AIRAS persists research state in the GitHub repository, so uploading the
    accumulated history lets you resume work in a later session with
    `download_research_history`. Requires GH_PERSONAL_ACCESS_TOKEN.

    `research_history` takes only the fields in this tool's own schema, and
    any other top-level key is rejected rather than dropped. Anything the
    schema has no home for belongs under `additional_data`, a free-form
    dict. `get_input_schema("research_history")` returns the same shape if
    you would rather ask for it directly.
    """
    result = (
        await GithubUploadSubgraph(_github_client())
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                ),
                "research_history": research_history,
                "commit_message": commit_message,
            }
        )
    )
    return {"is_github_upload": result["is_github_upload"]}


@mcp.tool()
async def download_research_history(
    github_owner: str,
    repository_name: str,
    branch_name: str,
) -> dict[str, Any]:
    """Load previously saved research history from the experiment repository.

    Restores the state saved by `upload_research_history` so a research
    session can continue where it left off. Requires GH_PERSONAL_ACCESS_TOKEN.
    """
    result = (
        await GithubDownloadSubgraph(_github_client())
        .build_graph()
        .ainvoke(
            {
                "github_config": GitHubConfig(
                    github_owner=github_owner,
                    repository_name=repository_name,
                    branch_name=branch_name,
                )
            }
        )
    )
    return _dump(result["research_history"])
