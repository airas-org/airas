import base64
import json
import logging
import os
import time
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Protocol, TypeVar

from langgraph.graph import END, START, StateGraph
from langgraph.graph.graph import CompiledGraph
from typing_extensions import TypedDict

from airas.utils.api_client.github_client import GithubClient
from airas.utils.check_api_key import check_api_key
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


class ExtraFileConfig(TypedDict):
    upload_branch: str
    upload_dir: str
    local_file_paths: list[str]

class GithubGraphWrapper:
    def __init__(
        self,
        subgraph: CompiledGraph,
        input_state: Any,
        output_state: Any,
        github_repository: str,
        branch_name: str,
        research_file_path: str = ".research/research_history.json",
        extra_files: list[ExtraFileConfig] | None = None,
        public_branch: str = "gh-pages",
        client: GithubClient | None = None,
        wait_seconds: float = 3.0, 
    ):
        self.subgraph = subgraph
        self.subgraph_name = getattr(
            subgraph, "__source_subgraph_name__", "subgraph"
        ).lower()
        self.input_state_keys = (
            list(input_state.__annotations__.keys()) if input_state else []
        )
        self.output_state_keys = (
            list(output_state.__annotations__.keys()) if output_state else []
        )
        try:
            self.github_owner, self.repository_name = github_repository.split("/", 1)
        except ValueError as e:
            raise ValueError("Repo string must be in the format 'owner/repository'") from e
        self.branch_name = branch_name
        self.research_file_path = research_file_path
        self.extra_files = extra_files
        self.public_branch = public_branch
        self.wait_seconds = wait_seconds

        check_api_key(github_personal_access_token_check=True)
        self.client = client or GithubClient()

        self._validate_repo_and_branch()

    @staticmethod
    def _encode_content(value: Any) -> bytes:
        match value:
            case bytes():
                return value
            case str() if os.path.isfile(value):
                with open(value, "rb") as f:
                    return f.read()
            case str():
                return value.encode("utf-8")
            case _:
                return json.dumps(value, indent=2, ensure_ascii=False).encode("utf-8")

    @staticmethod
    def _deep_merge(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
        result = deepcopy(old)
        for k, v in new.items():
            if k in result and isinstance(result[k], dict) and isinstance(v, dict):
                result[k] = GithubGraphWrapper._deep_merge(result[k], v)
            else:
                result[k] = deepcopy(v)
        return result


    def _validate_repo_and_branch(self) -> None:
        if not self.client.get_repository(self.github_owner, self.repository_name):
            raise ValueError(f"GitHub repository not found: '{self.github_owner}/{self.repository_name}'")
        if not self.client.get_branch(self.github_owner, self.repository_name, self.branch_name):
            raise ValueError(f"GitHub branch not found: '{self.github_owner}/{self.repository_name}/{self.branch_name}'")

    def download_state(self) -> dict[str, Any]:
        logger.info(f"[GitHub I/O] Downloading state from '{self.branch_name}:{self.research_file_path}'")
        try:
            data = self.client.get_repository_content(
                github_owner=self.github_owner,
                repository_name=self.repository_name,
                file_path=self.research_file_path,
                branch_name=self.branch_name,
            )
            file_bytes = base64.b64decode(data.get("content"))
            return json.loads(file_bytes.decode("utf-8")) if file_bytes else {}
        except FileNotFoundError:
            logger.warning("State file not found - starting with empty state")
            return {}
        except Exception as e:
            raise ValueError(f"Unable to decode JSON from {self.research_file_path}: {e}") from e

    def _upload_state(self, branch_name: str, state: dict[str, Any]) -> bool:
        logger.info(f"[GitHub I/O] Uploading state to '{branch_name}:{self.research_file_path}'")
        return self.client.commit_file_bytes(
            github_owner=self.github_owner,
            repository_name=self.repository_name,
            branch_name=branch_name,
            file_path=self.research_file_path,
            file_content=self._encode_content(state),
            commit_message=f"Update by subgraph: {self.subgraph_name}",
        )
    
    def _upload_extra_files(self, formatted_extra: list[ExtraFileConfig], commit_message: str) -> bool:
        all_ok = True
        for cfg in formatted_extra:
            for file_path in cfg["local_file_paths"]:
                try:
                    with open(file_path, "rb") as fp:
                        file_bytes = fp.read()
                    ok = self.client.commit_file_bytes(
                        github_owner=self.github_owner,
                        repository_name=self.repository_name,
                        branch_name=cfg["upload_branch"],
                        file_path=os.path.join(cfg["upload_dir"], os.path.basename(file_path)).replace("\\", "/"),
                        file_content=file_bytes,
                        commit_message=commit_message,
                    )
                    all_ok &= ok
                except Exception as e:
                    logger.warning(f"Failed to upload asset '{file_path}': {e}")
                    all_ok = False
        return all_ok

    def _create_child_branch(self) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        new_branch = f"{self.branch_name}-{self.subgraph_name}-{ts}"

        response = self.client.get_branch(self.github_owner, self.repository_name, self.branch_name)
        if response is None:
            logger.error(f"Branch '{self.branch_name}' not found in repository '{self.repository_name}'.")
            raise RuntimeError(f"Branch '{self.branch_name}' not found in repository '{self.repository_name}'.")
        
        sha = response["commit"]["sha"]
        
        self.client.create_branch(self.github_owner, self.repository_name, new_branch, from_sha=sha)
        logger.info(f"[GitHub I/O] Created safety branch '{new_branch}' from '{self.branch_name}'")
        return new_branch

    def _format_extra_files(self, branch_name: str) -> list[ExtraFileConfig] | None:
        if self.extra_files is None:
            return None

        formatted_files = []
        for cfg in self.extra_files:
            tb = cfg["upload_branch"].replace("{branch_name}", branch_name)
            tp = cfg["upload_dir"].replace("{branch_name}", branch_name)
            fps = [fp.replace("{branch_name}", branch_name) for fp in cfg["local_file_paths"]]
            formatted_files.append(
                {
                    "upload_branch": tb,
                    "upload_dir": tp,
                    "local_file_paths": fps,
                }
            )
        return formatted_files

    def _log_public_html_url(self, formatted_extra_files: list[ExtraFileConfig] | None) -> None:
        if not formatted_extra_files:
            return
        for cfg in formatted_extra_files:
            if cfg["upload_branch"].lower() == self.public_branch.lower():
                target_path = cfg["upload_dir"].rstrip("/")
                github_pages_url = f"https://{self.github_owner}.github.io/{self.repository_name}/{target_path}/index.html"
                print(f"Uploaded HTML available at: {github_pages_url} (It may take a few minutes to reflect on GitHub Pages)")
                break

    def _call_api(self) -> None:
        pass

    # @time_node("wrapper", "download_from_github")
    def _download_from_github(self, state: dict[str, Any]) -> dict[str, Any]:
        original_state = self.download_state()
        return {"original_state": original_state, **state}

    def _prepare_branch(self, state: dict[str, Any]) -> dict[str, Any]:
        original_state = state.get("original_state", {})
        user_input_state = {k: v for k, v in state.items() if k != "original_state"}

        branch_name = self.branch_name
        input_conflict = any(k in original_state for k in user_input_state)
        output_conflict = any(key in original_state for key in self.output_state_keys)
        if input_conflict or output_conflict:
            reason = "Input Key conflict" if input_conflict else "Output key conflict"
            branch_name = self._create_child_branch()
            print(f"{reason} detected. Created new branch: {branch_name}")
        else:
            print(f"No key conflict. Using existing branch: {branch_name}")

        return {
            "original_state": original_state,
            "user_input_state": user_input_state,
            "branch_name": branch_name,
        }

    # @time_node("wrapper", "run_subgraph")
    def _run_subgraph(self, state: dict[str, Any]) -> dict[str, Any]:
        original_state = state.get("original_state") or {}
        user_input_state = state.get("user_input_state", state)
        merged_input_state = self._deep_merge(original_state, user_input_state)
        branch_name = state.get("branch_name", self.branch_name)

        state_for_subgraph = {  # NOTE: Corresponds to cases where the original subgraph (CompiledGraph) refers to these internally
            **merged_input_state,
            "github_owner": self.github_owner,
            "repository_name": self.repository_name,
            "branch_name": branch_name,
        }

        missing = [k for k in self.input_state_keys if k not in state_for_subgraph]
        if missing:
            raise ValueError(f"run_subgraph: required keys missing: {missing}")

        output_state = self.subgraph.invoke(state_for_subgraph)
        return {
            "merged_input_state": merged_input_state,
            "output_state": output_state,
            "branch_name": branch_name,
        }

    # @time_node("wrapper", "upload_to_github")
    def _upload_to_github(self, state: dict[str, Any]) -> dict[str, Any]:
        merged_input_state = state.get("merged_input_state", {})
        raw_output_state = state.get("output_state", {})
        branch_name = state.get("branch_name", self.branch_name)

        output_state = {k: raw_output_state[k] for k in self.output_state_keys if k in raw_output_state} # NOTE: Removal of github-related meta information
        state_to_upload = self._deep_merge(merged_input_state, output_state)

        ok_json  = self._upload_state(branch_name, state_to_upload)

        if formatted_extra_files := self._format_extra_files(branch_name):
            ok_extra = self._upload_extra_files(
                formatted_extra_files,
                commit_message=f"Upload assets from subgraph: {self.subgraph_name}",
            )
            github_upload_success = ok_json and ok_extra
        else:
            github_upload_success = ok_json

        logger.info(f"Updated {self.research_file_path} (branch: {branch_name})")
        print(f"Check here：https://github.com/{self.github_owner}/{self.repository_name}/blob/{branch_name}/{self.research_file_path}")
        self._log_public_html_url(formatted_extra_files)

        if self.wait_seconds > 0:
            time.sleep(self.wait_seconds)

        return {
            "github_upload_success": github_upload_success,
            "merged_input_state": merged_input_state,
            "output_state": output_state,
            "branch_name": branch_name,
        }

    def build_graph(self) -> CompiledGraph:
        wrapper = StateGraph(dict[str, Any])
        wrapper.add_node("download_from_github", self._download_from_github)
        wrapper.add_node("prepare_branch", self._prepare_branch)
        wrapper.add_node("run_subgraph", self._run_subgraph)
        wrapper.add_node("upload_to_github", self._upload_to_github)

        wrapper.add_edge(START, "download_from_github")
        wrapper.add_edge("download_from_github", "prepare_branch")
        wrapper.add_edge("prepare_branch", "run_subgraph")
        wrapper.add_edge("run_subgraph", "upload_to_github")
        wrapper.add_edge("upload_to_github", END)
        return wrapper.compile()


class BuildableSubgraph(Protocol):
    def build_graph(self) -> CompiledGraph: ...


T = TypeVar("T", bound=BuildableSubgraph)


# TODO: Add support for subgraph API invocation
def create_wrapped_subgraph(
    subgraph: type[T],
    input_state: type[Any],
    output_state: type[Any],
) -> type:
    class GithubGraphRunner(GithubGraphWrapper):
        def __init__(
            self,
            github_repository: str,
            branch_name: str,
            research_file_path: str = ".research/research_history.json",
            extra_files: list[ExtraFileConfig] | None = None,
            public_branch: str = "gh-pages",
            *args: Any,
            **kwargs: Any,
        ):
            subgraph_instance = subgraph(*args, **kwargs)
            compiled_subgraph = subgraph_instance.build_graph()
            compiled_subgraph.__source_subgraph_name__ = subgraph_instance.__class__.__name__
            super().__init__(
                subgraph=compiled_subgraph,
                input_state=input_state,
                output_state=output_state,
                github_repository=github_repository,
                branch_name=branch_name,
                research_file_path=research_file_path,
                extra_files=extra_files,
                public_branch=public_branch,
            )

        def run(self) -> dict[str, Any]:
            graph = self.build_graph()
            config = {"recursion_limit": 300}  # NOTE:
            result = graph.invoke({}, config=config)
            base = {
                "github_upload_success": result.get("github_upload_success", False),
                "subgraph_name": self.subgraph_name,
                "github_owner": self.github_owner,
                "repository_name": self.repository_name,
                "branch_name": result["branch_name"],
                "research_file_path": self.research_file_path,
                "extra_files": self.extra_files,
            }
            return {
                **base,
                **result.get("merged_input_state", {}),
                **result.get("output_state", {}),
            }

    return GithubGraphRunner
