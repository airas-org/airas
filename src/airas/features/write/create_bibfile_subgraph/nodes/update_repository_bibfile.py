import base64
import logging
from typing import Any, Dict

from airas.services.api_client.github_client import GithubClient, GithubClientFatalError

logger = logging.getLogger(__name__)


def _merge_bibtex_content(existing: str, new: str) -> str:
    if not new.strip():
        return existing.strip()

    if not existing.strip():
        return new.strip()

    return existing.strip() + "\n\n" + new.strip()


def update_repository_bibfile(
    github_repository: Dict[str, Any],
    references_bib: str,
    bibfile_path: str = ".research/latex/references.bib",
    client: GithubClient | None = None,
) -> bool:
    client = GithubClient() or client

    github_owner = github_repository["github_owner"]
    repository_name = github_repository["repository_name"]
    branch_name = github_repository["branch_name"]

    logger.info(
        f"Updating {bibfile_path} in {github_owner}/{repository_name}@{branch_name}"
    )
    try:
        existing_content = client.get_repository_content(
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
    success = client.commit_file_bytes(
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


def main():
    test_github_repository = {
        "url": "https://github.com/test-owner/test-repo.git",
        "branch": "main",
    }

    test_references_bib = """@article{test_2024_example,
    title = {Test Example Paper},
    author = {Test Author},
    year = {2024},
    journal = {Test Journal},
    abstract = {This is a test abstract for demonstration purposes.}
}"""

    try:
        success = update_repository_bibfile(
            github_repository=test_github_repository, references_bib=test_references_bib
        )
        print(f"Update successful: {success}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
