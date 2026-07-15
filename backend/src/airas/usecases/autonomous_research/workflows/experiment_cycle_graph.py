"""Experiment Cycle Graph

Orchestrates the full iterative experiment lifecycle:
  1. Code Generation → Fetch Run IDs → Sanity Check → Fetch Experiment Code
  2. Execute experiment (pilot) → Visualization → Fetch Results → Analyze
  3. Record cycle → Decide next action
  4. Based on decision:
     - scale_up:  Re-execute at full scale on a new stage branch
     - redesign:  Create next cycle branch → Refine design → Back to step 1
     - complete:  Return experiment_history
     - abort:     Return experiment_history

Branch structure (base_branch = e.g. "main"):
  {base_branch}                         — final deliverables (PDF, ResearchHistory)
  {base_branch}-{n}-pilot-{run_id}      — pilot-stage execution branches
  {base_branch}-{n}-full-{run_id}       — full-stage execution branches
  where {n} is the cycle number (1, 2, ...)
"""

import logging
from typing import Any

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experiment_history import (
    ExperimentCycle,
    ExperimentCycleAction,
    ExperimentCycleDecision,
    ExperimentHistory,
    RunStage,
)
from airas.core.types.experimental_analysis import ExperimentalAnalysis
from airas.core.types.experimental_design import ComputeEnvironment, ExperimentalDesign
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.github import (
    GitHubActionsAgent,
    GitHubConfig,
)
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.runner import ExperimentRunnerConfig
from airas.core.types.wandb import WandbConfig
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.usecases.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentLLMMapping,
    AnalyzeExperimentSubgraph,
)
from airas.usecases.analyzers.decide_experiment_cycle_subgraph.decide_experiment_cycle_subgraph import (
    DecideExperimentCycleLLMMapping,
    DecideExperimentCycleSubgraph,
)
from airas.usecases.autonomous_research.workflows.code_generation_graph import (
    CodeGenerationGraph,
    CodeGenerationGraphLLMMapping,
)
from airas.usecases.autonomous_research.workflows.experiment_execution_graph import (
    ExperimentExecutionGraph,
)
from airas.usecases.autonomous_research.workflows.sanity_check_graph import (
    SanityCheckGraph,
)
from airas.usecases.autonomous_research.workflows.visualization_graph import (
    VisualizationGraph,
)
from airas.usecases.executors.dispatch_experiment_validation_subgraph.dispatch_experiment_validation_subgraph import (
    DispatchExperimentValidationLLMMapping,
)
from airas.usecases.executors.fetch_experiment_code_subgraph.fetch_experiment_code_subgraph import (
    FetchExperimentCodeSubgraph,
)
from airas.usecases.executors.fetch_experiment_results_subgraph.fetch_experiment_results_subgraph import (
    FetchExperimentResultsSubgraph,
)
from airas.usecases.executors.fetch_run_ids_subgraph.fetch_run_ids_subgraph import (
    FetchRunIdsSubgraph,
)
from airas.usecases.generators.refine_experimental_design_subgraph.refine_experimental_design_subgraph import (
    RefineExperimentalDesignLLMMapping,
    RefineExperimentalDesignSubgraph,
)
from airas.usecases.github.create_branch_subgraph import CreateBranchSubgraph

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("experiment_cycle_graph")(f)  # noqa: E731

_STANDARD_WORKFLOW_RECURSION_LIMIT = 50000
_MAX_EXPERIMENT_CYCLES = 6
_REGENERATOR_PROMPT_PATH = ".github/prompts/run_code_regenerator.md"


class WorkflowExecutionError(Exception):
    pass


# ---------------------------------------------------------------------------
# LLM Mapping
# ---------------------------------------------------------------------------
class ExperimentCycleGraphLLMMapping(BaseModel):
    code_generation: CodeGenerationGraphLLMMapping | None = None
    dispatch_experiment_validation: DispatchExperimentValidationLLMMapping | None = None
    analyze_experiment: AnalyzeExperimentLLMMapping | None = None
    decide_experiment_cycle: DecideExperimentCycleLLMMapping | None = None
    refine_experimental_design: RefineExperimentalDesignLLMMapping | None = None


# ---------------------------------------------------------------------------
# State
# ---------------------------------------------------------------------------
class ExperimentCycleGraphInputState(TypedDict):
    github_config: GitHubConfig
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    research_topic: str


class ExperimentCycleGraphOutputState(ExecutionTimeState):
    experiment_history: ExperimentHistory
    experiment_code: ExperimentCode


class ExperimentCycleGraphState(
    ExperimentCycleGraphInputState,
    ExperimentCycleGraphOutputState,
    total=False,
):
    base_github_config: GitHubConfig
    run_ids: list[str]
    current_run_stage: RunStage
    stage_github_config: GitHubConfig
    experimental_results: ExperimentalResults
    experimental_analysis: ExperimentalAnalysis
    experiment_cycle_decision: ExperimentCycleDecision
    cycle_count: int


# ---------------------------------------------------------------------------
# Graph
# ---------------------------------------------------------------------------
class ExperimentCycleGraph:
    def __init__(
        self,
        github_client: GithubClient,
        langchain_client: LangChainClient,
        runner_config: ExperimentRunnerConfig,
        wandb_config: WandbConfig,
        compute_environment: ComputeEnvironment,
        github_actions_agent: GitHubActionsAgent,
        num_experiment_models: int = 2,
        num_experiment_datasets: int = 2,
        num_comparison_methods: int = 2,
        llm_mapping: ExperimentCycleGraphLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.langchain_client = langchain_client
        self.runner_config = runner_config
        self.wandb_config = wandb_config
        self.compute_environment = compute_environment
        self.github_actions_agent = github_actions_agent
        self.num_experiment_models = num_experiment_models
        self.num_experiment_datasets = num_experiment_datasets
        self.num_comparison_methods = num_comparison_methods
        self.llm_mapping = llm_mapping or ExperimentCycleGraphLLMMapping()

    # =======================================================================
    # Code Generation Pipeline (shared by initial and redesign paths)
    # =======================================================================
    @record_execution_time
    async def _initialize(self, state: ExperimentCycleGraphState) -> dict[str, Any]:
        logger.info("=== Experiment Cycle Graph: Initialize ===")
        github_config = state["github_config"]
        cycle_count = 1
        cycle_branch_name = f"{github_config.branch_name}-{cycle_count}"

        result = (
            await CreateBranchSubgraph(
                github_client=self.github_client,
                new_branch_name=cycle_branch_name,
            )
            .build_graph()
            .ainvoke({"github_config": github_config})
        )

        return {
            "experiment_history": ExperimentHistory(),
            "base_github_config": github_config,
            "github_config": result["new_github_config"],
            "current_run_stage": RunStage.PILOT,
            "cycle_count": cycle_count,
        }

    @record_execution_time
    async def _run_code_generation(
        self, state: ExperimentCycleGraphState
    ) -> dict[str, Any]:
        cycle_count = state.get("cycle_count", 1)
        prompt_path = _REGENERATOR_PROMPT_PATH if cycle_count > 1 else None
        logger.info(
            f"=== Run Code Generation (prompt_path={prompt_path or 'default'}) ==="
        )
        await (
            CodeGenerationGraph(
                github_client=self.github_client,
                wandb_config=self.wandb_config,
                github_actions_agent=self.github_actions_agent,
                prompt_path=prompt_path,
                llm_mapping=self.llm_mapping.code_generation,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "research_topic": state.get("research_topic", ""),
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                }
            )
        )
        return {}

    @record_execution_time
    async def _fetch_run_ids(
        self, state: ExperimentCycleGraphState
    ) -> dict[str, list[str]]:
        logger.info("=== Fetch Run IDs ===")
        result = (
            await FetchRunIdsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        run_ids = result["run_ids"]
        if not run_ids:
            raise WorkflowExecutionError("No run IDs found after code generation")

        logger.info(f"Fetched {len(run_ids)} run IDs: {run_ids}")
        return {"run_ids": run_ids}

    @record_execution_time
    async def _run_sanity_check(
        self, state: ExperimentCycleGraphState
    ) -> dict[str, Any]:
        logger.info("=== Run Sanity Check ===")
        await (
            SanityCheckGraph(
                github_client=self.github_client,
                runner_config=self.runner_config,
                wandb_config=self.wandb_config,
                github_actions_agent=self.github_actions_agent,
                llm_mapping=self.llm_mapping.dispatch_experiment_validation,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "run_ids": state["run_ids"],
                    "research_topic": state.get("research_topic", ""),
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                },
                {"recursion_limit": _STANDARD_WORKFLOW_RECURSION_LIMIT},
            )
        )
        return {}

    @record_execution_time
    async def _fetch_experiment_code(
        self, state: ExperimentCycleGraphState
    ) -> dict[str, ExperimentCode]:
        logger.info("=== Fetch Experiment Code ===")
        result = (
            await FetchExperimentCodeSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )
        return {"experiment_code": result["experiment_code"]}

    # =======================================================================
    # Experiment Execution Pipeline
    # =======================================================================
    @record_execution_time
    async def _run_experiment(self, state: ExperimentCycleGraphState) -> dict[str, Any]:
        cycle_count = state.get("cycle_count", 1)
        run_stage = state.get("current_run_stage", RunStage.PILOT)
        github_config = state["github_config"]
        logger.info(
            f"=== Execute Experiment (cycle={cycle_count}, stage={run_stage.value}) ==="
        )

        # Create a stage-specific branch: {branch_name}-{stage}
        stage_branch_name = f"{github_config.branch_name}-{run_stage.value}"
        result = (
            await CreateBranchSubgraph(
                github_client=self.github_client,
                new_branch_name=stage_branch_name,
            )
            .build_graph()
            .ainvoke({"github_config": github_config})
        )
        stage_github_config = result["new_github_config"]

        await (
            ExperimentExecutionGraph(
                github_client=self.github_client,
                runner_config=self.runner_config,
                wandb_config=self.wandb_config,
                github_actions_agent=self.github_actions_agent,
                run_stage=run_stage,
                llm_mapping=self.llm_mapping.dispatch_experiment_validation,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": stage_github_config,
                    "run_ids": state["run_ids"],
                    "research_topic": state.get("research_topic", ""),
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                }
            )
        )
        return {"stage_github_config": stage_github_config}

    @record_execution_time
    async def _run_visualization(
        self, state: ExperimentCycleGraphState
    ) -> dict[str, Any]:
        stage_config = state["stage_github_config"]
        logger.info("=== Run Visualization ===")
        await (
            VisualizationGraph(
                github_client=self.github_client,
                wandb_config=self.wandb_config,
                github_actions_agent=self.github_actions_agent,
                llm_mapping=self.llm_mapping.dispatch_experiment_validation,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": stage_config,
                    "run_ids": state["run_ids"],
                    "research_topic": state.get("research_topic", ""),
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                },
                {"recursion_limit": _STANDARD_WORKFLOW_RECURSION_LIMIT},
            )
        )
        return {}

    @record_execution_time
    async def _fetch_experiment_results(
        self, state: ExperimentCycleGraphState
    ) -> dict[str, ExperimentalResults]:
        stage_config = state["stage_github_config"]
        logger.info("=== Fetch Experiment Results ===")
        result = (
            await FetchExperimentResultsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke({"github_config": stage_config})
        )
        return {"experimental_results": result["experimental_results"]}

    # =======================================================================
    # Analysis & Decision
    # =======================================================================
    @record_execution_time
    async def _analyze_experiment(
        self, state: ExperimentCycleGraphState
    ) -> dict[str, ExperimentalAnalysis]:
        logger.info("=== Analyze Experiment ===")
        result = (
            await AnalyzeExperimentSubgraph(
                langchain_client=self.langchain_client,
                llm_mapping=self.llm_mapping.analyze_experiment,
            )
            .build_graph()
            .ainvoke(
                {
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                    "experiment_code": state["experiment_code"],
                    "experimental_results": state["experimental_results"],
                }
            )
        )
        return {"experimental_analysis": result["experimental_analysis"]}

    @record_execution_time
    def _record_cycle(
        self, state: ExperimentCycleGraphState
    ) -> dict[str, ExperimentHistory]:
        logger.info("=== Record Experiment Cycle ===")
        history = state.get("experiment_history", ExperimentHistory())

        cycle = ExperimentCycle(
            experimental_design=state["experimental_design"],
            run_stage=state.get("current_run_stage", RunStage.PILOT),
            experimental_results=state.get("experimental_results"),
            experimental_analysis=state.get("experimental_analysis"),
        )
        history.cycles.append(cycle)

        logger.info(
            f"Recorded cycle {len(history.cycles)} (stage={cycle.run_stage.value})"
        )
        return {"experiment_history": history}

    @record_execution_time
    async def _decide_next_action(
        self, state: ExperimentCycleGraphState
    ) -> dict[str, Any]:
        logger.info("=== Decide Next Action ===")
        result = (
            await DecideExperimentCycleSubgraph(
                langchain_client=self.langchain_client,
                llm_mapping=self.llm_mapping.decide_experiment_cycle,
            )
            .build_graph()
            .ainvoke(
                {
                    "research_hypothesis": state["research_hypothesis"],
                    "experiment_history": state.get(
                        "experiment_history", ExperimentHistory()
                    ),
                }
            )
        )
        decision = result["experiment_cycle_decision"]

        # Attach decision to the last cycle
        history = state.get("experiment_history", ExperimentHistory())
        if history.cycles:
            history.cycles[-1].decision = decision

        logger.info(f"Decision: {decision.action.value} — {decision.reasoning}")
        return {
            "experiment_cycle_decision": decision,
            "experiment_history": history,
        }

    # =======================================================================
    # Routing
    # =======================================================================
    def _route_after_decision(self, state: ExperimentCycleGraphState) -> str:
        decision = state["experiment_cycle_decision"]
        cycle_count = state.get("cycle_count", 1)

        if cycle_count >= _MAX_EXPERIMENT_CYCLES:
            logger.warning(
                f"Maximum experiment cycles ({_MAX_EXPERIMENT_CYCLES}) reached. "
                f"Forcing completion."
            )
            if decision.action != ExperimentCycleAction.COMPLETE:
                forced_reason = (
                    f"{decision.reasoning}\n\n[System] Maximum experiment cycles "
                    f"({_MAX_EXPERIMENT_CYCLES}) reached. Forcing completion."
                    if decision.reasoning
                    else f"[System] Maximum experiment cycles ({_MAX_EXPERIMENT_CYCLES}) reached. Forcing completion."
                )
                decision.action = ExperimentCycleAction.COMPLETE
                decision.reasoning = forced_reason
            return "complete"

        if decision.action == ExperimentCycleAction.SCALE_UP:
            return "scale_up"
        elif decision.action == ExperimentCycleAction.REDESIGN:
            return "redesign"
        elif decision.action == ExperimentCycleAction.COMPLETE:
            return "complete"
        elif decision.action == ExperimentCycleAction.ABORT:
            return "abort"
        else:
            logger.error(f"Unknown action: {decision.action}")
            return "abort"

    # =======================================================================
    # Scale Up: same run_ids, stage=full (branch created in _run_experiment)
    # =======================================================================
    @record_execution_time
    def _prepare_scale_up(self, state: ExperimentCycleGraphState) -> dict[str, Any]:
        logger.info("=== Prepare Scale Up (pilot → full) ===")
        return {
            "current_run_stage": RunStage.FULL,
        }

    # =======================================================================
    # Redesign: new cycle branch → refine design → code gen → sanity → loop
    # =======================================================================
    @record_execution_time
    async def _create_next_cycle_branch(
        self, state: ExperimentCycleGraphState
    ) -> dict[str, Any]:
        cycle_count = state.get("cycle_count", 1) + 1
        base_config = state["base_github_config"]
        new_branch_name = f"{base_config.branch_name}-{cycle_count}"

        logger.info(f"=== Create Next Cycle Branch: {new_branch_name} ===")

        result = (
            await CreateBranchSubgraph(
                github_client=self.github_client,
                new_branch_name=new_branch_name,
            )
            .build_graph()
            .ainvoke({"github_config": base_config})
        )

        return {
            "github_config": result["new_github_config"],
            "current_run_stage": RunStage.PILOT,
            "cycle_count": cycle_count,
        }

    @record_execution_time
    async def _refine_experimental_design(
        self, state: ExperimentCycleGraphState
    ) -> dict[str, ExperimentalDesign]:
        decision = state["experiment_cycle_decision"]
        design_instruction = decision.design_instruction or decision.reasoning

        logger.info(f"=== Refine Experimental Design: {design_instruction} ===")

        result = (
            await RefineExperimentalDesignSubgraph(
                langchain_client=self.langchain_client,
                compute_environment=self.compute_environment,
                num_models_to_use=self.num_experiment_models,
                num_datasets_to_use=self.num_experiment_datasets,
                num_comparative_methods=self.num_comparison_methods,
                llm_mapping=self.llm_mapping.refine_experimental_design,
            )
            .build_graph()
            .ainvoke(
                {
                    "research_hypothesis": state["research_hypothesis"],
                    "experiment_history": state.get(
                        "experiment_history", ExperimentHistory()
                    ),
                    "design_instruction": design_instruction,
                }
            )
        )
        return {"experimental_design": result["experimental_design"]}

    # =======================================================================
    # Finalize
    # =======================================================================
    @record_execution_time
    def _finalize(self, state: ExperimentCycleGraphState) -> dict[str, Any]:
        history = state.get("experiment_history", ExperimentHistory())
        decision = state.get("experiment_cycle_decision")
        action = decision.action.value if decision else "unknown"
        logger.info(
            f"=== Experiment Cycle Complete: {len(history.cycles)} cycles, "
            f"final action={action} ==="
        )
        return {
            "experiment_history": history,
            "experiment_code": state.get("experiment_code"),
        }

    # =======================================================================
    # Build Graph
    # =======================================================================
    def build_graph(self):
        graph_builder = StateGraph(
            ExperimentCycleGraphState,
            input_schema=ExperimentCycleGraphInputState,
            output_schema=ExperimentCycleGraphOutputState,
        )

        # --- Nodes ---
        graph_builder.add_node("initialize", self._initialize)

        # Code generation pipeline (initial + redesign shared entry point)
        graph_builder.add_node("run_code_generation", self._run_code_generation)
        graph_builder.add_node("fetch_run_ids", self._fetch_run_ids)
        graph_builder.add_node("run_sanity_check", self._run_sanity_check)
        graph_builder.add_node("fetch_experiment_code", self._fetch_experiment_code)

        # Experiment execution pipeline
        graph_builder.add_node("run_experiment", self._run_experiment)
        graph_builder.add_node("run_visualization", self._run_visualization)
        graph_builder.add_node(
            "fetch_experiment_results", self._fetch_experiment_results
        )

        # Analysis & decision
        graph_builder.add_node("analyze_experiment", self._analyze_experiment)
        graph_builder.add_node("record_cycle", self._record_cycle)
        graph_builder.add_node("decide_next_action", self._decide_next_action)

        # Scale up
        graph_builder.add_node("prepare_scale_up", self._prepare_scale_up)

        # Redesign
        graph_builder.add_node(
            "create_next_cycle_branch", self._create_next_cycle_branch
        )
        graph_builder.add_node(
            "refine_experimental_design", self._refine_experimental_design
        )

        # Finalize
        graph_builder.add_node("finalize", self._finalize)

        # --- Edges ---
        # Initial: initialize → code gen pipeline
        graph_builder.add_edge(START, "initialize")
        graph_builder.add_edge("initialize", "run_code_generation")

        # Code generation pipeline
        graph_builder.add_edge("run_code_generation", "fetch_run_ids")
        graph_builder.add_edge("fetch_run_ids", "run_sanity_check")
        graph_builder.add_edge("run_sanity_check", "fetch_experiment_code")

        # → Experiment execution pipeline
        graph_builder.add_edge("fetch_experiment_code", "run_experiment")
        graph_builder.add_edge("run_experiment", "run_visualization")
        graph_builder.add_edge("run_visualization", "fetch_experiment_results")

        # → Analysis & decision
        graph_builder.add_edge("fetch_experiment_results", "analyze_experiment")
        graph_builder.add_edge("analyze_experiment", "record_cycle")
        graph_builder.add_edge("record_cycle", "decide_next_action")

        # Decision routing
        graph_builder.add_conditional_edges(
            "decide_next_action",
            self._route_after_decision,
            {
                "scale_up": "prepare_scale_up",
                "redesign": "create_next_cycle_branch",
                "complete": "finalize",
                "abort": "finalize",
            },
        )

        # Scale up → skip code gen, go straight to experiment execution
        graph_builder.add_edge("prepare_scale_up", "run_experiment")

        # Redesign → new cycle → refine design → back to code gen pipeline
        graph_builder.add_edge("create_next_cycle_branch", "refine_experimental_design")
        graph_builder.add_edge("refine_experimental_design", "run_code_generation")

        # Finalize
        graph_builder.add_edge("finalize", END)

        return graph_builder.compile()


if __name__ == "__main__":
    from pathlib import Path
    from unittest.mock import MagicMock

    graph = ExperimentCycleGraph(
        github_client=MagicMock(),
        langchain_client=MagicMock(),
        runner_config=MagicMock(),
        wandb_config=MagicMock(),
        compute_environment=MagicMock(),
        github_actions_agent=MagicMock(),
    )
    png_data = graph.build_graph().get_graph().draw_mermaid_png()
    output_path = Path(__file__).with_suffix(".png")
    output_path.write_bytes(png_data)
    print(f"Saved: {output_path}")
