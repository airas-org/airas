import asyncio
import logging

from langgraph.graph import END, START, StateGraph
from pydantic import ValidationError
from typing_extensions import TypedDict

from airas.features.analyzers.analyze_experiment_subgraph.analyze_experiment_subgraph import (
    AnalyzeExperimentSubgraph,
)
from airas.features.executors.execute_evaluation_subgraph.execute_evaluation_subgraph import (
    ExecuteEvaluationSubgraph,
)
from airas.features.executors.execute_full_experiment_subgraph.execute_full_experiment_subgraph import (
    ExecuteFullExperimentSubgraph,
)
from airas.features.executors.execute_trial_experiment_subgraph.execute_trial_experiment_subgraph import (
    ExecuteTrialExperimentSubgraph,
)
from airas.features.executors.fetch_experiment_results_subgraph.fetch_experiment_results_subgraph import (
    FetchExperimentResultsSubgraph,
)
from airas.features.generators.generate_code_subgraph.generate_code_subgraph import (
    GenerateCodeSubgraph,
)
from airas.features.generators.generate_experimental_design_subgraph.generate_experimental_design_subgraph import (
    GenerateExperimentalDesignSubgraph,
)
from airas.features.generators.generate_hypothesis_subgraph.generate_hypothesis_subgraph_v0 import (
    GenerateHypothesisSubgraphV0,
)
from airas.features.github.github_upload_subgraph import GithubUploadSubgraph
from airas.features.github.poll_github_actions_subgraph.poll_github_actions_subgraph import (
    PollGithubActionsSubgraph,
)
from airas.features.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)
from airas.features.github.push_code_subgraph.push_code_subgraph import (
    PushCodeSubgraph,
)
from airas.features.publication.compile_latex_subgraph.compile_latex_subgraph import (
    CompileLatexSubgraph,
)
from airas.features.publication.generate_latex_subgraph.generate_latex_subgraph import (
    GenerateLatexSubgraph,
)
from airas.features.publication.push_latex_subgraph.push_latex_subgraph import (
    PushLatexSubgraph,
)
from airas.features.retrieve.retrieve_paper_subgraph.retrieve_paper_subgraph import (
    RetrievePaperSubgraph,
)
from airas.features.retrieve.search_paper_titles_subgraph.nodes.search_paper_titles_from_airas_db import (
    AirasDbPaperSearchIndex,
)
from airas.features.retrieve.search_paper_titles_subgraph.search_paper_titles_from_airas_db_subgraph import (
    SearchPaperTitlesFromAirasDbSubgraph,
)
from airas.features.writers.generate_bibfile_subgraph.generate_bibfile_subgraph import (
    GenerateBibfileSubgraph,
)
from airas.features.writers.write_subgraph.write_subgraph import WriteSubgraph
from airas.services.api_client.arxiv_client import ArxivClient
from airas.services.api_client.github_client import GithubClient
from airas.services.api_client.langchain_client import LangChainClient
from airas.types.experiment_code import ExperimentCode
from airas.types.experimental_analysis import ExperimentalAnalysis
from airas.types.experimental_design import ExperimentalDesign, RunnerConfig
from airas.types.experimental_results import ExperimentalResults
from airas.types.github import (
    GitHubActionsConclusion,
    GitHubActionsStatus,
    GitHubConfig,
)
from airas.types.paper import PaperContent
from airas.types.research_history import ResearchHistory
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy
from airas.types.wandb import WandbConfig
from airas.utils.execution_timers import ExecutionTimeState, time_node
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

record_execution_time = lambda f: time_node("execute_e2e")(f)  # noqa: E731


class ExecuteE2EInputState(TypedDict):
    github_config: GitHubConfig
    queries: list[str]
    runner_config: RunnerConfig
    wandb_config: WandbConfig
    is_private: bool
    max_results_per_query: int
    refinement_rounds: int
    num_models_to_use: int
    num_datasets_to_use: int
    num_comparative_methods: int
    max_code_validations: int
    writing_refinement_rounds: int
    latex_template_name: str


class ExecuteE2EOutputState(ExecutionTimeState):
    status: str
    research_history: ResearchHistory | None


class ExecuteE2EState(
    ExecuteE2EInputState,
    ExecuteE2EOutputState,
    total=False,
):
    paper_titles: list[str]
    research_study_list: list[ResearchStudy]
    research_hypothesis: ResearchHypothesis
    experimental_design: ExperimentalDesign
    experiment_code: ExperimentCode
    experimental_results: ExperimentalResults
    experimental_analysis: ExperimentalAnalysis
    references_bib: str
    paper_content: PaperContent
    latex_text: str
    is_repository_ready: bool
    is_branch_ready: bool
    code_pushed: bool
    is_upload_successful: bool
    # Experiment execution states
    trial_dispatched: bool
    trial_run_ids: list[str]
    trial_workflow_status: GitHubActionsStatus | None
    trial_workflow_conclusion: GitHubActionsConclusion | None
    full_dispatched: bool
    full_experiment_branches: list[str]
    full_workflow_status: GitHubActionsStatus | None
    full_workflow_conclusion: GitHubActionsConclusion | None
    evaluation_dispatched: bool
    evaluation_workflow_status: GitHubActionsStatus | None
    evaluation_workflow_conclusion: GitHubActionsConclusion | None
    compile_latex_dispatched: bool
    compile_latex_workflow_status: GitHubActionsStatus | None
    compile_latex_workflow_conclusion: GitHubActionsConclusion | None


class ExecuteE2ESubgraph:
    def __init__(
        self,
        search_index: AirasDbPaperSearchIndex,
        github_client: GithubClient,
        arxiv_client: ArxivClient,
        langchain_client: LangChainClient,
    ):
        self.search_index = search_index
        self.github_client = github_client
        self.arxiv_client = arxiv_client
        self.langchain_client = langchain_client

    def _validate_github_actions_completion(
        self,
        workflow_name: str,
        status: GitHubActionsStatus | None,
        conclusion: GitHubActionsConclusion | None,
    ) -> None:
        if status is None:
            raise ValueError(
                f"{workflow_name} workflow polling timed out or no status available"
            )

        if status is GitHubActionsStatus.COMPLETED:
            if conclusion not in {
                GitHubActionsConclusion.SUCCESS,
                GitHubActionsConclusion.NEUTRAL,
                GitHubActionsConclusion.SKIPPED,
            }:
                raise ValueError(
                    f"{workflow_name} workflow failed with conclusion: {conclusion}"
                )
            return

        if status in {
            GitHubActionsStatus.FAILURE,
            GitHubActionsStatus.STARTUP_FAILURE,
        }:
            raise ValueError(
                f"{workflow_name} workflow did not complete successfully. "
                f"Status: {status}, conclusion: {conclusion}"
            )

        raise ValueError(
            f"{workflow_name} workflow ended in unexpected state. "
            f"Status: {status}, conclusion: {conclusion}"
        )

    @record_execution_time
    async def _prepare_repository(self, state: ExecuteE2EState) -> dict[str, bool]:
        logger.info("=== Repository Preparation ===")
        result = (
            await PrepareRepositorySubgraph(
                github_client=self.github_client,
                is_private=state.get("is_private", True),
            )
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {
            "is_repository_ready": result["is_repository_ready"],
            "is_branch_ready": result["is_branch_ready"],
        }

    @record_execution_time
    async def _search_paper_titles(self, state: ExecuteE2EState) -> dict:
        logger.info("=== Search Paper Titles ===")
        result = (
            await SearchPaperTitlesFromAirasDbSubgraph(
                search_index=self.search_index,
                max_results_per_query=state.get("max_results_per_query", 5),
            )
            .build_graph()
            .ainvoke({"queries": state["queries"]})
        )
        return {"paper_titles": result["paper_titles"]}

    @record_execution_time
    async def _retrieve_papers(
        self, state: ExecuteE2EState
    ) -> dict[str, list[ResearchStudy]]:
        logger.info("=== Paper Retrieval ===")
        result = (
            await RetrievePaperSubgraph(
                langchain_client=self.langchain_client,
                arxiv_client=self.arxiv_client,
                github_client=self.github_client,
                max_results_per_query=state.get("max_results_per_query", 5),
            )
            .build_graph()
            .ainvoke({"paper_titles": state["paper_titles"]})
        )
        research_study_list = result["research_study_list"]
        logger.info(f"Retrieved {len(research_study_list)} papers")
        return {"research_study_list": research_study_list}

    @record_execution_time
    async def _generate_hypothesis(
        self, state: ExecuteE2EState
    ) -> dict[str, ResearchHypothesis]:
        logger.info("=== Hypothesis Generation ===")
        # TODO: objectiveを入力し、クエリを生成するように変更する
        research_objective = (
            state["queries"][0] if state.get("queries") else "Research objective"
        )

        result = (
            await GenerateHypothesisSubgraphV0(
                langchain_client=self.langchain_client,
                refinement_rounds=state.get("refinement_rounds", 1),
            )
            .build_graph()
            .ainvoke(
                {
                    "research_objective": research_objective,
                    "research_study_list": state["research_study_list"],
                }
            )
        )

        return {"research_hypothesis": result["research_hypothesis"]}

    @record_execution_time
    async def _upload_research_history(
        self, state: ExecuteE2EState
    ) -> dict[str, ResearchHistory]:
        logger.info("=== Upload Research History ===")
        try:
            research_history = ResearchHistory(
                **{
                    k: v
                    for k, v in state.items()
                    if k in ResearchHistory.model_fields.keys()
                }
            )
        except ValidationError as e:
            logger.error(f"Failed to construct ResearchHistory: {e}")
            raise

        await (
            GithubUploadSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "research_history": research_history,
                    "commit_message": "Update research history",
                }
            )
        )

        return {"research_history": research_history}

    @record_execution_time
    async def _generate_experimental_design(
        self, state: ExecuteE2EState
    ) -> dict[str, ExperimentalDesign]:
        logger.info("=== Experimental Design ===")
        result = (
            await GenerateExperimentalDesignSubgraph(
                langchain_client=self.langchain_client,
                runner_config=state["runner_config"],
                num_models_to_use=state.get("num_models_to_use", 1),
                num_datasets_to_use=state.get("num_datasets_to_use", 1),
                num_comparative_methods=state.get("num_comparative_methods", 1),
            )
            .build_graph()
            .ainvoke({"research_hypothesis": state["research_hypothesis"]})
        )

        return {"experimental_design": result["experimental_design"]}

    @record_execution_time
    async def _generate_code(self, state: ExecuteE2EState) -> dict[str, ExperimentCode]:
        logger.info("=== Code Generation ===")
        result = (
            await GenerateCodeSubgraph(
                langchain_client=self.langchain_client,
                wandb_config=state["wandb_config"],
                max_code_validations=state.get("max_code_validations", 3),
            )
            .build_graph()
            .ainvoke(
                {
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                }
            )
        )

        return {"experiment_code": result["experiment_code"]}

    @record_execution_time
    async def _push_code(self, state: ExecuteE2EState) -> dict[str, bool]:
        logger.info("=== Push Code to GitHub ===")
        result = (
            await PushCodeSubgraph(
                github_client=self.github_client,
                secret_names=None,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "experiment_code": state["experiment_code"],
                }
            )
        )

        return {"code_pushed": result["code_pushed"]}

    @record_execution_time
    async def _execute_trial_experiment(
        self, state: ExecuteE2EState
    ) -> dict[str, bool | list[str]]:
        logger.info("=== Execute Trial Experiment ===")
        result = (
            await ExecuteTrialExperimentSubgraph(
                github_client=self.github_client,
                runner_label=state["runner_config"].runner_label,
            )
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {
            "trial_dispatched": result["dispatched"],
            "trial_run_ids": result.get("run_ids", []),
        }

    @record_execution_time
    async def _poll_trial_workflow(
        self, state: ExecuteE2EState
    ) -> dict[str, GitHubActionsStatus | GitHubActionsConclusion | None]:
        logger.info("=== Poll Trial Workflow ===")
        result = (
            await PollGithubActionsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {"github_config": state["github_config"]}, {"recursion_limit": 300}
            )
        )

        status = result.get("status")
        conclusion = result.get("conclusion")
        self._validate_github_actions_completion("Trial", status, conclusion)

        return {
            "trial_workflow_status": status,
            "trial_workflow_conclusion": conclusion,
        }

    @record_execution_time
    async def _execute_full_experiment(
        self, state: ExecuteE2EState
    ) -> dict[str, bool | list[str]]:
        logger.info("=== Execute Full Experiment ===")
        result = (
            await ExecuteFullExperimentSubgraph(
                github_client=self.github_client,
                runner_label=state["runner_config"].runner_label,
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "run_ids": state.get("trial_run_ids", []),
                }
            )
        )

        branches = [
            branch_name
            for _, branch_name, success in result.get("branch_creation_results", [])
            if success
        ]

        return {
            "full_dispatched": result["all_dispatched"],
            "full_experiment_branches": branches,
        }

    @record_execution_time
    async def _poll_full_workflow(
        self, state: ExecuteE2EState
    ) -> dict[str, GitHubActionsStatus | GitHubActionsConclusion | None]:
        logger.info("=== Poll Full Workflow ===")

        if not (branches := state.get("full_experiment_branches", [])):
            logger.warning("No full experiment branches found, skipping poll")
            return {
                "full_workflow_status": None,
                "full_workflow_conclusion": None,
            }

        logger.info(f"Polling {len(branches)} branches in parallel: {branches}")

        async def poll_branch(
            branch: str,
        ) -> tuple[str, GitHubActionsStatus | None, GitHubActionsConclusion | None]:
            logger.info(f"Polling workflow for branch: {branch}")
            branch_config = GitHubConfig(
                **state["github_config"].model_dump(exclude={"branch_name"}),
                branch_name=branch,
            )

            result = (
                await PollGithubActionsSubgraph(github_client=self.github_client)
                .build_graph()
                .ainvoke({"github_config": branch_config}, {"recursion_limit": 300})
            )

            status: GitHubActionsStatus | None = result.get("status")
            conclusion: GitHubActionsConclusion | None = result.get("conclusion")

            logger.info(f"Branch {branch}: status={status}, conclusion={conclusion}")

            return branch, status, conclusion

        results = await asyncio.gather(*[poll_branch(branch) for branch in branches])

        all_success = all(
            conclusion == GitHubActionsConclusion.SUCCESS
            for _, _, conclusion in results
        )
        for branch, _, conclusion in results:
            if conclusion != GitHubActionsConclusion.SUCCESS:
                logger.warning(
                    f"Branch {branch} workflow failed with conclusion: {conclusion}"
                )

        final_status = GitHubActionsStatus.COMPLETED
        final_conclusion = (
            GitHubActionsConclusion.SUCCESS
            if all_success
            else GitHubActionsConclusion.FAILURE
        )

        self._validate_github_actions_completion("Full", final_status, final_conclusion)

        return {
            "full_workflow_status": final_status,
            "full_workflow_conclusion": final_conclusion,
        }

    @record_execution_time
    async def _execute_evaluation_workflow(
        self, state: ExecuteE2EState
    ) -> dict[str, bool]:
        logger.info("=== Execute Evaluation ===")
        result = (
            await ExecuteEvaluationSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "wandb_config": state["wandb_config"],
                }
            )
        )

        return {
            "evaluation_dispatched": result.get("dispatched", False),
        }

    @record_execution_time
    async def _poll_evaluation(
        self, state: ExecuteE2EState
    ) -> dict[str, GitHubActionsStatus | GitHubActionsConclusion | None]:
        logger.info("=== Poll Evaluation Workflow ===")
        result = (
            await PollGithubActionsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {"github_config": state["github_config"]}, {"recursion_limit": 300}
            )
        )

        status = result.get("status")
        conclusion = result.get("conclusion")
        self._validate_github_actions_completion("Evaluation", status, conclusion)

        return {
            "evaluation_workflow_status": status,
            "evaluation_workflow_conclusion": conclusion,
        }

    @record_execution_time
    async def _fetch_experiment_results(
        self, state: ExecuteE2EState
    ) -> dict[str, ExperimentalResults]:
        logger.info("=== Fetch Experiment Results ===")
        result = (
            await FetchExperimentResultsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {"experimental_results": result["experiment_results"]}

    @record_execution_time
    async def _analyze_experiment(
        self, state: ExecuteE2EState
    ) -> dict[str, ExperimentalAnalysis]:
        logger.info("=== Experiment Analysis ===")
        result = (
            await AnalyzeExperimentSubgraph(
                langchain_client=self.langchain_client,
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
    async def _generate_bibfile(self, state: ExecuteE2EState) -> dict[str, str]:
        logger.info("=== Reference Generation ===")
        result = (
            await GenerateBibfileSubgraph()
            .build_graph()
            .ainvoke({"research_study_list": state["research_study_list"]})
        )

        return {"references_bib": result["references_bib"]}

    @record_execution_time
    async def _generate_paper(self, state: ExecuteE2EState) -> dict[str, PaperContent]:
        logger.info("=== Paper Writing ===")
        result = (
            await WriteSubgraph(
                langchain_client=self.langchain_client,
                writing_refinement_rounds=state.get("writing_refinement_rounds", 2),
            )
            .build_graph()
            .ainvoke(
                {
                    "research_hypothesis": state["research_hypothesis"],
                    "experimental_design": state["experimental_design"],
                    "experiment_code": state["experiment_code"],
                    "experimental_results": state["experimental_results"],
                    "experimental_analysis": state["experimental_analysis"],
                    "research_study_list": state["research_study_list"],
                    "references_bib": state["references_bib"],
                }
            )
        )

        return {"paper_content": result["paper_content"]}

    @record_execution_time
    async def _generate_latex(self, state: ExecuteE2EState) -> dict[str, str]:
        logger.info("=== LaTeX Generation ===")
        result = (
            await GenerateLatexSubgraph(
                langchain_client=self.langchain_client,
                github_client=self.github_client,
                latex_template_name=state.get("latex_template_name", "iclr2024"),
            )
            .build_graph()
            .ainvoke(
                {
                    "references_bib": state["references_bib"],
                    "paper_content": state["paper_content"],
                }
            )
        )

        return {"latex_text": result["latex_text"]}

    @record_execution_time
    async def _push_latex(self, state: ExecuteE2EState) -> dict[str, bool]:
        logger.info("=== Push LaTeX to GitHub ===")
        result = (
            await PushLatexSubgraph(
                github_client=self.github_client,
                latex_template_name=state.get("latex_template_name", "iclr2024"),
            )
            .build_graph()
            .ainvoke(
                {
                    "github_config": state["github_config"],
                    "latex_text": state["latex_text"],
                }
            )
        )

        return {"is_upload_successful": result["is_upload_successful"]}

    @record_execution_time
    async def _compile_latex(
        self, state: ExecuteE2EState
    ) -> dict[str, bool | str | None]:
        logger.info("=== Compile LaTeX ===")
        result = (
            await CompileLatexSubgraph(
                github_client=self.github_client,
                latex_template_name=state.get("latex_template_name", "iclr2024"),
            )
            .build_graph()
            .ainvoke({"github_config": state["github_config"]})
        )

        return {
            "compile_latex_dispatched": result["compile_latex_dispatched"],
            "paper_url": result.get("paper_url"),
        }

    @record_execution_time
    async def _poll_compile_latex_workflow(
        self, state: ExecuteE2EState
    ) -> dict[str, GitHubActionsStatus | GitHubActionsConclusion | None]:
        logger.info("=== Poll Compile LaTeX Workflow ===")
        result = (
            await PollGithubActionsSubgraph(github_client=self.github_client)
            .build_graph()
            .ainvoke(
                {"github_config": state["github_config"]}, {"recursion_limit": 300}
            )
        )

        status = result.get("status")
        conclusion = result.get("conclusion")
        self._validate_github_actions_completion("Compile LaTeX", status, conclusion)

        return {
            "compile_latex_workflow_status": status,
            "compile_latex_workflow_conclusion": conclusion,
        }

    @record_execution_time
    async def _finalize(
        self, state: ExecuteE2EState
    ) -> dict[str, str | ResearchHistory | None]:
        logger.info("=== Workflow Completed ===")
        logger.info(
            f"Repository: {state['github_config'].github_owner}/{state['github_config'].repository_name}"
        )
        logger.info(f"Branch: {state['github_config'].branch_name}")
        if paper_url := state.get("paper_url"):
            logger.info(f"Paper URL: {paper_url}")

        return {
            "status": "completed",
            "research_history": state.get("research_history"),
        }

    def build_graph(self):
        PIPELINE = [
            ("prepare_repository", self._prepare_repository),
            ("search_paper_titles", self._search_paper_titles),
            ("retrieve_papers", self._retrieve_papers),
            ("generate_hypothesis", self._generate_hypothesis),
            ("generate_experimental_design", self._generate_experimental_design),
            ("generate_code", self._generate_code),
            ("push_code", self._push_code),
            ("execute_trial_experiment", self._execute_trial_experiment),
            ("poll_trial_workflow", self._poll_trial_workflow),
            ("execute_full_experiment", self._execute_full_experiment),
            ("poll_full_workflow", self._poll_full_workflow),
            ("execute_evaluation_workflow", self._execute_evaluation_workflow),
            ("poll_evaluation", self._poll_evaluation),
            ("fetch_experiment_results", self._fetch_experiment_results),
            ("analyze_experiment", self._analyze_experiment),
            ("generate_bibfile", self._generate_bibfile),
            ("generate_paper", self._generate_paper),
            ("generate_latex", self._generate_latex),
            ("push_latex", self._push_latex),
            ("compile_latex", self._compile_latex),
            ("poll_compile_latex_workflow", self._poll_compile_latex_workflow),
            ("finalize", self._finalize),
        ]

        UPLOAD_AFTER = {
            "search_paper_titles",
            "retrieve_papers",
            "generate_hypothesis",
            "generate_experimental_design",
            "generate_code",
            "fetch_experiment_results",
            "analyze_experiment",
            "generate_bibfile",
            "generate_paper",
            "generate_latex",
        }

        graph_builder = StateGraph(
            ExecuteE2EState,
            input_schema=ExecuteE2EInputState,
            output_schema=ExecuteE2EOutputState,
        )

        for node_name, method in PIPELINE:
            graph_builder.add_node(node_name, method)

        for node in UPLOAD_AFTER:
            upload_node = f"upload_after_{node}"
            graph_builder.add_node(upload_node, self._upload_research_history)

        graph_builder.add_edge(START, PIPELINE[0][0])

        for (prev, _), (nxt, _) in zip(PIPELINE, PIPELINE[1:], strict=False):
            if prev in UPLOAD_AFTER:
                upload_node = f"upload_after_{prev}"
                graph_builder.add_edge(prev, upload_node)
                graph_builder.add_edge(upload_node, nxt)
            else:
                graph_builder.add_edge(prev, nxt)

        graph_builder.add_edge(PIPELINE[-1][0], END)

        return graph_builder.compile()


if __name__ == "__main__":
    from dependency_injector.wiring import Provide

    from airas.core.container import Container

    graph = ExecuteE2ESubgraph(
        search_index=Provide[Container.airas_db_paper_search_index],
        github_client=Provide[Container.github_client],
        arxiv_client=Provide[Container.arxiv_client],
        langchain_client=Provide[Container.langchain_client],
    ).build_graph()
    print(graph.get_graph().draw_mermaid())
