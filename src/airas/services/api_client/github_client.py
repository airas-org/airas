import asyncio
import base64
import logging
import os
from datetime import datetime, timezone
from typing import Any, Literal, Protocol, runtime_checkable

import httpx
import requests
from nacl import public
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from airas.services.api_client.base_http_client import BaseHTTPClient
from airas.services.api_client.response_parser import ResponseParser
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
    def _raise_for_status(
        response: requests.Response | httpx.Response, path: str
    ) -> None:
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
                delay = max(
                    (reset_dt - datetime.now(tz=timezone.utc)).total_seconds(), 0
                )
                logger.warning(
                    f"GitHub rate limit exceeded; will retry after {delay:.0f} s (at {reset_dt.isoformat()})"
                )
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

        raise GithubClientFatalError(f"Unexpected status {code}: {response.text}")

    # --------------------------------------------------
    # Repository
    # --------------------------------------------------

    @GITHUB_RETRY
    def get_repository(self, github_owner: str, repository_name: str) -> dict:
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
        branch_name: str
        | None = None,  # NOTE: If None, the repository's default branch will be used.
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
        as_: Literal["json", "bytes"] = "json",
    ) -> dict | bytes:
        # https://docs.github.com/ja/rest/repos/contents?apiVersion=2022-11-28#get-repository-content
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
    def fork_repository(  # NOTE: Currently unused because a template is being used
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
                logger.error(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
                raise GithubClientFatalError(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
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
                logger.info(
                    f"Repository created from template (201): {template_owner}/{template_repo} → {repository_name}"
                )
                return self._parser.parse(response, as_="json")
            case 404:
                raise GithubClientFatalError(f"Template not found (404): {path}")
            case 422:
                raise GithubClientFatalError(
                    f"Validation failed or repository already exists (422): {response.text}"
                )
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
                logger.error(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
                raise GithubClientFatalError(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
            case _:
                self._raise_for_status(response, path)
                return False

    def list_commits(
        self,
        github_owner: str,
        repository_name: str,
        sha: str | None = None,
        per_page: int = 100,
        page: int = 1,
    ) -> list[dict]:
        # https://docs.github.com/ja/rest/commits/commits?apiVersion=2022-11-28#list-commits
        path = f"/repos/{github_owner}/{repository_name}/commits"
        params = {
            **({"sha": sha} if sha else {}),
            "per_page": per_page,
            "page": page,
        }

        response = self.get(path=path, params=params)
        if response.status_code == 200:
            return self._parser.parse(response, as_="json")
        self._raise_for_status(response, path)

    @GITHUB_RETRY
    def download_repository_zip(
        self, github_owner: str, repository_name: str, ref: str = "master"
    ) -> bytes:
        # https://docs.github.com/en/rest/repos/contents#download-a-repository-archive-zip
        path = f"/repos/{github_owner}/{repository_name}/zipball/{ref}"

        response = self.get(path=path, stream=True)
        match response.status_code:
            case 200:
                logger.info(f"Successfully downloaded ZIP: {path}")
                return response.content
            case 302:
                # Handle redirect
                location = response.headers.get("Location")
                if location:
                    redirect_response = requests.get(location)
                    if redirect_response.status_code == 200:
                        return redirect_response.content
                logger.warning(f"Failed to follow redirect for ZIP download: {path}")
                self._raise_for_status(response, path)
            case _:
                self._raise_for_status(response, path)

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
                logger.error(
                    "Validation failed, or the endpoint has been spammed (422)."
                )
                raise GithubClientFatalError(
                    "Validation failed, or the endpoint has been spammed (422)."
                )
            case _:
                self._raise_for_status(response, path)
                return None

    # --------------------------------------------------
    # Git Data API (for batch commits)
    # --------------------------------------------------

    @GITHUB_RETRY
    def create_blob(
        self,
        github_owner: str,
        repository_name: str,
        content: str,
        encoding: str = "utf-8",
    ) -> str:
        """Create a blob object"""
        # https://docs.github.com/en/rest/git/blobs#create-a-blob
        path = f"/repos/{github_owner}/{repository_name}/git/blobs"
        payload = {
            "content": content,
            "encoding": encoding,
        }

        response = self.post(path=path, json=payload)
        match response.status_code:
            case 201:
                result = self._parser.parse(response, as_="json")
                return result["sha"]
            case _:
                self._raise_for_status(response, path)
                raise GithubClientFatalError(f"Failed to create blob: {response.text}")

    @GITHUB_RETRY
    def create_tree(
        self,
        github_owner: str,
        repository_name: str,
        base_tree: str,
        tree_entries: list[dict],
    ) -> str:
        """Create a tree object"""
        # https://docs.github.com/en/rest/git/trees#create-a-tree
        path = f"/repos/{github_owner}/{repository_name}/git/trees"
        payload = {
            "base_tree": base_tree,
            "tree": tree_entries,
        }

        response = self.post(path=path, json=payload)
        match response.status_code:
            case 201:
                result = self._parser.parse(response, as_="json")
                return result["sha"]
            case _:
                self._raise_for_status(response, path)
                raise GithubClientFatalError(f"Failed to create tree: {response.text}")

    @GITHUB_RETRY
    def create_commit(
        self,
        github_owner: str,
        repository_name: str,
        message: str,
        tree_sha: str,
        parent_shas: list[str],
    ) -> str:
        """Create a commit object"""
        # https://docs.github.com/en/rest/git/commits#create-a-commit
        path = f"/repos/{github_owner}/{repository_name}/git/commits"
        payload = {
            "message": message,
            "tree": tree_sha,
            "parents": parent_shas,
        }

        response = self.post(path=path, json=payload)
        match response.status_code:
            case 201:
                result = self._parser.parse(response, as_="json")
                return result["sha"]
            case _:
                self._raise_for_status(response, path)
                raise GithubClientFatalError(
                    f"Failed to create commit: {response.text}"
                )

    @GITHUB_RETRY
    def update_ref(
        self,
        github_owner: str,
        repository_name: str,
        ref: str,
        sha: str,
        force: bool = False,
    ) -> bool:
        """Update a reference"""
        # https://docs.github.com/en/rest/git/refs#update-a-reference
        path = f"/repos/{github_owner}/{repository_name}/git/refs/{ref}"
        payload = {
            "sha": sha,
            "force": force,
        }

        response = self.patch(path=path, json=payload)
        match response.status_code:
            case 200:
                return True
            case _:
                self._raise_for_status(response, path)
                return False

    def commit_multiple_files(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
        files: dict[str, str],  # path -> content
        commit_message: str,
    ) -> bool:
        """Commit multiple files in a single commit using Git Data API"""
        try:
            # Get current branch info
            branch_info = self.get_branch(github_owner, repository_name, branch_name)
            if not branch_info:
                raise GithubClientFatalError(f"Branch {branch_name} not found")

            current_commit_sha = branch_info["commit"]["sha"]
            base_tree_sha = branch_info["commit"]["commit"]["tree"]["sha"]

            # Create blobs for all files
            tree_entries = []
            for file_path, content in files.items():
                blob_sha = self.create_blob(github_owner, repository_name, content)
                tree_entries.append(
                    {
                        "path": file_path,
                        "mode": "100644",
                        "type": "blob",
                        "sha": blob_sha,
                    }
                )

            # Create tree
            tree_sha = self.create_tree(
                github_owner, repository_name, base_tree_sha, tree_entries
            )

            # Create commit
            commit_sha = self.create_commit(
                github_owner,
                repository_name,
                commit_message,
                tree_sha,
                [current_commit_sha],
            )

            # Update branch reference
            return self.update_ref(
                github_owner, repository_name, f"heads/{branch_name}", commit_sha
            )

        except Exception as e:
            logger.error(f"Failed to commit multiple files: {e}")
            raise GithubClientFatalError(f"Failed to commit multiple files: {e}") from e

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
                raise GithubClientFatalError(
                    f"Workflow or repository not found (404): {path}"
                )
            case 422:
                logger.error(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
                raise GithubClientFatalError(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
            case _:
                self._raise_for_status(response, path)
                return False

    @GITHUB_RETRY
    def list_workflow_runs(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str | None = None,
        event: str = "workflow_dispatch",
        status: str | None = None,
        per_page: int = 100,
    ) -> dict | None:
        # https://docs.github.com/ja/rest/actions/workflow-runs?apiVersion=2022-11-28#list-workflow-runs-for-a-repository
        path = f"/repos/{github_owner}/{repository_name}/actions/runs"
        params = {"event": event, "per_page": per_page}
        if branch_name:
            params["branch"] = branch_name
        if status:
            params["status"] = status

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
                raise GithubClientFatalError(
                    f"Workflow or repository not found (404): {path}"
                )
            case 422:
                logger.error(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
                raise GithubClientFatalError(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
            case _:
                self._raise_for_status(response, path)
                return None

    @GITHUB_RETRY
    def get_workflow_run_logs(
        self,
        github_owner: str,
        repository_name: str,
        run_id: int,
    ) -> bytes | None:
        """Download workflow run logs"""
        # https://docs.github.com/en/rest/actions/workflow-runs#download-workflow-run-logs
        path = f"/repos/{github_owner}/{repository_name}/actions/runs/{run_id}/logs"

        response = self.get(path=path, allow_redirects=False)
        match response.status_code:
            case 302:
                # Follow redirect to download logs
                log_url = response.headers.get("Location")
                if log_url:
                    import requests

                    log_response = requests.get(log_url)
                    if log_response.status_code == 200:
                        return log_response.content
                return None
            case 404:
                logger.warning(f"Logs not found for run {run_id}")
                return None
            case _:
                self._raise_for_status(response, path)
                return None

    @GITHUB_RETRY
    def list_workflow_run_jobs(
        self,
        github_owner: str,
        repository_name: str,
        run_id: int,
    ) -> dict | None:
        """List jobs for a workflow run"""
        # https://docs.github.com/en/rest/actions/workflow-jobs#list-jobs-for-a-workflow-run
        path = f"/repos/{github_owner}/{repository_name}/actions/runs/{run_id}/jobs"

        response = self.get(path=path)
        match response.status_code:
            case 200:
                return self._parser.parse(response, as_="json")
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
                raise GithubClientFatalError(
                    f"Workflow or repository not found (404): {path}"
                )
            case 422:
                logger.error(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
                raise GithubClientFatalError(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
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

    # --------------------------------------------------
    # Secrets (Actions)
    # --------------------------------------------------

    @GITHUB_RETRY
    def get_repository_public_key(
        self,
        github_owner: str,
        repository_name: str,
    ) -> dict[str, str] | None:
        # https://docs.github.com/en/rest/actions/secrets#get-a-repository-public-key
        path = f"/repos/{github_owner}/{repository_name}/actions/secrets/public-key"

        response = self.get(path=path)
        match response.status_code:
            case 200:
                logger.info(f"Successfully retrieved repository public key: {path}")
                return self._parser.parse(response, as_="json")
            case 404:
                logger.error(f"Repository not found (404): {path}")
                raise GithubClientFatalError(f"Repository not found (404): {path}")
            case _:
                self._raise_for_status(response, path)
                return None

    def _encrypt_secret(self, public_key: str, secret_value: str) -> str:
        public_key_bytes = base64.b64decode(public_key)
        public_key_obj = public.PublicKey(public_key_bytes)
        sealed_box = public.SealedBox(public_key_obj)
        encrypted = sealed_box.encrypt(secret_value.encode("utf-8"))
        return base64.b64encode(encrypted).decode("utf-8")

    @GITHUB_RETRY
    def create_or_update_repository_secret(
        self,
        github_owner: str,
        repository_name: str,
        secret_name: str,
        secret_value: str,
        public_key_info: dict[str, str],
    ) -> bool:
        # https://docs.github.com/en/rest/actions/secrets#create-or-update-a-repository-secret
        encrypted_value = self._encrypt_secret(public_key_info["key"], secret_value)

        path = f"/repos/{github_owner}/{repository_name}/actions/secrets/{secret_name}"
        payload = {
            "encrypted_value": encrypted_value,
            "key_id": public_key_info["key_id"],
        }

        response = self.put(path=path, json=payload)
        match response.status_code:
            case 201 | 204:
                logger.info(
                    f"Successfully created/updated repository secret: {secret_name}"
                )
                return True
            case 404:
                logger.error(f"Repository not found (404): {path}")
                raise GithubClientFatalError(f"Repository not found (404): {path}")
            case _:
                self._raise_for_status(response, path)
                return False

    # --------------------------------------------------
    # Async Branch Methods
    # --------------------------------------------------

    async def aget_branch(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
    ) -> dict | None:
        # https://docs.github.com/ja/rest/branches/branches?apiVersion=2022-11-28#get-a-branch
        # For public repositories, no access token is required.
        path = f"/repos/{github_owner}/{repository_name}/branches/{branch_name}"

        response = await self.aget(path=path)
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

    async def acreate_branch(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
        from_sha: str,
    ) -> bool:
        path = f"/repos/{github_owner}/{repository_name}/git/refs"
        payload = {"ref": f"refs/heads/{branch_name}", "sha": from_sha}

        response = await self.apost(path=path, json=payload)
        match response.status_code:
            case 201:
                logger.info(f"Branch created (201): {branch_name}")
                return True
            case 409:
                logger.error(f"Conflict creating branch (409): {path}")
                raise GithubClientFatalError(f"Conflict creating branch (409): {path}")
            case 422:
                logger.error(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
                raise GithubClientFatalError(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
            case _:
                self._raise_for_status(response, path)
                return False

    # --------------------------------------------------
    # Async GitHub Actions Methods
    # --------------------------------------------------

    async def acreate_workflow_dispatch(
        self,
        github_owner: str,
        repository_name: str,
        workflow_file_name: str,
        ref: str,
        inputs: dict | None = None,
    ) -> bool:
        path = f"/repos/{github_owner}/{repository_name}/actions/workflows/{workflow_file_name}/dispatches"
        json = {"ref": ref, **({"inputs": inputs} if inputs else {})}

        response = await self.apost(path=path, json=json)
        match response.status_code:
            case 204:
                logger.info("Workflow dispatch accepted.")
                return True
            case 403:
                logger.error(f"Access forbidden (403): {path}")
                raise GithubClientFatalError(f"Access forbidden (403): {path}")
            case 404:
                logger.error(f"Workflow or repository not found (404): {path}")
                raise GithubClientFatalError(
                    f"Workflow or repository not found (404): {path}"
                )
            case 422:
                logger.error(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
                raise GithubClientFatalError(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
            case _:
                self._raise_for_status(response, path)
                return False

    async def alist_workflow_runs(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str | None = None,
        event: str = "workflow_dispatch",
        status: str | None = None,
        per_page: int = 100,
    ) -> dict | None:
        path = f"/repos/{github_owner}/{repository_name}/actions/runs"
        params = {"event": event, "per_page": per_page}
        if branch_name:
            params["branch"] = branch_name
        if status:
            params["status"] = status

        response = await self.aget(path=path, params=params)
        match response.status_code:
            case 200:
                logger.info(f"Success (200): {path}")
                return response.json()
            case 403:
                logger.error(f"Access forbidden (403): {path}")
                raise GithubClientFatalError(f"Access forbidden (403): {path}")
            case 404:
                logger.error(f"Workflow or repository not found (404): {path}")
                raise GithubClientFatalError(
                    f"Workflow or repository not found (404): {path}"
                )
            case 422:
                logger.error(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
                raise GithubClientFatalError(
                    f"Validation failed, or the endpoint has been spammed (422): {path}"
                )
            case _:
                self._raise_for_status(response, path)
                return None

    async def aget_repository_content(
        self,
        github_owner: str,
        repository_name: str,
        file_path: str,
        branch_name: str | None = None,
        as_: Literal["json", "bytes"] = "json",
    ) -> dict | bytes:
        path = f"/repos/{github_owner}/{repository_name}/contents/{file_path}"

        headers = None
        if as_ == "bytes":
            headers = {"Accept": "application/vnd.github.raw+json"}

        response = await self.aget(path, params={"ref": branch_name}, headers=headers)
        match response.status_code:
            case 200:
                logger.info(f"Success (200): {path}")
                if as_ == "json":
                    return response.json()
                else:
                    return response.content
            case 404:
                logger.warning(f"Resource not found (404): {path}")
                raise GithubClientFatalError(f"Resource not found (404): {path}")
            case 403:
                logger.error(f"Access forbidden (403): {path}")
                raise GithubClientFatalError(f"Access forbidden (403): {path}")
            case _:
                self._raise_for_status(response, path)

    async def acommit_multiple_files(
        self,
        github_owner: str,
        repository_name: str,
        branch_name: str,
        files: dict[str, str],  # path -> content
        commit_message: str,
    ) -> bool:
        try:
            # Get current branch info
            branch_info = await self.aget_branch(
                github_owner, repository_name, branch_name
            )
            if not branch_info:
                raise GithubClientFatalError(f"Branch {branch_name} not found")

            current_commit_sha = branch_info["commit"]["sha"]
            base_tree_sha = branch_info["commit"]["commit"]["tree"]["sha"]

            # Create blobs for all files
            blob_tasks = []
            for _, content in files.items():
                blob_tasks.append(
                    self._acreate_blob(github_owner, repository_name, content)
                )

            blob_shas = await asyncio.gather(*blob_tasks)

            # Create tree entries
            tree_entries = []
            for i, (file_path, _) in enumerate(files.items()):
                tree_entries.append(
                    {
                        "path": file_path,
                        "mode": "100644",
                        "type": "blob",
                        "sha": blob_shas[i],
                    }
                )

            # Create tree
            tree_sha = await self._acreate_tree(
                github_owner, repository_name, base_tree_sha, tree_entries
            )

            # Create commit
            commit_sha = await self._acreate_commit(
                github_owner,
                repository_name,
                commit_message,
                tree_sha,
                [current_commit_sha],
            )

            # Update branch reference
            return await self._aupdate_ref(
                github_owner, repository_name, f"heads/{branch_name}", commit_sha
            )

        except Exception as e:
            logger.error(f"Failed to commit multiple files: {e}")
            raise GithubClientFatalError(f"Failed to commit multiple files: {e}") from e

    async def _acreate_blob(
        self,
        github_owner: str,
        repository_name: str,
        content: str,
        encoding: str = "utf-8",
    ) -> str:
        path = f"/repos/{github_owner}/{repository_name}/git/blobs"
        payload = {
            "content": content,
            "encoding": encoding,
        }

        response = await self.apost(path=path, json=payload)
        match response.status_code:
            case 201:
                result = response.json()
                return result["sha"]
            case _:
                self._raise_for_status(response, path)
                raise GithubClientFatalError(f"Failed to create blob: {response.text}")

    async def _acreate_tree(
        self,
        github_owner: str,
        repository_name: str,
        base_tree: str,
        tree_entries: list[dict],
    ) -> str:
        path = f"/repos/{github_owner}/{repository_name}/git/trees"
        payload = {
            "base_tree": base_tree,
            "tree": tree_entries,
        }

        response = await self.apost(path=path, json=payload)
        match response.status_code:
            case 201:
                result = response.json()
                return result["sha"]
            case _:
                self._raise_for_status(response, path)
                raise GithubClientFatalError(f"Failed to create tree: {response.text}")

    async def _acreate_commit(
        self,
        github_owner: str,
        repository_name: str,
        message: str,
        tree_sha: str,
        parent_shas: list[str],
    ) -> str:
        path = f"/repos/{github_owner}/{repository_name}/git/commits"
        payload = {
            "message": message,
            "tree": tree_sha,
            "parents": parent_shas,
        }

        response = await self.apost(path=path, json=payload)
        match response.status_code:
            case 201:
                result = response.json()
                return result["sha"]
            case _:
                self._raise_for_status(response, path)
                raise GithubClientFatalError(
                    f"Failed to create commit: {response.text}"
                )

    async def _aupdate_ref(
        self,
        github_owner: str,
        repository_name: str,
        ref: str,
        sha: str,
        force: bool = False,
    ) -> bool:
        path = f"/repos/{github_owner}/{repository_name}/git/refs/{ref}"
        payload = {
            "sha": sha,
            "force": force,
        }

        response = await self.apatch(path=path, json=payload)
        match response.status_code:
            case 200:
                return True
            case _:
                self._raise_for_status(response, path)
                return False
