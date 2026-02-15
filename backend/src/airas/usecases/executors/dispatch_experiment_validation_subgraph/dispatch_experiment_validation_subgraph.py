import logging

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.llm_config import DEFAULT_NODE_LLM_CONFIG, NodeLLMConfig
from airas.core.logging_utils import setup_logging
from airas.core.types.experiment_code import RunStage
from airas.core.types.experimental_design import ExperimentalDesign
from airas.core.types.github import GitHubActionsAgent, GitHubConfig
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.wandb import WandbConfig
from airas.infra.github_client import GithubClient
from airas.usecases.github.nodes.dispatch_workflow import dispatch_workflow

setup_logging()
logger = logging.getLogger(__name__)


def record_execution_time(f):
    return time_node("dispatch_experiment_validation_subgraph")(f)  # noqa: E731


class DispatchExperimentValidationLLMMapping(BaseModel):
    dispatch_experiment_validation: NodeLLMConfig = DEFAULT_NODE_LLM_CONFIG[
        "dispatch_experiment_validation"
    ]


class DispatchExperimentValidationSubgraphInputState(TypedDict, total=False):
    github_config: GitHubConfig
    research_topic: str
    run_id: str | None
    workflow_run_id: int
    run_stage: RunStage
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    wandb_config: WandbConfig
    github_actions_agent: GitHubActionsAgent


class DispatchExperimentValidationSubgraphOutputState(ExecutionTimeState):
    dispatched: bool


class DispatchExperimentValidationSubgraphState(
    DispatchExperimentValidationSubgraphInputState,
    DispatchExperimentValidationSubgraphOutputState,
    total=False,
):
    pass


class DispatchExperimentValidationSubgraph:
    def __init__(
        self,
        github_client: GithubClient,
        workflow_file: str = "run_experiment_validator.yml",
        llm_mapping: DispatchExperimentValidationLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.workflow_file = workflow_file
        self.llm_mapping = llm_mapping or DispatchExperimentValidationLLMMapping()

    @record_execution_time
    async def _dispatch_experiment_validation(
        self, state: DispatchExperimentValidationSubgraphState
    ) -> dict[str, bool]:
        github_config = state["github_config"]
        research_topic = state["research_topic"]
        run_id = state.get("run_id")
        workflow_run_id = state["workflow_run_id"]
        run_stage = state["run_stage"]
        research_hypothesis = state["research_hypothesis"]
        experimental_design = state["experimental_design"]
        wandb_config = state["wandb_config"]
        github_actions_agent = state["github_actions_agent"]

        if run_id:
            logger.info(
                f"Dispatching experiment validation for run_id={run_id}, stage={run_stage} on branch '{github_config.branch_name}'"
            )
        else:
            logger.info(
                f"Dispatching experiment validation for stage={run_stage} on branch '{github_config.branch_name}' (no specific run_id)"
            )

        inputs = {
            "branch_name": github_config.branch_name,
            "research_topic": research_topic,
            "workflow_run_id": str(workflow_run_id),
            "run_stage": run_stage,
            "research_hypothesis": research_hypothesis.model_dump_json(),
            "experimental_design": experimental_design.model_dump_json(),
            "wandb_config": wandb_config.model_dump_json(),
            "github_actions_agent": github_actions_agent,
            "model_name": self.llm_mapping.dispatch_experiment_validation.llm_name,
        }

        # Only add run_id if it's provided
        if run_id:
            inputs["run_id"] = run_id

        success = await dispatch_workflow(
            self.github_client,
            github_config.github_owner,
            github_config.repository_name,
            github_config.branch_name,
            self.workflow_file,
            inputs,
        )

        if success:
            if run_id:
                logger.info(
                    f"Experiment validation dispatch successful for run_id={run_id}"
                )
            else:
                logger.info(
                    f"Experiment validation dispatch successful for stage={run_stage}"
                )
        else:
            if run_id:
                logger.error(
                    f"Experiment validation dispatch failed for run_id={run_id}"
                )
            else:
                logger.error(
                    f"Experiment validation dispatch failed for stage={run_stage}"
                )

        return {"dispatched": success}

    def build_graph(self):
        graph_builder = StateGraph(
            DispatchExperimentValidationSubgraphState,
            input_schema=DispatchExperimentValidationSubgraphInputState,
            output_schema=DispatchExperimentValidationSubgraphOutputState,
        )

        graph_builder.add_node(
            "dispatch_experiment_validation", self._dispatch_experiment_validation
        )

        graph_builder.add_edge(START, "dispatch_experiment_validation")
        graph_builder.add_edge("dispatch_experiment_validation", END)

        return graph_builder.compile()
