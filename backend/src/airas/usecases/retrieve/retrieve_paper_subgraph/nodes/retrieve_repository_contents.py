import io
import logging
import re
import zipfile
from dataclasses import dataclass, field

from airas.core.logging_utils import setup_logging
from airas.core.types.research_study import ResearchStudy
from airas.infra.github_client import GithubClient, GithubClientFatalError

setup_logging()
logger = logging.getLogger(__name__)


SUPPORTED_EXTENSIONS: tuple[str, ...] = (
    ".py",
    ".yaml",
    ".yml",
    ".json",
    ".toml",
    ".md",
    ".sh",
    ".txt",
)


@dataclass
class RepositoryFile:
    path: str
    content: str
    extension: str


@dataclass
class RepositoryContents:
    files: list[RepositoryFile] = field(default_factory=list)


def _parse_github_url(github_url: str) -> tuple[str, str] | None:
    match = re.match(r"https://github\.com/([^/]+)/([^/]+)", github_url)
    if not match:
        return None
    return match.group(1), match.group(2)


def _extract_files_from_zip(
    zip_data: bytes, title: str, github_url: str
) -> RepositoryContents:
    result = RepositoryContents()

    try:
        with zipfile.ZipFile(io.BytesIO(zip_data), "r") as zip_file:
            for file_info in zip_file.infolist():
                if file_info.is_dir():
                    continue

                extension = ""
                for ext in SUPPORTED_EXTENSIONS:
                    if file_info.filename.endswith(ext):
                        extension = ext
                        break

                if not extension:
                    continue

                try:
                    file_data = zip_file.read(file_info)
                    content_str = file_data.decode("utf-8")
                except UnicodeDecodeError:
                    logger.warning(
                        f"Skipping binary file: {file_info.filename} in '{title}'"
                    )
                    continue

                # NOTE: Check Git LFS pointer files
                if content_str.strip().startswith(
                    "version https://git-lfs.github.com/spec/v1"
                ):
                    logger.warning(
                        f"Repository '{title}' ({github_url}) appears to use Git LFS, which is not supported. Skipping repository."
                    )
                    return RepositoryContents()

                # NOTE: In the case of ZIP, the repository name prefix is added to the path, so remove it.
                clean_path = (
                    "/".join(file_info.filename.split("/")[1:])
                    if "/" in file_info.filename
                    else file_info.filename
                )

                result.files.append(
                    RepositoryFile(
                        path=clean_path,
                        content=content_str,
                        extension=extension,
                    )
                )

    except Exception as e:
        logger.error(f"Error extracting ZIP contents: {e}")

    return result


def _retrieve_single_repository_contents(
    github_client: GithubClient, github_url: str, title: str
) -> RepositoryContents:
    if not (url_parts := _parse_github_url(github_url)):
        logger.warning(f"Invalid GitHub URL format for '{title}': {github_url}")
        return RepositoryContents()

    github_owner, repository_name = url_parts

    try:
        repo_info = github_client.get_repository(github_owner, repository_name)
        default_branch = repo_info.get("default_branch", "master")

        zip_data = github_client.download_repository_zip(
            github_owner, repository_name, default_branch
        )
        contents = _extract_files_from_zip(zip_data, title, github_url)

        logger.info(
            f"Successfully retrieved repository contents for '{title}': {len(contents.files)} files"
        )
        return contents

    except GithubClientFatalError:
        logger.warning(
            f"Fatal error for repository '{title}': {github_url}. Skipping repository."
        )
        return RepositoryContents()
    except Exception as e:
        logger.error(f"Error processing repository '{title}': {e}")
        return RepositoryContents()


def retrieve_repository_contents(
    research_study_list: list[ResearchStudy],
    github_client: GithubClient,
) -> list[RepositoryContents]:
    contents_list: list[RepositoryContents] = []

    for research_study in research_study_list:
        title = research_study.title or "N/A"

        if not research_study.meta_data or not research_study.meta_data.github_url:
            logger.warning(
                f"No GitHub URL for '{title}', skipping repository content retrieval."
            )
            contents_list.append(RepositoryContents())
            continue

        contents = _retrieve_single_repository_contents(
            github_client, research_study.meta_data.github_url, title
        )
        contents_list.append(contents)

    return contents_list


def retrieve_repository_contents_from_urls(
    github_url_list: list[str],
    github_client: GithubClient,
) -> list[RepositoryContents]:
    contents_list: list[RepositoryContents] = []

    for idx, github_url in enumerate(github_url_list):
        title = f"GitHub Repository {idx + 1}"
        contents = _retrieve_single_repository_contents(
            github_client, github_url, title
        )
        contents_list.append(contents)

    return contents_list
