import argparse
from typing import Any

from airas.features.github.github_upload_subgraph import (
    GithubUploadSubgraph,
)
from airas.features.github.prepare_repository_subgraph.prepare_repository_subgraph import (
    PrepareRepositorySubgraph,
)
from airas.features.retrieve.generate_queries_subgraph.generate_queries_subgraph import (
    GenerateQueriesSubgraph,
)
from airas.features.retrieve.get_paper_titles_subgraph.get_paper_titles_from_db_subgraph import (
    GetPaperTitlesFromDBSubgraph,
)
from airas.features.retrieve.retrieve_code_subgraph.retrieve_code_subgraph import (
    RetrieveCodeSubgraph,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.retrieve_paper_content_subgraph import (
    RetrievePaperContentSubgraph,
)
from airas.features.retrieve.summarize_paper_subgraph.summarize_paper_subgraph import (
    SummarizePaperSubgraph,
)
from airas.types.github import GitHubRepositoryInfo


def run_e2e_retrieve_workflow(
    research_topic: str,
    github_repository: str,
    branch_name: str,
    llm_name: str = "o3-mini-2025-01-31",
) -> dict[str, Any]:
    github_owner, repository_name = github_repository.split("/", 1)
    github_repository_info = GitHubRepositoryInfo(
        github_owner=github_owner,
        repository_name=repository_name,
        branch_name=branch_name,
    )

    print("Starting E2E Retrieve Workflow...")
    print(f"Repository: {github_repository}")
    print(f"Branch: {branch_name}")
    print(f"LLM: {llm_name}")

    state = {
        "github_repository_info": github_repository_info,
        "research_topic": research_topic,
    }

    # Step 1: Prepare Repository
    print("\nPreparing repository...")
    state = PrepareRepositorySubgraph().run(state)

    # Step 2: Generate Queries + Upload
    print("\nGenerating queries...")
    state = GenerateQueriesSubgraph(llm_name=llm_name).run(state)
    print(
        f"Generated {len(state.get('queries', []))} queries: {state.get('queries', [])}"
    )
    GithubUploadSubgraph().run(state)

    # Step 3: Get Paper Titles + Upload
    print("\nGetting paper titles from database...")
    state = GetPaperTitlesFromDBSubgraph(
        max_results_per_query=3, semantic_search=True
    ).run(state)
    print(f"Found {len(state.get('research_study_list', []))} papers")
    GithubUploadSubgraph().run(state)

    print("\nRetrieving paper content...")
    state = RetrievePaperContentSubgraph(
        target_study_list_source="research_study_list",
        paper_provider="arxiv",
    ).run(state)
    print(f"Retrieved content for {len(state.get('research_study_list', []))} papers")
    GithubUploadSubgraph().run(state)

    # Step 5: Summarize Papers + Upload
    print("\nSummarizing papers...")
    state = SummarizePaperSubgraph(llm_name=llm_name).run(state)
    print(f"Summarized {len(state.get('research_study_list', []))} papers")
    GithubUploadSubgraph().run(state)

    # Step 6: Retrieve Code + Upload
    print("\nRetrieving code from papers...")
    state = RetrieveCodeSubgraph().run(state)
    print(f"Retrieved code for {len(state.get('research_study_list', []))} papers")
    GithubUploadSubgraph().run(state)

    print("\nE2E Retrieve Workflow completed successfully!")
    return state


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="E2E Retrieve Workflow with GitHub Integration"
    )
    parser.add_argument("github_repository", help="GitHub repository (owner/repo)")
    parser.add_argument("branch_name", help="Branch name for GitHub uploads")

    research_topic = "diffusion model for image generation"
    llm_name = "o3-mini-2025-01-31"

    args = parser.parse_args()

    try:
        result = run_e2e_retrieve_workflow(
            research_topic=research_topic,
            github_repository=args.github_repository,
            branch_name=args.branch_name,
            llm_name=llm_name,
        )
        print(f"result: {result}")
    except Exception as e:
        print(f"Workflow failed: {e}")
        raise
