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
from datetime import datetime, timezone

from airas.utils.api_client.base_http_client import BaseHTTPClient
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

DEFAULT_MAX_RETRIES = 10
DEFAULT_INITIAL_WAIT = 1.0


class GithubClientError(RuntimeError):
    ...

class GithubClientRetryableError(GithubClientError):
    ...

class GithubClientFatalError(GithubClientError):
    ...

GITHUB_RETRY = retry(
    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
    wait=wait_exponential(multiplier=DEFAULT_INITIAL_WAIT),
    retry=(
        retry_if_exception_type(GithubClientRetryableError)
        | retry_if_exception_type(requests.RequestException)
    ),
    before_sleep=before_sleep_log(logger, logging.WARNING),
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

    @staticmethod
    def _raise_for_status(response: requests.Response, path: str) -> None:
        code = response.status_code

        if 200 <= code < 300:
            return
        
        if 300 <= code < 400:
            location = response.headers.get("Location", "unknown")
            logger.warning(f"Unexpected redirect ({code}) for {path} → {location}")
            raise GithubClientRetryableError(
                f"Redirect response ({code}) for {path}; check Location: {location}"
            )

        if code == 403:
            if response.headers.get("X-RateLimit-Remaining") == "0":
                reset_epoch = int(response.headers.get("X-RateLimit-Reset", "0"))
                reset_dt = datetime.fromtimestamp(reset_epoch, tz=timezone.utc)
                delay = max((reset_dt - datetime.now(tz=timezone.utc)).total_seconds(), 0)
                logger.warning(f"GitHub rate limit exceeded; will retry after {delay:.0f} s (at {reset_dt.isoformat()})")
                raise GithubClientRetryableError(
                    f"Rate limit exceeded for {path}; retry after {delay:.0f} s"
                )
            else:
                raise GithubClientFatalError(
                    f"Access forbidden (403) for {path}: {response.text}"
                )
        
        if 400 <= code < 500:
            raise GithubClientFatalError(
                f"Client error {code} for URL {path}: {response.text}"
            )

        if 500 <= code < 600:
            raise GithubClientRetryableError(
                f"Server error {code} for URL {path}: {response.text}"
            )

        if code >= 600 or code < 200:
            raise GithubClientFatalError(
                f"Unexpected HTTP status {code} for URL {path}: {response.text}"
            )
        
        raise GithubClientRetryableError(
            f"Unhandled status code {code} for URL: {path}"
        )

    # --------------------------------------------------
    # Repository
    # --------------------------------------------------

    @GITHUB_RETRY
    def get_repository(
        self, github_owner: str, repository_name: str
    ) -> dict:
        # https://docs.github.com/ja/rest/repos/repos?apiVersion=2022-11-28#get-a-repository
        # For public repositories, no access token is required.
        path = f"/repos/{github_owner}/{repository_name}"

        response = self.get(path=path)
        match response.status_code:
            case 200:
                logger.info("A research repository exists (200).")
                return self.parse_response(response)
            case 404:
                logger.warning(f"Repository not found: {path} (404).")
                return None  # NOTE: Returning None is intentional; a missing branch is an expected case.
            case _:
                self._raise_for_status(response, path)
                return self.parse_response

            
    @GITHUB_RETRY
    def get_repository_content(
        self, github_owner: str, repository_name: str, file_path: str
    ) -> bytes | None:
        # https://docs.github.com/ja/rest/repos/contents?apiVersion=2022-11-28#get-repository-content
        # For public repositories, no access token is required.
        path = f"/repos/{github_owner}/{repository_name}/contents/{file_path}"
        headers={"Accept": "application/vnd.github.raw+json"}

        response = self.get(path=path, headers=headers)
        match response.status_code:
            case 200:
                return self.parse_response(response)
            case 302:
                logger.warning("Found (301).")
                return None  # NOTE: Returning None is intentional; a missing branch is an expected case.
            case 304:
                logger.warning("Not modified (304).")
                return None
            case _:
                self._raise_for_status(response, path)
                return self.parse_response(response)
            
    @GITHUB_RETRY
    def fork_repository(
        self,
        repository_name: str,
        device_type: str = "cpu",
        organization: str = "",
    ) -> bool:
        # https://docs.github.com/ja/rest/repos/forks?apiVersion=2022-11-28#create-a-fork
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

        response = self.post(path=path, json=json)
        match response.status_code:
            case 202:
                logger.info("Fork of the repository was successful (202).")
                return True
            case 400:
                logger.error(f"Bad Request (400): {path}")
                raise GithubClientFatalError(f"Bad Request (400): {path}")
            case 404:
                logger.error(f"Resource not found (404): {path}")
                raise GithubClientFatalError(f"Resource not found (404): {path}")
            case 422:
                logger.error(f"Validation failed, or the endpoint has been spammed (422): {path}")
                raise GithubClientFatalError(f"Validation failed, or the endpoint has been spammed (422): {path}")
            case _:
                self._raise_for_status(response, path)
                return False

    # --------------------------------------------------
    # Branch
    # --------------------------------------------------

    @GITHUB_RETRY
    def check_branch_existence(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
    ) -> str | None:
        # https://docs.github.com/ja/rest/branches/branches?apiVersion=2022-11-28#get-a-branch
        # For public repositories, no access token is required.
        path = f"/repos/{github_owner}/{repository_name}/branches/{branch_name}"

        response = self.get(path=path)
        match response.status_code:
            case 200:
                logger.info("The specified branch exists (200).")
                response = self.parse_response(response)
                return response["commit"]["sha"]
            case 301:
                logger.warning(f"Moved permanently: {path} (301).")
                return None  # NOTE: Returning None is intentional; a missing branch is an expected case.
            case 404:
                logger.error(f"Branch not found: {path} (404).")
                return None
            case _:
                self._raise_for_status(response, path)
                return self.parse_response(response)

    @GITHUB_RETRY
    def create_branch(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
        from_sha: str,
    ) -> bool:
        # https://docs.github.com/ja/rest/git/refs?apiVersion=2022-11-28#create-a-reference
        path = f"/repos/{github_owner}/{repository_name}/git/refs"
        payload = {"ref": f"refs/heads/{branch_name}", "sha": from_sha}

        response = self.post(path=path, json=payload)
        match response.status_code:
            case 201:
                logger.info(f"Branch created (201): {branch_name}")
                return True
            case 409:
                logger.error(f"Conflict creating branch (409): {path}")
                raise GithubClientFatalError(f"Conflict creating branch (409): {path}")
            case 422:
                logger.error(f"Validation failed, or the endpoint has been spammed (422): {path}")
                raise GithubClientFatalError(f"Validation failed, or the endpoint has been spammed (422): {path}")
            case _:
                self._raise_for_status(response, path)
                return False

    # --------------------------------------------------
    # Tree
    # --------------------------------------------------

    @GITHUB_RETRY
    def get_a_tree(
        self, github_owner: str, repository_name: str, tree_sha: str
    ) -> dict:
        # https://docs.github.com/ja/rest/git/trees?apiVersion=2022-11-28#get-a-tree
        # For public repositories, no access token is required.
        path = f"/repos/{github_owner}/{repository_name}/git/trees/{tree_sha}"
        headers={"Accept": "application/vnd.github+json"}
        params = {"recursive": "true"}

        response = self.get(path=path, headers=headers, params=params)
        match response.status_code:
            case 200:
                return self.parse_response(response)
            case 404:
                logger.error("Resource not found (404).")
                raise GithubClientFatalError(f"Resource not found (404): {path}")
            case 409:
                logger.error("Conflict (409).")
                raise GithubClientFatalError("Conflict (409).")
            case 422:
                logger.error("Validation failed, or the endpoint has been spammed (422).")
                raise GithubClientFatalError("Validation failed, or the endpoint has been spammed (422).")
            case _:
                self._raise_for_status(response, path)
                return self.parse_response(response)
            
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
    ) -> dict:
        path = f"/repos/{github_owner}/{repository_name}/contents/{repository_path}"
        params = {"ref": branch_name}
        
        response = self.get(path=path, params=params)
        match response.status_code:
            case 200:
                logger.info(f"Success (200): {path}")
                return self.parse_response(response)
            case 404:
                logger.error(f"Resource not found (404): {path}")
                raise GithubClientFatalError(f"Resource not found (404): {path}")
            case 403:
                logger.error(f"Access forbidden (403): {path}")
                raise GithubClientFatalError(f"Access forbidden (403): {path}")
            case _:
                self._raise_for_status(response, path)
                return self.parse_response(response)

    @GITHUB_RETRY
    def write_file_bytes(
        self,
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

        response = self.get(path=path, params=params)
        # TODO: Set the condition of status code

        if response.status_code == 200 and "sha" in response.json():
            sha = response.json()["sha"]

        payload: dict[str, Any] = {
            "message": commit_message,
            "branch": branch_name,
            "content": base64.b64encode(file_content).decode(),
        }
        if sha:
            payload["sha"] = sha

        response = self.put(path=path, json=payload)
        if response.status_code in (200, 201):
            logger.info(f"[GitHub] {repository_path} uploaded/updated → branch {branch_name}")
            return True

        logger.error(
            f"[GitHub] Failed to upload {repository_path} → {response.status_code}: {response.text}"
        )
        return False
    
    # --------------------------------------------------
    # Github Actions
    # --------------------------------------------------

    @GITHUB_RETRY
    def dispatch_workflow(
        self, 
        github_owner: str, 
        repository_name: str, 
        workflow_file_name: str, 
        ref: str, 
        inputs: dict | None = None, 
    ) -> bool:
        # https://docs.github.com/ja/rest/actions/workflows?apiVersion=2022-11-28#create-a-workflow-dispatch-event
        path = f"/repos/{github_owner}/{repository_name}/actions/workflows/{workflow_file_name}/dispatches"
        json = {"ref": ref}
        if inputs:
            json["inputs"] = inputs
        
        response = self.post(path=path, json=json)
        match response.status_code:
            case 204:
                logger.info("Workflow dispatch accepted.")
                return True
            case 403:
                logger.error(f"Access forbidden (403): {path}")
                raise GithubClientFatalError(f"Access forbidden (403): {path}")
            case 404:
                logger.error(f"Workflow or repository not found (404): {path}")
                raise GithubClientFatalError(f"Workflow or repository not found (404): {path}")
            case 422:
                logger.error(f"Validation failed, or the endpoint has been spammed (422): {path}")
                raise GithubClientFatalError(f"Validation failed, or the endpoint has been spammed (422): {path}")
            case _:
                self._raise_for_status(response, path)
                return False
            
    @GITHUB_RETRY
    def list_workflow_runs(
        self,
        github_owner: str, 
        repository_name: str, 
        branch_name: str, 
        event: str = "workflow_dispatch", 
    ) -> dict:
        # https://docs.github.com/ja/rest/actions/workflow-runs?apiVersion=2022-11-28#list-workflow-runs-for-a-repository
        path = f"/repos/{github_owner}/{repository_name}/actions/runs"
        params = {"branch": branch_name, "event": event}
        response = self.get(path=path, params=params)
        match response.status_code:
            case 200:
                logger.info(f"Success (200): {path}")
                return self.parse_response(response)
            case 403:
                logger.error(f"Access forbidden (403): {path}")
                raise GithubClientFatalError(f"Access forbidden (403): {path}")
            case 404:
                logger.error(f"Workflow or repository not found (404): {path}")
                raise GithubClientFatalError(f"Workflow or repository not found (404): {path}")
            case 422:
                logger.error(f"Validation failed, or the endpoint has been spammed (422): {path}")
                raise GithubClientFatalError(f"Validation failed, or the endpoint has been spammed (422): {path}")
            case _:
                self._raise_for_status(response, path)
                return self.parse_response(response)
            
    @GITHUB_RETRY
    def list_repository_artifacts(
        self, 
        github_owner: str, 
        repository_name: str, 
    ) -> dict:
        # https://docs.github.com/ja/rest/actions/artifacts?apiVersion=2022-11-28#list-artifacts-for-a-repository
        path = f"/repos/{github_owner}/{repository_name}/actions/artifacts"
        response = self.get(path=path)
        match response.status_code:
            case 200:
                logger.info(f"Success (200): {path}")
                return self.parse_response(response)
            case 403:
                logger.error(f"Access forbidden (403): {path}")
                raise GithubClientFatalError(f"Access forbidden (403): {path}")
            case 404:
                logger.error(f"Workflow or repository not found (404): {path}")
                raise GithubClientFatalError(f"Workflow or repository not found (404): {path}")
            case 422:
                logger.error(f"Validation failed, or the endpoint has been spammed (422): {path}")
                raise GithubClientFatalError(f"Validation failed, or the endpoint has been spammed (422): {path}")
            case _:
                self._raise_for_status(response, path)
                return self.parse_response(response)
    
    @GITHUB_RETRY
    def download_artifact_archive(
        self, 
        github_owner: str, 
        repository_name: str, 
        artifact_id: int, 
    ) -> bytes:
        # https://docs.github.com/ja/rest/actions/artifacts?apiVersion=2022-11-28#download-an-artifact
        path = f"/repos/{github_owner}/{repository_name}/actions/artifacts/{artifact_id}/zip"
        
        response = self.get(path=path, stream=True)
        match response.status_code:
            case 200:
                logger.info(f"Success (200): {path}")
                return self.parse_response(response)
            case 302:
                logger.info(f"Found (302): {path}")
                return self.parse_response(response)
            case 404:
                logger.error(f"Artifact not found: {artifact_id} (404)")
                raise GithubClientFatalError(f"Artifact not found: {artifact_id} (404)")
            case _:
                self._raise_for_status(response, path)
                return self.parse_response(response)