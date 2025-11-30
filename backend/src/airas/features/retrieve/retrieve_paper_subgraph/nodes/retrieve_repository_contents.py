import io
import logging
import re
import zipfile

from airas.services.api_client.github_client import GithubClient, GithubClientFatalError
from airas.types.research_study import ResearchStudy
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def _parse_github_url(github_url: str) -> tuple[str, str] | None:
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)", github_url)
    if not match:
        return None
    return match.group(1), match.group(2)


def _extract_python_files_from_zip(zip_data: bytes, title: str, github_url: str) -> str:
    try:
        with zipfile.ZipFile(io.BytesIO(zip_data), "r") as zip_file:
            contents = []

            for file_info in zip_file.infolist():
                if file_info.is_dir() or not file_info.filename.endswith(".py"):
                    continue

                file_data = zip_file.read(file_info)
                content_str = file_data.decode("utf-8")

                # NOTE: Check Git LFS pointer files
                if content_str.strip().startswith(
                    "version https://git-lfs.github.com/spec/v1"
                ):
                    logger.warning(
                        f"Repository '{title}' ({github_url}) appears to use Git LFS, which is not supported. Skipping repository."
                    )
                    return ""

                # NOTE: In the case of ZIP, the repository name prefix is added to the path, so remove it.
                clean_path = (
                    "/".join(file_info.filename.split("/")[1:])
                    if "/" in file_info.filename
                    else file_info.filename
                )

                contents.append(f"File Path: {clean_path}\nContent:\n{content_str}")

            return "\n".join(contents)

    except Exception as e:
        logger.error(f"Error extracting ZIP contents: {e}")
        return ""


def _retrieve_single_repository_contents(
    github_client: GithubClient, github_url: str, title: str
) -> str:
    if not (url_parts := _parse_github_url(github_url)):
        logger.warning(f"Invalid GitHub URL format for '{title}': {github_url}")
        return ""

    github_owner, repository_name = url_parts

    try:
        repo_info = github_client.get_repository(github_owner, repository_name)
        default_branch = repo_info.get("default_branch", "master")

        zip_data = github_client.download_repository_zip(
            github_owner, repository_name, default_branch
        )
        contents = _extract_python_files_from_zip(zip_data, title, github_url)

        file_count = len(contents.split("File Path:")) - 1 if contents else 0
        logger.info(
            f"Successfully retrieved repository contents for '{title}': {file_count} files"
        )
        return contents

    except GithubClientFatalError:
        logger.warning(
            f"Fatal error for repository '{title}': {github_url}. Skipping repository."
        )
        return ""
    except Exception as e:
        logger.error(f"Error processing repository '{title}': {e}")
        return ""


def retrieve_repository_contents(
    research_study_list: list[ResearchStudy],
    github_client: GithubClient,
) -> list[str]:
    code_str_list = []

    for research_study in research_study_list:
        title = research_study.title or "N/A"

        if not research_study.meta_data or not research_study.meta_data.github_url:
            logger.warning(
                f"No GitHub URL for '{title}', skipping repository content retrieval."
            )
            code_str_list.append("")
            continue

        content = _retrieve_single_repository_contents(
            github_client, research_study.meta_data.github_url, title
        )
        code_str_list.append(content)

    return code_str_list


def retrieve_repository_contents_from_url_groups(
    github_url_list: list[list[str]],
    github_client: GithubClient,
) -> list[list[str]]:
    github_code_list: list[list[str]] = []

    for group_idx, url_group in enumerate(github_url_list):
        code_group: list[str] = []
        for url_idx, github_url in enumerate(url_group):
            title = f"GitHub Repository {group_idx + 1}-{url_idx + 1}"
            content = _retrieve_single_repository_contents(
                github_client, github_url, title
            )
            # NOTE: Always store a placeholder string when content could not be retrieved.
            code_group.append(content if content else "")
        github_code_list.append(code_group)

    return github_code_list
