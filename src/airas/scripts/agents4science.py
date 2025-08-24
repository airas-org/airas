import logging

from tqdm import tqdm

from airas.features import (
    AnalyticSubgraph,
    CreateBibfileSubgraph,
    CreateCodeSubgraph,
    CreateExperimentalDesignSubgraph,
    CreateMethodSubgraph,
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

# Set the default LLM model for this session.
llm_name = "o3-mini-2025-01-31"


# --- Supported Models ---

OPENAI_MODEL = [
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
]

# If GEMINI_API_KEY is available
VERTEXAI_MODEL = [
    "gemini-2.5-pro",
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite-preview-06-17",
    "gemini-2.0-flash-001",
    "gemini-2.0-flash-lite-001",
    "gemini-embedding-001",
]

generate_queries = GenerateQueriesSubgraph(
    llm_name="gpt-5-mini-2025-08-07", n_queries=5
)
get_paper_titles = GetPaperTitlesFromDBSubgraph(
    max_results_per_query=3, semantic_search=True
)
retrieve_paper_content = RetrievePaperContentSubgraph(
    paper_provider="arxiv", target_study_list_source="research_study_list"
)
summarize_paper = SummarizePaperSubgraph(llm_name="gemini-2.5-pro")
retrieve_code = RetrieveCodeSubgraph(llm_name="gemini-2.5-pro")
reference_extractor = ExtractReferenceTitlesSubgraph(
    llm_name="gemini-2.5-flash", paper_retrieval_limit=10
)
retrieve_reference_paper_content = RetrievePaperContentSubgraph(
    paper_provider="arxiv", target_study_list_source="reference_research_study_list"
)
create_method = CreateMethodSubgraph(llm_name="gpt-5-2025-08-07", refine_iterations=2)
create_experimental_design = CreateExperimentalDesignSubgraph(
    llm_name="gpt-5-2025-08-07"
)
# coder = CreateCodeWithDevinSubgraph()
coder = CreateCodeSubgraph(llm_name="gpt-5-2025-08-07")
executor = GitHubActionsExecutorSubgraph(gpu_enabled=True)
# fixer = FixCodeWithDevinSubgraph(llm_name="gemini-2.5-flash")
fixer = FixCodeSubgraph(llm_name="gpt-5-2025-08-07")
analysis = AnalyticSubgraph(llm_name="gpt-5-2025-08-07")
create_bibfile = CreateBibfileSubgraph(
    llm_name="gemini-2.5-pro",
    latex_template_name="iclr2024",
    max_filtered_references=30,
)
writer = WriterSubgraph(llm_name="gpt-5-2025-08-07", max_refinement_count=2)
review = ReviewPaperSubgraph(llm_name="gpt-5-2025-08-07")
latex = LatexSubgraph(
    llm_name="gpt-5-2025-08-07",
    latex_template_name="agents4science_2025",
    max_revision_count=3,
)
readme = ReadmeSubgraph()
html = HtmlSubgraph(llm_name="gpt-5-2025-08-07")
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
    repository_name = "tanaka-20250824-v1"
    research_topic_list = [
        "New architecture of diffusion model",
    ]
    execute_workflow(
        github_owner, repository_name, research_topic_list=research_topic_list
    )
