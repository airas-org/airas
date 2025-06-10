import base64
import logging
import os
from datetime import datetime, timezone
from typing import Any, Literal, Protocol, runtime_checkable

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from airas.utils.api_client.base_http_client import BaseHTTPClient
from airas.utils.api_client.response_parser import ResponseParser
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


@runtime_checkable
class ResponseParserProtocol(Protocol):
    def parse(self, response: requests.Response, *, as_: str) -> Any: ...

class GithubClientError(RuntimeError): ...
class GithubClientRetryableError(GithubClientError): ...
class GithubClientFatalError(GithubClientError): ...

DEFAULT_MAX_RETRIES = 10
DEFAULT_INITIAL_WAIT = 1.0

GITHUB_RETRY = retry(
    stop=stop_after_attempt(DEFAULT_MAX_RETRIES),
    wait=wait_exponential(multiplier=DEFAULT_INITIAL_WAIT),
    before_sleep=before_sleep_log(logger, logging.WARNING),
    reraise=True,
    retry=(
        retry_if_exception_type(GithubClientRetryableError)
        | retry_if_exception_type(requests.RequestException)
    ),
)

# TODO: Raise exceptions for all error cases; let the caller handle failures.
# TODO: Use an Enum for HTTP status codes and extract retry logic into a mixin for reuse across API clients.

class GithubClient(BaseHTTPClient):
    def __init__(
        self,
        base_url: str = "https://api.github.com",
        default_headers: dict[str, str] | None = None,
        parser: ResponseParserProtocol | None = None, 
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
        self._parser = parser or ResponseParser()

    @staticmethod
    def _raise_for_status(response: requests.Response, path: str) -> None:
        code = response.status_code

        if 200 <= code < 300:
            return
        
        if 300 <= code < 400:
            location = response.headers.get("Location", "unknown")
            logger.warning(f"Unexpected redirect ({code}) for {path} → {location}")
            raise GithubClientRetryableError(f"Redirect response ({code}) for {path}; check Location: {location}")

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
            raise GithubClientFatalError(f"Client error {code} for URL {path}: {response.text}")

        if 500 <= code < 600:
            raise GithubClientRetryableError(f"Server error {code} for URL {path}: {response.text}")

        raise GithubClientFatalError(f"Unexpected status {code}: {response.text}")

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
                return self._parser.parse(response, as_="json")
            case 404:
                logger.warning(f"Repository not found: {path} (404).")
                raise GithubClientFatalError(f"Resource not found (404): {path}")
            case _:
                self._raise_for_status(response, path)


    def _fetch_content(
        self, 
        github_owner: str, 
        repository_name: str, 
        file_path: str, 
        branch_name: str | None = None,  # NOTE: If None, the repository's default branch will be used.
        as_: Literal["json", "bytes"] = "json", 
    ) -> dict | bytes:
        # https://docs.github.com/ja/rest/repos/contents?apiVersion=2022-11-28#get-repository-content
        path = f"/repos/{github_owner}/{repository_name}/contents/{file_path}"

        headers = None
        if as_ == "bytes":
            headers = {"Accept": "application/vnd.github.raw+json"}

        response = self.get(path, params={"ref": branch_name}, headers=headers)
        match response.status_code:
            case 200:
                logger.info(f"Success (200): {path}")
                return self._parser.parse(response, as_=as_)
            case 404:
                logger.warning(f"Resource not found (404): {path}")
                raise GithubClientFatalError(f"Resource not found (404): {path}")
            case 403:
                logger.error(f"Access forbidden (403): {path}")
                raise GithubClientFatalError(f"Access forbidden (403): {path}")
            case _:
                self._raise_for_status(response, path)  

    @GITHUB_RETRY
    def get_repository_content(
        self, 
        github_owner: str, 
        repository_name: str, 
        file_path: str, 
        branch_name: str | None = None, 
        as_: Literal["json", "bytes"] = "json"
    ) -> dict | bytes:
        return self._fetch_content(
            github_owner=github_owner, 
            repository_name=repository_name, 
            file_path=file_path, 
            branch_name=branch_name, 
            as_=as_, 
        )

    @GITHUB_RETRY
    def commit_file_bytes(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
        file_path: str,
        file_content: bytes,
        commit_message: str,
    ) -> bool:
        sha: str | None = None
        try:
            meta = self._fetch_content(
                github_owner=github_owner,
                repository_name=repository_name,
                file_path=file_path,
                branch_name=branch_name,
            )
            if isinstance(meta, dict):
                sha = meta.get("sha")
        except GithubClientFatalError as e:
            if "404" in str(e):
                logger.warning(f"File not found, will create new: {file_path}")
                sha = None
            else:
                raise

        payload = {
            "message": commit_message,
            "branch": branch_name,
            "content": base64.b64encode(file_content).decode(),
        }
        if sha:
            payload["sha"] = sha

        path = f"/repos/{github_owner}/{repository_name}/contents/{file_path}"
        response = self.put(path=path, json=payload)

        match response.status_code:
            case 200 | 201:
                logger.info(f"Success (200): {path}")
                return True
            case 403:
                logger.error(f"Access forbidden (403): {path}")
                raise GithubClientFatalError(f"Access forbidden (403): {path}")
            case _:
                self._raise_for_status(response, path)
                return False
            
    @GITHUB_RETRY
    def fork_repository(   # NOTE: Currently unused because a template is being used
        self,
        repository_name: str,
        device_type: str = "gpu",
        organization: str = "",
    ) -> bool:
        # https://docs.github.com/ja/rest/repos/forks?apiVersion=2022-11-28#create-a-fork
        # TODO：Integrate the CPU repository and GPU repository. Make it possible to specify which one to use when running experiments.
        if device_type == "cpu":
            source = "auto-res/cpu-repository"
        elif device_type == "gpu":
            source = "airas-org/airas-template"
        else:
            raise ValueError("Invalid device type. Must be 'cpu' or 'gpu'.")

        path = f"/repos/{source}/forks"
        json = {
            "name": repository_name,
            "default_branch_only": "true",
            **({"organization": organization} if organization else {}),
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
            
    @GITHUB_RETRY
    def create_repository_from_template(
        self,
        github_owner: str, 
        repository_name: str,
        template_owner: str,
        template_repo: str,
        include_all_branches: bool = True,
        private: bool = False,
    ) -> dict | None:        
        # https://docs.github.com/ja/rest/repos/repos?apiVersion=2022-11-28#create-a-repository-using-a-template
        path = f"/repos/{template_owner}/{template_repo}/generate"
        payload: dict[str, Any] = {
            "owner": github_owner, 
            "name": repository_name,
            "include_all_branches": include_all_branches,
            "private": private,
        }

        response = self.post(path=path, json=payload)
        match response.status_code:
            case 201:
                logger.info(f"Repository created from template (201): {template_owner}/{template_repo} → {repository_name}")
                return self._parser.parse(response, as_="json")
            case 404:
                raise GithubClientFatalError(f"Template not found (404): {path}")
            case 422:
                raise GithubClientFatalError(f"Validation failed or repository already exists (422): {response.text}")
            case _:
                self._raise_for_status(response, path)
                return None  
    
    # --------------------------------------------------
    # Branch
    # --------------------------------------------------

    @GITHUB_RETRY
    def get_branch(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
    ) -> dict | None:
        # https://docs.github.com/ja/rest/branches/branches?apiVersion=2022-11-28#get-a-branch
        # For public repositories, no access token is required.
        path = f"/repos/{github_owner}/{repository_name}/branches/{branch_name}"

        response = self.get(path=path)
        match response.status_code:
            case 200:
                logger.info("The specified branch exists (200).")
                response = self._parser.parse(response, as_="json")
                return response
            case 301:
                logger.warning(f"Moved permanently: {path} (301).")
                return None  # NOTE: Returning None is intentional; a missing branch is an expected case.
            case 404:
                logger.warning(f"Branch not found: {path} (404).")
                return None
            case _:
                self._raise_for_status(response, path)
                return None
            
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
    ) -> dict | None:
        # https://docs.github.com/ja/rest/git/trees?apiVersion=2022-11-28#get-a-tree
        # For public repositories, no access token is required.
        path = f"/repos/{github_owner}/{repository_name}/git/trees/{tree_sha}"
        params = {"recursive": "true"}

        response = self.get(path=path, params=params)
        match response.status_code:
            case 200:
                return self._parser.parse(response, as_="json")
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
                return None

    # --------------------------------------------------
    # Github Actions
    # --------------------------------------------------

    @GITHUB_RETRY
    def create_workflow_dispatch(
        self, 
        github_owner: str, 
        repository_name: str, 
        workflow_file_name: str, 
        ref: str, 
        inputs: dict | None = None, 
    ) -> bool:
        # https://docs.github.com/ja/rest/actions/workflows?apiVersion=2022-11-28#create-a-workflow-dispatch-event
        path = f"/repos/{github_owner}/{repository_name}/actions/workflows/{workflow_file_name}/dispatches"
        json = {"ref": ref, **({"inputs": inputs} if inputs else {})}
        
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
    ) -> dict | None:
        # https://docs.github.com/ja/rest/actions/workflow-runs?apiVersion=2022-11-28#list-workflow-runs-for-a-repository
        path = f"/repos/{github_owner}/{repository_name}/actions/runs"
        params = {"branch": branch_name, "event": event}
        response = self.get(path=path, params=params)
        match response.status_code:
            case 200:
                logger.info(f"Success (200): {path}")
                return self._parser.parse(response, as_="json")
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
                return None
            
    @GITHUB_RETRY
    def list_repository_artifacts(
        self, 
        github_owner: str, 
        repository_name: str, 
    ) -> dict | None:
        # https://docs.github.com/ja/rest/actions/artifacts?apiVersion=2022-11-28#list-artifacts-for-a-repository
        path = f"/repos/{github_owner}/{repository_name}/actions/artifacts"
        response = self.get(path=path)
        match response.status_code:
            case 200:
                logger.info(f"Success (200): {path}")
                return self._parser.parse(response, as_="json")
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
                return None
    
    @GITHUB_RETRY
    def download_artifact_archive(
        self, 
        github_owner: str, 
        repository_name: str, 
        artifact_id: int, 
    ) -> bytes | None:
        # https://docs.github.com/ja/rest/actions/artifacts?apiVersion=2022-11-28#download-an-artifact
        path = f"/repos/{github_owner}/{repository_name}/actions/artifacts/{artifact_id}/zip"
        
        response = self.get(path=path, stream=True)
        match response.status_code:
            case 200:
                logger.info(f"Success (200): {path}")
                return self._parser.parse(response, as_="bytes")
            case 302:
                logger.info(f"Found (302): {path}")
                return self._parser.parse(response, as_="bytes")
            case 404:
                logger.error(f"Artifact not found: {artifact_id} (404)")
                raise GithubClientFatalError(f"Artifact not found: {artifact_id} (404)")
            case _:
                self._raise_for_status(response, path)
                return None
