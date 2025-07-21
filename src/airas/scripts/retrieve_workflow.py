import json
import os
from datetime import datetime

from airas.features.retrieve.generate_queries_subgraph.generate_queries_subgraph import (
    GenerateQueriesSubgraph,
)
from airas.features.retrieve.get_paper_titles_subgraph.get_paper_titles_from_db_subgraph import (
    GetPaperTitlesFromDBSubgraph,
)
from airas.features.retrieve.retrieve_paper_content_subgraph.retrieve_paper_content_subgraph import (
    RetrievePaperContentSubgraph,
)
from airas.features.retrieve.summarize_paper_subgraph.summarize_paper_subgraph import (
    SummarizePaperSubgraph,
)

llm_name = "o3-mini-2025-01-31"
save_dir = "/workspaces/airas/data"


def save_state(state, step_name: str, save_dir: str):
    filename = f"{step_name}.json"
    state_save_dir = f"/workspaces/airas/data/{save_dir}"
    os.makedirs(state_save_dir, exist_ok=True)
    filepath = os.path.join(state_save_dir, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False, default=str)

    print(f"State saved: {filepath}")
    return state_save_dir


def load_state(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    print(f"State loaded: {file_path}")
    return state


def run_retrieve_workflow(user_prompt: str, save_dir_suffix: str | None = None):
    generate_queries_subgraph = GenerateQueriesSubgraph(llm_name=llm_name)
    get_paper_titles_subgraph = GetPaperTitlesFromDBSubgraph()
    retrieve_paper_content_subgraph = RetrievePaperContentSubgraph(save_dir=save_dir)
    summarize_paper_subgraph = SummarizePaperSubgraph(llm_name=llm_name)

    if save_dir_suffix:
        workflow_save_dir = (
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{save_dir_suffix}"
        )
    else:
        workflow_save_dir = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("Step 1: Generating queries...")
    state = {"user_prompt": user_prompt}
    state = generate_queries_subgraph.run(state)
    save_state(state, "generate_queries", workflow_save_dir)

    print("Step 2: Getting paper titles from database...")
    state = get_paper_titles_subgraph.run(state)
    save_state(state, "get_paper_titles", workflow_save_dir)

    print("Step 3: Retrieving paper content from ArXiv...")
    state = retrieve_paper_content_subgraph.run(state)
    save_state(state, "retrieve_paper_content", workflow_save_dir)

    print("Step 4: Summarizing paper content...")
    state = summarize_paper_subgraph.run(state)
    save_state(state, "summarize_paper", workflow_save_dir)

    print(f"Workflow completed. Results saved in: {workflow_save_dir}")
    return state


def run_from_state_file(file_path: str):
    subgraph_steps = [
        "generate_queries",
        "get_paper_titles",
        "retrieve_paper_content",
        "summarize_paper",
    ]

    state = load_state(file_path)

    filename = os.path.basename(file_path)
    step_name = os.path.splitext(filename)[0]

    if step_name not in subgraph_steps:
        print(f"Unknown step: {step_name}")
        return

    start_index = subgraph_steps.index(step_name)
    remaining_steps = subgraph_steps[start_index + 1 :]

    workflow_save_dir = os.path.basename(os.path.dirname(file_path))

    get_paper_titles_subgraph = GetPaperTitlesFromDBSubgraph()
    retrieve_paper_content_subgraph = RetrievePaperContentSubgraph(save_dir=save_dir)
    summarize_paper_subgraph = SummarizePaperSubgraph(llm_name=llm_name)

    for step in remaining_steps:
        print(f"Executing step: {step}")

        if step == "get_paper_titles":
            state = get_paper_titles_subgraph.run(state)
        elif step == "retrieve_paper_content":
            state = retrieve_paper_content_subgraph.run(state)
        elif step == "summarize_paper":
            state = summarize_paper_subgraph.run(state)

        save_state(state, step, workflow_save_dir)

    print(f"Workflow resumed and completed. Results saved in: {workflow_save_dir}")
    return state


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        run_from_state_file(file_path)
    else:
        user_prompt = "diffusion model for image generation"
        result = run_retrieve_workflow(user_prompt, save_dir_suffix="retrieve_workflow")

        print("\n=== Final Result ===")
        print(f"Generated queries: {result.get('queries', [])}")
        print(f"Found titles: {result.get('titles', [])}")
        print(f"Retrieved papers: {len(result.get('research_study_list', []))}")

        for i, study in enumerate(result.get("research_study_list", [])):
            print(f"\nPaper {i + 1}: {study.get('title', 'Unknown title')}")
            if "llm_extracted_info" in study:
                info = study["llm_extracted_info"]
                print(
                    f"  Main contributions: {info.get('main_contributions', 'N/A')[:100]}..."
                )
