import base64
import logging
import os

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)
from typing import Any

from airas.utils.api_client.base_http_client import BaseHTTPClient
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 10
DEFAULT_INITIAL_WAIT = 1.0

GITHUB_RETRY = retry(
    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
    wait=wait_exponential(multiplier=DEFAULT_INITIAL_WAIT),
    retry=(
        retry_if_exception_type(requests.RequestException)
        | retry_if_exception_type(RuntimeError)
    ),
    before_sleep=before_sleep_log(logger, logging.INFO),
)


class GithubClient(BaseHTTPClient):
    def __init__(
        self,
        base_url: str = "https://api.github.com",
        default_headers: dict[str, str] | None = None,
    ) -> None:
        auth_headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {os.getenv('GITHUB_PERSONAL_ACCESS_TOKEN')}",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        super().__init__(
            base_url=base_url,
            default_headers={**auth_headers, **(default_headers or {})},
        )

    # --------------------------------------------------
    # Repository
    # --------------------------------------------------

    @GITHUB_RETRY
    def check_repository_existence(
        self, github_owner: str, repository_name: str
    ) -> bool:
        # https://docs.github.com/ja/rest/repos/repos?apiVersion=2022-11-28#get-a-repository
        # For public repositories, no access token is required.
        path = f"/repos/{github_owner}/{repository_name}"

        response = self.get(path=path, parse=False)
        match response.status_code:
            case 200:
                logger.info("A research repository exists (200).")
                return True
            case 404:
                logger.info(f"Repository not found: {path} (404).")
                return False
            case 403:
                raise RuntimeError(
                    f"Access forbidden: {path} (403).\n"
                    "The requested resource has been permanently moved to a new location."
                )
            case 301:
                raise RuntimeError(
                    f"Access forbidden: {path} (301).\n"
                    "You do not have permission to access this resource."
                )
            case _:
                raise RuntimeError(
                    f"Unhandled status code {response.status_code} for URL: {path}\n"
                )
            
    @GITHUB_RETRY
    def get_repository_content(
        self, github_owner: str, repository_name: str, file_path: str
    ) -> str | None:
        # https://docs.github.com/ja/rest/repos/contents?apiVersion=2022-11-28#get-repository-content
        # For public repositories, no access token is required.
        path = f"/repos/{github_owner}/{repository_name}/contents/{file_path}"
        headers={"Accept": "application/vnd.github.raw+json"}

        response = self.get(path=path, headers=headers, parse=False)
        match response.status_code:
            case 200:
                return response.text
            case 302:
                logger.warning("Resource not found (302).")
                return None
            case 304:
                logger.warning("Not Modified (304).")
                return None
            case 403:
                logger.warning("Forbidden (403).")
                return None
            case 404:
                logger.warning("Resource not found (404).")
                return None
            case _:
                raise RuntimeError(
                    f"Unhandled status code {response.status_code} for URL: {path}\n"
                )
            
    @GITHUB_RETRY
    def fork_repository(
        self,
        repository_name: str,
        device_type: str = "cpu",
        organization: str = "",
    ) -> bool:
        if device_type == "cpu":
            source = "auto-res/cpu-repository"
        elif device_type == "gpu":
            source = "auto-res2/gpu-repository"
        else:
            raise ValueError("Invalid device type. Must be 'cpu' or 'gpu'.")

        path = f"/repos/{source}/forks"
        if organization == "":
            json = {
                "name": repository_name,
                "default_branch_only": "true",
            }
        else:
            json = {
                "organization": organization,
                "name": repository_name,
                "default_branch_only": "true",
            }

        response = self.post(path=path, json=json, parse=False)
        match response.status_code:
            case 202:
                logger.info("Fork of the repository was successful (202).")
                return True
            case 400:
                raise RuntimeError(f"Bad request (400): {path}")
            case 403:
                raise RuntimeError(f"Access forbidden (403): {path}")
            case 404:
                raise RuntimeError(f"Resource not found (404): {path}")
            case 422:
                raise RuntimeError(f"Validation failed (422): {path}")
            case _:
                raise RuntimeError(
                    f"Unhandled status code {response.status_code} for URL: {path}\n"
                )

    # --------------------------------------------------
    # Branch
    # --------------------------------------------------

    @GITHUB_RETRY
    def check_branch_existence(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
    ) -> str:
        # https://docs.github.com/ja/rest/branches/branches?apiVersion=2022-11-28#get-a-branch
        # For public repositories, no access token is required.
        path = f"/repos/{github_owner}/{repository_name}/branches/{branch_name}"

        response = self.get(path=path, parse=False)
        match response.status_code:
            case 200:
                logger.info("The specified branch exists (200).")
                response = response.json()
                return response["commit"]["sha"]
            case 404:
                logger.info(f"Branch not found: {path} (404).")
                return ""
            case 301:
                raise RuntimeError(f"Moved permanently: {path} (301).")
            case _:
                raise RuntimeError(
                    f"Unhandled status code {response.status_code} for URL: {path}\n"
                )

    @GITHUB_RETRY
    def create_branch(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
        from_sha: str,
    ) -> bool:
        path = f"/repos/{github_owner}/{repository_name}/git/refs"
        payload = {"ref": f"refs/heads/{branch_name}", "sha": from_sha}

        response = self.post(path=path, json=payload, parse=False)
        match response.status_code:
            case 201:
                logger.info(f"Branch created (201): {branch_name}")
                return True
            case 409:
                raise RuntimeError(f"Conflict creating branch (409): {path}")
            case 422:
                error_message = response.json()
                raise RuntimeError(
                    f"Validation failed, or the endpoint has been spammed (422): {path}\n"
                    f"Error message: {error_message}"
                )
            case _:
                raise RuntimeError(
                    f"Unhandled status code {response.status_code} for URL: {path}\n"
                )

    # --------------------------------------------------
    # Tree
    # --------------------------------------------------

    @GITHUB_RETRY
    def get_a_tree(
        self, github_owner: str, repository_name: str, tree_sha: str
    ) -> dict | None:
        # https://docs.github.com/ja/rest/git/trees?apiVersion=2022-11-28#get-a-tree
        # For public repositories, no access token is required.
        path = f"/repos/{github_owner}/{repository_name}/git/trees/{tree_sha}"
        headers={"Accept": "application/vnd.github.raw+json"}
        params = {"recursive": "true"}

        response = self.get(path=path, headers=headers, params=params, parse=False)
        match response.status_code:
            case 200:
                return response.json()
            case 404:
                logger.warning("Resource not found (404).")
                return None
            case 409:
                logger.warning("Conflict (409).")
                return None
            case 422:
                logger.warning(
                    "Validation failed, or the endpoint has been spammed (422)."
                )
                return None
            case _:
                raise RuntimeError(
                    f"Unhandled status code {response.status_code} for URL: {path}\n"
                )
            
    # --------------------------------------------------
    # Content I/O
    # --------------------------------------------------

    @GITHUB_RETRY
    def read_file_bytes(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
        repository_path: str,
    ) -> bytes:
        path = f"/repos/{github_owner}/{repository_name}/contents/{repository_path}"
        params = {"ref": branch_name}
        
        response = self.get(path=path, params=params)
        if isinstance(response, dict) and "content" in response:
            return base64.b64decode(response["content"])
        raise RuntimeError(f"[GitHub] read_file_bytes: content field not found ({path})")
        

    @GITHUB_RETRY
    def write_file_bytes(
        self,
        *,
        github_owner: str,
        repository_name: str,
        branch_name: str,
        repository_path: str,
        file_content: bytes,
        commit_message: str,
    ) -> bool:
        path = f"/repos/{github_owner}/{repository_name}/contents/{repository_path}"
        params = {"ref": branch_name}
        sha: str | None = None

        response = self.get(path=path, params=params, parse=False)
        if response.status_code == 200 and "sha" in response.json():
            sha = response.json()["sha"]

        payload: dict[str, Any] = {
            "message": commit_message,
            "branch": branch_name,
            "content": base64.b64encode(file_content).decode(),
        }
        if sha:
            payload["sha"] = sha

        response = self.put(path=path, json=payload, parse=False)
        if response.status_code in (200, 201):
            logger.info(f"[GitHub] {repository_path} uploaded/updated → branch {branch_name}")
            return True

        logger.error(
            f"[GitHub] Failed to upload {repository_path} → {response.status_code}: {response.text}"
        )
        return False