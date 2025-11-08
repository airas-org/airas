import base64
import logging

from dependency_injector.wiring import Provide, inject

from airas.services.api_client.api_clients_container import SyncContainer
from airas.services.api_client.github_client import GithubClient, GithubClientFatalError
from airas.types.github import GitHubRepositoryInfo
from airas.types.latex import LATEX_TEMPLATE_NAME

logger = logging.getLogger(__name__)


def _merge_bibtex_content(existing: str, new: str) -> str:
    if not new.strip():
        return existing.strip()

    if not existing.strip():
        return new.strip()

    return existing.strip() + "\n\n" + new.strip()


@inject
def update_repository_bibfile(
    github_repository_info: GitHubRepositoryInfo,
    references_bib: str,
    latex_template_name: LATEX_TEMPLATE_NAME,
    github_client: GithubClient = Provide[SyncContainer.github_client],
) -> bool:
    github_owner = github_repository_info.github_owner
    repository_name = github_repository_info.repository_name
    branch_name = github_repository_info.branch_name
    bibfile_path = f".research/latex/{latex_template_name}/references.bib"

    logger.info(
        f"Updating {bibfile_path} in {github_owner}/{repository_name}@{branch_name}"
    )
    try:
        existing_content = github_client.get_repository_content(
            github_owner=github_owner,
            repository_name=repository_name,
            file_path=bibfile_path,
            branch_name=branch_name,
            as_="json",
        )

        if isinstance(existing_content, dict) and "content" in existing_content:
            existing_bib = base64.b64decode(existing_content["content"]).decode("utf-8")
        else:
            existing_bib = ""

    except GithubClientFatalError as e:
        if "404" in str(e):
            logger.info(f"No existing {bibfile_path} found, creating new file")
            existing_bib = ""
        else:
            logger.warning(f"Error downloading existing bibfile, starting fresh: {e}")
            existing_bib = ""

    merged_bib = _merge_bibtex_content(existing_bib, references_bib)

    commit_message = f"Update {bibfile_path} with new references"
    success = github_client.commit_file_bytes(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
        file_path=bibfile_path,
        file_content=merged_bib.encode("utf-8"),
        commit_message=commit_message,
    )

    if success:
        logger.info(f"Successfully updated {bibfile_path}")
    else:
        logger.error(f"Failed to update {bibfile_path}")

    return success
