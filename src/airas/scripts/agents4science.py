import logging

from tqdm import tqdm

from airas.features import (
    AnalyticSubgraph,
    CreateBibfileSubgraph,
    CreateCodeSubgraph,
    CreateExperimentalDesignSubgraph,
    CreateMethodSubgraphV2,
    ExtractReferenceTitlesSubgraph,
    FixCodeSubgraph,
    FixCodeWithDevinSubgraph,
    GenerateQueriesSubgraph,
    GetPaperTitlesFromDBSubgraph,
    GitHubActionsExecutorSubgraph,
    GithubUploadSubgraph,
    HtmlSubgraph,
    LatexSubgraph,
    PrepareRepositorySubgraph,
    ReadmeSubgraph,
    RetrieveCodeSubgraph,
    RetrievePaperContentSubgraph,
    ReviewPaperSubgraph,
    SummarizePaperSubgraph,
    WriterSubgraph,
)
from airas.types.github import GitHubRepositoryInfo
from airas.utils.logging_utils import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

AVAILABLE_MODELS = [
    # gpt
    "o4-mini-2025-04-16",
    "o3-2025-04-16",
    "o3-mini-2025-01-31",
    "o1-pro-2025-03-19",
    "o1-2024-12-17",
    "gpt-5-2025-08-07",
    "gpt-5-mini-2025-08-07",
    "gpt-5-nano-2025-08-07",
    "gpt-4.1-2025-04-14",
    "gpt-4o-2024-11-20",
    "gpt-4o-mini-2024-07-18",
    # gemini
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite-preview-06-17",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite-001",
    "gemini-embedding-001",
]


generate_queries = GenerateQueriesSubgraph(
    llm_mapping={
        "generate_queries": "o3-2025-04-16",
    },
    n_queries=2,
)
get_paper_titles = GetPaperTitlesFromDBSubgraph(
    max_results_per_query=3, semantic_search=True
)
retrieve_paper_content = RetrievePaperContentSubgraph(
    target_study_list_source="research_study_list",
    llm_mapping={
        "search_arxiv_id_from_title": "gemini-2.5-flash",
    },
    paper_provider="arxiv",
)
summarize_paper = SummarizePaperSubgraph(
    llm_mapping={"summarize_paper": "gemini-2.5-flash"}
)
retrieve_code = RetrieveCodeSubgraph(
    llm_mapping={
        "extract_github_url_from_text": "gemini-2.5-flash",
        "extract_experimental_info": "gemini-2.5-flash",
    }
)
reference_extractor = ExtractReferenceTitlesSubgraph(
    llm_mapping={"extract_reference_titles": "gemini-2.5-flash"},
    paper_retrieval_limit=5,
)
retrieve_reference_paper_content = RetrievePaperContentSubgraph(
    target_study_list_source="reference_research_study_list",
    llm_mapping={
        "search_arxiv_id_from_title": "gemini-2.5-flash",
    },
    paper_provider="arxiv",
)

create_method = CreateMethodSubgraphV2(
    llm_mapping={
        "generate_ide_and_research_summary": "gpt-5-2025-08-07",
        "evaluate_novelty_and_significance": "gpt-5-2025-08-07",
        "refine_idea_and_research_summary": "gpt-5-2025-08-07",
        "search_arxiv_id_from_title": "gemini-2.5-flash",
    },
    refine_iterations=1,
)
create_experimental_design = CreateExperimentalDesignSubgraph(
    llm_mapping={
        "generate_experiment_strategy": "gpt-5-2025-08-07",
        "generate_experiment_specification": "gpt-5-2025-08-07",
        "generate_experiment_code": "gpt-5-2025-08-07",
    }
)
coder = CreateCodeSubgraph(
    llm_mapping={
        "generate_code_for_scripts": "gpt-5-2025-08-07",
    }
)
executor = GitHubActionsExecutorSubgraph(gpu_enabled=True)
fixer = FixCodeSubgraph(
    llm_mapping={
        "should_fix_code": "gpt-5-2025-08-07",
        "fix_code": "gpt-5-2025-08-07",
    }
)
analysis = AnalyticSubgraph(
    llm_mapping={
        "analytic_node": "gpt-5-2025-08-07",
    }
)
create_bibfile = CreateBibfileSubgraph(
    llm_mapping={
        "filter_references": "gemini-2.5-flash",
    },
    latex_template_name="agents4science_2025",
    max_filtered_references=5,
)
writer = WriterSubgraph(
    llm_mapping={
        "write_paper": "gpt-5-2025-08-07",
        "refine_paper": "gpt-5-2025-08-07",
    },
    max_refinement_count=2,
)
review = ReviewPaperSubgraph(
    llm_mapping={
        "review_paper": "gpt-5-2025-08-07",
    }
)
latex = LatexSubgraph(
    llm_mapping={
        "convert_to_latex": "gpt-5-2025-08-07",
        "is_execution_successful": "gpt-5-2025-08-07",
        "fix_latex_text": "gpt-5-2025-08-07",
    },
    latex_template_name="agents4science_2025",
    max_revision_count=3,
)
readme = ReadmeSubgraph()
html = HtmlSubgraph(
    llm_mapping={
        "convert_to_html": "gpt-5-2025-08-07",
    }
)
uploader = GithubUploadSubgraph()


subgraph_list = [
    generate_queries,
    get_paper_titles,
    retrieve_paper_content,
    summarize_paper,
    retrieve_code,
    create_method,
    create_experimental_design,
    coder,
    executor,
    fixer,
    analysis,
    reference_extractor,
    retrieve_reference_paper_content,
    create_bibfile,
    writer,
    review,
    latex,
    readme,
    html,
]


def run_subgraphs(subgraph_list, state):
    for subgraph in tqdm(subgraph_list, desc="Executing Research Workflow"):
        subgraph_name = subgraph.__class__.__name__
        print(f"--- Running Subgraph: {subgraph_name} ---")

        if isinstance(subgraph, (FixCodeSubgraph, FixCodeWithDevinSubgraph)):
            while True:
                if state.get("executed_flag") is True:
                    state = analysis.run(state)
                    break
                else:
                    state = fixer.run(state)
                    state = executor.run(state)
        else:
            state = subgraph.run(state)

        _ = uploader.run(state)
        print(f"--- Finished Subgraph: {subgraph_name} ---\n")


def execute_workflow(
    github_owner: str,
    repository_name: str,
    research_topic_list: list[str],
    subgraph_list: list = subgraph_list,
):
    for index, research_topic in enumerate(research_topic_list):
        print(f"index:{index}")
        state = {
            "github_repository_info": GitHubRepositoryInfo(
                github_owner=github_owner,
                repository_name=repository_name,
                branch_name=f"test-{index}",
            ),
            "research_topic": research_topic,
        }

        _ = PrepareRepositorySubgraph().run(state)
        try:
            _ = run_subgraphs(subgraph_list, state)
        except Exception:
            raise


if __name__ == "__main__":
    github_owner = "auto-res2"
    repository_name = "tanaka-20250825-v3"
    research_topic_list = [
        "Architecture of a new diffusion model for memory efficiency",
    ]
    execute_workflow(
        github_owner, repository_name, research_topic_list=research_topic_list
    )
