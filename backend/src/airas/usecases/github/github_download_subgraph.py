"""ResearchHistory transport — kept only until the record replaces it.

TODO: rework against the CI gate. This moves `research_history.json`
through the GitHub contents API, file by file: every upload is a fresh
commit the API composes, and a download reads whatever the branch holds
now. The record cannot be carried that way. The gate judges the pushed
history — it walks every revision of `record.json` to check containment,
and asks whether each run's recorded commit is an ancestor of HEAD — so
what has to reach GitHub is the *local commits themselves*, pushed to the
staging ref and fast-forwarded once the check is green, not a
reconstruction of their contents.

Today nothing here is used for the record: `commit_record_paths`
(`research_record/store.py`) commits locally and the agent pushes with
`git push` from its shell (see `setup-repository` and `publish-paper`).
That leaves the fixed workflow, which has no shell, with no way to
publish the record at all.

So the replacement is a push in `infra/local_git.py` — the same call for
the agent and for a graph node — and this module retires with
`ResearchHistory` itself (also `usecases/autonomous_research/
node_decorators.py::upload_to_github` and `mcp/tools/history.py`).
"""

import logging

from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.core.types.research_history import ResearchHistory
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.github_download import github_download

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("github_download_subgraph")(f)  # noqa: E731


class GithubDownloadInputState(TypedDict):
    github_config: GitHubConfig


class GithubDownloadOutputState(ExecutionTimeState):
    research_history: ResearchHistory


class GithubDownloadSubgraphState(
    GithubDownloadInputState,
    GithubDownloadOutputState,
    total=False,
):
    pass


class GithubDownloadSubgraph:
    def __init__(self, github_client: GithubClient):
        self.research_file_path = ".research/research_history.json"
        self.github_client = github_client

    @record_execution_time
    def _download_history(
        self, state: GithubDownloadSubgraphState
    ) -> dict[str, ResearchHistory]:
        research_history = github_download(
            github_config=state["github_config"],
            github_client=self.github_client,
        )
        return {
            "research_history": research_history,
        }

    def build_graph(self):
        sg = StateGraph(
            GithubDownloadSubgraphState,
            input_schema=GithubDownloadInputState,
            output_schema=GithubDownloadOutputState,
        )
        sg.add_node("download_history", self._download_history)

        sg.add_edge(START, "download_history")
        sg.add_edge("download_history", END)
        return sg.compile()
