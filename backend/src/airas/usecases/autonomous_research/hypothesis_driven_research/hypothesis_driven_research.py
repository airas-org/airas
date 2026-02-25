import logging
from typing import Any
from uuid import UUID

from langgraph.graph import END, START, StateGraph
from pydantic import BaseModel
from typing_extensions import TypedDict

from airas.core.execution_timers import ExecutionTimeState, time_node
from airas.core.logging_utils import setup_logging
from airas.core.types.experiment_code import ExperimentCode
from airas.core.types.experimental_analysis import ExperimentalAnalysis
from airas.core.types.experimental_design import ExperimentalDesign, RunnerConfig
from airas.core.types.experimental_results import ExperimentalResults
from airas.core.types.github import (
    GitHubActionsAgent,
    GitHubConfig,
)
from airas.core.types.latex import LATEX_TEMPLATE_NAME
from airas.core.types.paper import PaperContent
from airas.core.types.research_history import ResearchHistory
from airas.core.types.research_hypothesis import ResearchHypothesis
from airas.core.types.research_study import ResearchStudy
from airas.core.types.wandb import WandbConfig
from airas.core.utils import to_dict_deep
from airas.infra.db.models.e2e import Status, StepType
from airas.infra.github_client import GithubClient
from airas.infra.langchain_client import LangChainClient
from airas.usecases.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentLLMMapping,
    AnalyzeExperimentSubgraph,
)
from airas.usecases.autonomous_research.e2e_research_service_protocol import (
    E2EResearchServiceProtocol,
)
from airas.usecases.autonomous_research.node_decorators import (
    save_to_db,
    upload_to_github,
)
from airas.usecases.autonomous_research.workflows.code_generation_graph import (
    CodeGenerationGraph,
    CodeGenerationGraphLLMMapping,
)
from airas.usecases.autonomous_research.workflows.latex_graph import (
    LaTeXGraph,
    LaTeXGraphLLMMapping,
)
from airas.usecases.autonomous_research.workflows.main_experiment_graph import (
    MainExperimentGraph,
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
from airas.usecases.generators.generate_experimental_design_subgraph.generate_experimental_design_subgraph import (
    GenerateExperimentalDesignLLMMapping,
    GenerateExperimentalDesignSubgraph,
)
from airas.usecases.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)
from airas.usecases.github.push_github_subgraph.push_github_subgraph import (
    PushGitHubSubgraph,
)
from airas.usecases.github.set_github_actions_secrets_subgraph.set_github_actions_secrets_subgraph import (
    SetGithubActionsSecretsSubgraph,
)
from airas.usecases.writers.generate_bibfile_subgraph.generate_bibfile_subgraph import (
    GenerateBibfileSubgraph,
)
from airas.usecases.writers.write_subgraph.write_subgraph import (
    WriteLLMMapping,
    WriteSubgraph,
)

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("execute_e2e")(f)  # noqa: E731

_STANDARD_WORKFLOW_RECURSION_LIMIT = 50000


class HypothesisDrivenResearchLLMMapping(BaseModel):
    generate_experimental_design: GenerateExperimentalDesignLLMMapping | None = None
    code_generation: CodeGenerationGraphLLMMapping | None = None
    dispatch_experiment_validation: DispatchExperimentValidationLLMMapping | None = None
    analyze_experiment: AnalyzeExperimentLLMMapping | None = None
    write: WriteLLMMapping | None = None
    latex: LaTeXGraphLLMMapping | None = None


class HypothesisDrivenResearchInputState(TypedDict):
    task_id: str | UUID
    github_config: GitHubConfig
    research_hypothesis: ResearchHypothesis
    research_topic: str  # Context label for downstream LLM nodes; can be empty string


class HypothesisDrivenResearchOutputState(ExecutionTimeState):
    status: str
    research_history: ResearchHistory | None


class HypothesisDrivenResearchState(
    HypothesisDrivenResearchInputState,
    HypothesisDrivenResearchOutputState,
    total=False,
):
    current_step: StepType
    research_study_list: list[ResearchStudy]
    experimental_design: ExperimentalDesign
    experiment_code: ExperimentCode
    experimental_results: ExperimentalResults
    experimental_analysis: ExperimentalAnalysis
    references_bib: str
    paper_content: PaperContent
    paper_url: str | None
    is_repository_ready: bool
    is_branch_ready: bool
    secrets_set: bool
    run_ids: list[str]
    is_upload_successful: bool


class HypothesisDrivenResearch:
    def __init__(
        self,
        github_client: GithubClient,
        langchain_client: LangChainClient,
        e2e_service: E2EResearchServiceProtocol,
        runner_config: RunnerConfig,
        wandb_config: WandbConfig,
        task_id: UUID,
        created_by: UUID,
        is_github_repo_private: bool = False,
        num_experiment_models: int = 1,
        num_experiment_datasets: int = 1,
        num_comparison_methods: int = 1,
        paper_content_refinement_iterations: int = 2,
        github_actions_agent: GitHubActionsAgent = "open_code",
        latex_template_name: LATEX_TEMPLATE_NAME = "mdpi",
        llm_mapping: HypothesisDrivenResearchLLMMapping | None = None,
    ):
        self.github_client = github_client
        self.langchain_client = langchain_client
        self.e2e_service = e2e_service
        self.runner_config = runner_config
        self.wandb_config = wandb_config
        self.task_id = task_id
        self.created_by = created_by
        self.is_github_repo_private = is_github_repo_private
        self.num_experiment_models = num_experiment_models
        self.num_experiment_datasets = num_experiment_datasets
        self.num_comparison_methods = num_comparison_methods
        self.paper_content_refinement_iterations = paper_content_refinement_iterations
        self.latex_template_name = latex_template_name
        self.github_actions_agent = github_actions_agent
        self.llm_mapping = llm_mapping or HypothesisDrivenResearchLLMMapping()

    @record_execution_time
    def _create_record(self, state: HypothesisDrivenResearchState) -> dict[str, Any]:
        github_config = state["github_config"]
        github_url = (
            f"https://github.com/{github_config.github_owner}/"
            f"{github_config.repository_name}/tree/{github_config.branch_name}"
        )
        self.e2e_service.create(
            id=self.task_id,
            title="Untitled E2E Research Task",
            created_by=self.created_by,
            status=Status.RUNNING,
            current_step=StepType.GENERATE_EXPERIMENTAL_DESIGN,
            github_url=github_url,
        )
        return {}

    @record_execution_time
    async def _prepare_repository(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, Any]:
        logger.info("=== Repository Preparation ===")
        result = (
            await PrepareRepositorySubgraph(
                github_client=self.github_client,
                is_github_repo_private=self.is_github_repo_private,
            )
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {
            "is_repository_ready": result["is_repository_ready"],
            "is_branch_ready": result["is_branch_ready"],
        }

    @record_execution_time
    async def _set_github_actions_secrets(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, bool]:
        logger.info("=== Set GitHub Actions Secrets ===")
        result = (
            await SetGithubActionsSecretsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {"secrets_set": result["secrets_set"]}

    @record_execution_time
    @save_to_db
    @upload_to_github
    async def _generate_experimental_design(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, Any]:
        logger.info("=== Experimental Design ===")
        result = (
            await GenerateExperimentalDesignSubgraph(
                langchain_client=self.langchain_client,
                runner_config=self.runner_config,
                num_models_to_use=self.num_experiment_models,
                llm_mapping=self.llm_mapping.generate_experimental_design,
                num_datasets_to_use=self.num_experiment_datasets,
                num_comparative_methods=self.num_comparison_methods,
            )
            .build_graph()
            .ainvoke({"research_hypothesis": state["research_hypothesis"]})
        )

        return {
            "experimental_design": result["experimental_design"],
            "current_step": StepType.GENERATE_CODE,
        }

    @record_execution_time
    async def _run_code_generation(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, Any]:
        logger.info("=== Run Code Generation ===")
        await (
            CodeGenerationGraph(
                github_client=self.github_client,
                wandb_config=self.wandb_config,
                github_actions_agent=self.github_actions_agent,
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
    @save_to_db
    @upload_to_github
    async def _fetch_run_ids(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, Any]:
        logger.info("=== Fetch Run IDs ===")
        try:
            result = (
                await FetchRunIdsSubgraph(github_client=self.github_client)
                .build_graph()
                .ainvoke({"github_config": state["github_config"]})
            )

            if not (run_ids := result["run_ids"]):
                error_msg = "No run IDs were fetched from the subgraph. Cannot proceed with experiments."
                logger.error(error_msg)
                raise ValueError(error_msg)

            logger.info(f"Successfully fetched {len(run_ids)} run IDs: {run_ids}")

            return {"run_ids": run_ids}
        except ValueError:
            raise
        except Exception as e:
            logger.exception(f"Failed to fetch run IDs: {e}")
            raise ValueError("Failed to fetch run IDs") from e

    @record_execution_time
    async def _run_sanity_check(
        self, state: HypothesisDrivenResearchState
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
    @save_to_db
    @upload_to_github
    async def _fetch_experiment_code(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, ExperimentCode]:
        logger.info("=== Fetch Experiment Code ===")
        result = (
            await FetchExperimentCodeSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {"experiment_code": result["experiment_code"]}

    @record_execution_time
    async def _run_main_experiment(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, Any]:
        logger.info("=== Run Main Experiment ===")
        await (
            MainExperimentGraph(
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
                }
            )
        )
        return {}

    @record_execution_time
    async def _run_visualization(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, Any]:
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
    @save_to_db
    @upload_to_github
    async def _fetch_experiment_results(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, Any]:
        logger.info("=== Fetch Experiment Results ===")
        result = (
            await FetchExperimentResultsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {
            "experimental_results": result["experimental_results"],
            "current_step": StepType.ANALYZE_EXPERIMENT_RESULTS,
        }

    @record_execution_time
    @save_to_db
    @upload_to_github
    async def _analyze_experiment(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, Any]:
        logger.info("=== Experiment Analysis ===")
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

        return {
            "experimental_analysis": result["experimental_analysis"],
            "current_step": StepType.GENERATE_BIBFILE,
        }

    @record_execution_time
    @save_to_db
    @upload_to_github
    async def _generate_bibfile(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, Any]:
        logger.info("=== Reference Generation ===")
        result = (
            await GenerateBibfileSubgraph()
            .build_graph()
            .ainvoke({"research_study_list": state.get("research_study_list", [])})
        )

        return {
            "references_bib": result["references_bib"],
            "current_step": StepType.GENERATE_PAPER,
        }

    @record_execution_time
    async def _push_bibfile(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, bool]:
        logger.info("=== Push Bibfile to GitHub ===")
        bibfile_path = f".research/latex/{self.latex_template_name}/references.bib"

        result = (
            await PushGitHubSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "push_files": {bibfile_path: state["references_bib"]},
                }
            )
        )

        return {"is_upload_successful": result["is_file_pushed"]}

    @record_execution_time
    @save_to_db
    @upload_to_github
    async def _generate_paper(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, Any]:
        logger.info("=== Paper Writing ===")
        result = (
            await WriteSubgraph(
                langchain_client=self.langchain_client,
                paper_content_refinement_iterations=self.paper_content_refinement_iterations,
                llm_mapping=self.llm_mapping.write,
            )
            .build_graph()
            .ainvoke(
                {
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                    "experiment_code": state["experiment_code"],
                    "experimental_results": state["experimental_results"],
                    "experimental_analysis": state["experimental_analysis"],
                    "research_study_list": state.get("research_study_list", []),
                    "references_bib": state["references_bib"],
                }
            )
        )

        return {
            "paper_content": result["paper_content"],
            "current_step": StepType.GENERATE_LATEX,
        }

    @record_execution_time
    async def _run_latex(self, state: HypothesisDrivenResearchState) -> dict[str, Any]:
        logger.info("=== Run LaTeX ===")
        result = (
            await LaTeXGraph(
                github_client=self.github_client,
                langchain_client=self.langchain_client,
                latex_template_name=self.latex_template_name,
                github_actions_agent=self.github_actions_agent,
                llm_mapping=self.llm_mapping.latex,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "references_bib": state["references_bib"],
                    "paper_content": state["paper_content"],
                }
            )
        )

        return {
            "paper_url": result.get("paper_url"),
            "current_step": StepType.DONE,
        }

    @record_execution_time
    async def _finalize(
        self, state: HypothesisDrivenResearchState
    ) -> dict[str, str | ResearchHistory | None]:
        logger.info("=== Workflow Completed ===")
        logger.info(
            f"Repository: {state['github_config'].github_owner}/{state['github_config'].repository_name}"
        )
        logger.info(f"Branch: {state['github_config'].branch_name}")
        if paper_url := state.get("paper_url"):
            logger.info(f"Paper URL: {paper_url}")

        self.e2e_service.update(
            id=self.task_id,
            status=Status.COMPLETED,
            current_step=StepType.DONE,
            result=to_dict_deep(state),
        )
        return {
            "status": "completed",
            "research_history": state.get("research_history"),
        }

    def build_graph(self):
        graph_builder = StateGraph(
            HypothesisDrivenResearchState,
            input_schema=HypothesisDrivenResearchInputState,
            output_schema=HypothesisDrivenResearchOutputState,
        )

        graph_builder.add_node("create_record", self._create_record)
        graph_builder.add_node("prepare_repository", self._prepare_repository)
        graph_builder.add_node(
            "set_github_actions_secrets", self._set_github_actions_secrets
        )
        graph_builder.add_node(
            "generate_experimental_design", self._generate_experimental_design
        )
        graph_builder.add_node("run_code_generation", self._run_code_generation)
        graph_builder.add_node("fetch_run_ids", self._fetch_run_ids)
        graph_builder.add_node("run_sanity_check", self._run_sanity_check)
        graph_builder.add_node("fetch_experiment_code", self._fetch_experiment_code)
        graph_builder.add_node("run_main_experiment", self._run_main_experiment)
        graph_builder.add_node("run_visualization", self._run_visualization)
        graph_builder.add_node(
            "fetch_experiment_results", self._fetch_experiment_results
        )
        graph_builder.add_node("analyze_experiment", self._analyze_experiment)
        graph_builder.add_node("generate_bibfile", self._generate_bibfile)
        graph_builder.add_node("push_bibfile", self._push_bibfile)
        graph_builder.add_node("generate_paper", self._generate_paper)
        graph_builder.add_node("run_latex", self._run_latex)
        graph_builder.add_node("finalize", self._finalize)

        graph_builder.add_edge(START, "create_record")
        graph_builder.add_edge("create_record", "prepare_repository")
        graph_builder.add_edge("prepare_repository", "set_github_actions_secrets")
        graph_builder.add_edge(
            "set_github_actions_secrets", "generate_experimental_design"
        )
        graph_builder.add_edge("generate_experimental_design", "run_code_generation")
        graph_builder.add_edge("run_code_generation", "fetch_run_ids")
        graph_builder.add_edge("fetch_run_ids", "run_sanity_check")
        graph_builder.add_edge("run_sanity_check", "fetch_experiment_code")
        graph_builder.add_edge("fetch_experiment_code", "run_main_experiment")
        graph_builder.add_edge("run_main_experiment", "run_visualization")
        graph_builder.add_edge("run_visualization", "fetch_experiment_results")
        graph_builder.add_edge("fetch_experiment_results", "analyze_experiment")
        graph_builder.add_edge("analyze_experiment", "generate_bibfile")
        graph_builder.add_edge("generate_bibfile", "push_bibfile")
        graph_builder.add_edge("push_bibfile", "generate_paper")
        graph_builder.add_edge("generate_paper", "run_latex")
        graph_builder.add_edge("run_latex", "finalize")
        graph_builder.add_edge("finalize", END)

        return graph_builder.compile()
