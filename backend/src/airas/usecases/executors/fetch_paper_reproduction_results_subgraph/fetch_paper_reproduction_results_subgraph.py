import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import NodeLLMConfig, require_llm_mapping
from airas.core.logging_utils import setup_logging
from airas.core.types.github import GitHubConfig
from airas.infra.github_client import GithubClient
from airas.infra.litellm_client import LiteLLMClient
from airas.usecases.executors.fetch_paper_reproduction_results_subgraph.nodes.fetch_reproduction_outputs import (
    fetch_reproduction_outputs,
)
from airas.usecases.executors.fetch_paper_reproduction_results_subgraph.nodes.judge_reproduction import (
    judge_reproduction,
)
from airas.usecases.executors.fetch_paper_reproduction_results_subgraph.nodes.pitfall_check import (
    format_evidence,
    run_pitfall_checklist,
)

setup_logging()
logger = logging.getLogger(__name__)


def record_execution_time(f):
    return time_node("fetch_paper_reproduction_results_subgraph")(f)


class FetchPaperReproductionResultsLLMMapping(BaseModel):
    judge_reproduction: NodeLLMConfig


class FetchPaperReproductionResultsSubgraphInputState(TypedDict):
    github_config: GitHubConfig


class FetchPaperReproductionResultsSubgraphOutputState(ExecutionTimeState):
    result: dict | None
    validation: dict | None
    final_status: dict | None
    repro_md: str | None
    repro_png_base64: str | None


class FetchPaperReproductionResultsSubgraphState(
    FetchPaperReproductionResultsSubgraphInputState,
    FetchPaperReproductionResultsSubgraphOutputState,
    total=False,
):
    # Carried between fetch and validate; not part of the public output.
    main_py: str | None
    run_log: str | None
    paper_txt: str | None


class FetchPaperReproductionResultsSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        litellm_client: LiteLLMClient,
        llm_mapping: FetchPaperReproductionResultsLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.litellm_client = litellm_client
        self.llm_mapping = require_llm_mapping(llm_mapping)

    @record_execution_time
    async def _fetch(self, state: FetchPaperReproductionResultsSubgraphState) -> dict:
        try:
            outputs = await fetch_reproduction_outputs(
                github_client=self.github_client,
                github_config=state["github_config"],
            )
        except Exception as exc:
            logger.warning("Failed to fetch reproduction outputs: %s", exc)
            return {
                "result": None,
                "repro_md": None,
                "repro_png_base64": None,
                "main_py": None,
                "run_log": None,
                "paper_txt": None,
                "final_status": {"status": "failed", "fetch_error": str(exc)},
            }
        return {
            "result": outputs.get("result"),
            "repro_md": outputs.get("repro_md"),
            "repro_png_base64": outputs.get("repro_png_base64"),
            "main_py": outputs.get("main_py"),
            "run_log": outputs.get("run_log"),
            "paper_txt": outputs.get("paper_txt"),
        }

    def _route_after_fetch(
        self, state: FetchPaperReproductionResultsSubgraphState
    ) -> str:
        if state.get("final_status"):
            return END
        return "validate"

    @record_execution_time
    async def _validate(
        self, state: FetchPaperReproductionResultsSubgraphState
    ) -> dict:
        result = state.get("result")
        if not isinstance(result, dict):
            return {
                "validation": None,
                "final_status": {"status": "failed", "run_error": "result_missing"},
            }

        run_error = result.get("error")
        if run_error:
            # Early exit (target_not_found/gpu_required): nothing to validate.
            return {
                "validation": None,
                "final_status": {"status": "failed", "run_error": run_error},
            }

        checklist = run_pitfall_checklist(
            reproduce_code=state.get("main_py"),
            run_log=state.get("run_log"),
            summary=str(result.get("summary", "")),
            repro_md=state.get("repro_md"),
            repro_png_base64=state.get("repro_png_base64"),
        )
        try:
            validation = await judge_reproduction(
                llm_config=self.llm_mapping.judge_reproduction,
                litellm_client=self.litellm_client,
                paper_text=state.get("paper_txt"),
                result=result,
                evidence=format_evidence(checklist),
            )
        except Exception as exc:
            logger.warning("judge_reproduction failed: %s", exc)
            return {
                "validation": None,
                "final_status": {"status": "failed", "validation_error": str(exc)},
            }
        severity = validation.get("severity")
        status = "failed" if severity == "critical" else "passed"
        return {
            "validation": validation,
            "final_status": {
                "status": status,
                "validation_severity": severity,
                "reproduction_level": validation.get("reproduction_level"),
            },
        }

    def build_graph(self):
        graph_builder = StateGraph(
            FetchPaperReproductionResultsSubgraphState,
            input_schema=FetchPaperReproductionResultsSubgraphInputState,
            output_schema=FetchPaperReproductionResultsSubgraphOutputState,
        )
        graph_builder.add_node("fetch", self._fetch)
        graph_builder.add_node("validate", self._validate)
        graph_builder.add_edge(START, "fetch")
        graph_builder.add_conditional_edges("fetch", self._route_after_fetch)
        graph_builder.add_edge("validate", END)
        return graph_builder.compile()
