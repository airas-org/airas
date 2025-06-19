from airas.core import (
    AnalyticSubgraph,
    CreateExperimentalDesignSubgraph,
    CreateMethodSubgraph,
    CreateCodeSubgraph,
    FixCodeSubgraph,
    GitHubActionsExecutorSubgraph,
    PrepareRepositorySubgraph,
    GithubDownloadSubgraph,
    GithubUploadSubgraph,
    HtmlSubgraph,
    LatexSubgraph,
    ReadmeSubgraph,
    RetrieveCodeSubgraph,
    RetrievePaperFromQuerySubgraph,
    RetrieveRelatedPaperSubgraph,
    CitationSubgraph,
    WriterSubgraph,
    create_branch,
)

import json
import os
from datetime import datetime


scrape_urls = [
    "https://icml.cc/virtual/2024/papers.html?filter=title",
    # "https://iclr.cc/virtual/2024/papers.html?filter=title",
    # "https://nips.cc/virtual/2024/papers.html?filter=title",
    # "https://cvpr.thecvf.com/virtual/2024/papers.html?filter=title",
]
#llm_name = "o3-mini-2025-01-31"
llm_name = "gemini-2.0-flash-001"
save_dir = "/workspaces/airas/data"

prepare = PrepareRepositorySubgraph()
retriever = RetrievePaperFromQuerySubgraph(llm_name=llm_name, save_dir=save_dir, scrape_urls=scrape_urls)
retriever2 = RetrieveRelatedPaperSubgraph(llm_name=llm_name, save_dir=save_dir, scrape_urls=scrape_urls)
retriever3 = RetrieveCodeSubgraph(llm_name=llm_name)
creator = CreateMethodSubgraph(llm_name="o3-mini-2025-01-31")
creator2 = CreateExperimentalDesignSubgraph(llm_name="o3-mini-2025-01-31")
coder = CreateCodeSubgraph()
executor = GitHubActionsExecutorSubgraph(gpu_enabled=True)
fixer = FixCodeSubgraph(llm_name="o3-mini-2025-01-31")
analysis = AnalyticSubgraph("o3-mini-2025-01-31")
writer = WriterSubgraph("o3-mini-2025-01-31")
citation = CitationSubgraph(llm_name="o3-mini-2025-01-31")
latex = LatexSubgraph("o3-mini-2025-01-31")
readme = ReadmeSubgraph()
html = HtmlSubgraph("o3-mini-2025-01-31")

upload = GithubUploadSubgraph()


def save_state(state, step_name: str, save_dir: str):
    filename = f"{step_name}.json"
    state_save_dir = f"/workspaces/airas/data/{save_dir}"
    os.makedirs(state_save_dir, exist_ok=True)
    filepath = os.path.join(state_save_dir, filename)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"State saved: {filepath}")
    return state_save_dir


def load_state(file_path: str) -> dict:
    with open(file_path, 'r', encoding='utf-8') as f:
        state = json.load(f)
    print(f"State loaded: {file_path}")
    return state


def retrieve_execution_subgraph_list(filename: str, subgraph_name_list: list[str]) -> list[str]:
    START_FROM_STEP = filename.split('_')[1]
    start_index = subgraph_name_list.index(START_FROM_STEP)
    subgraph_name_list = subgraph_name_list[start_index + 1:]
    return subgraph_name_list

def run_from_state_file(github_repository, branch_name, save_dir: str, filename: str | None = None):
    """
    filenameが指定されていればそのstateファイルから、指定されていなければ最初からsubgraphを順次実行し、各ステップの結果を保存する
    """
    subgraph_name_list = [
        "retriever",
        "retriever2",
        "retriever3",
        "creator",
        "creator2",
        # "coder",
        # "executor",
        # "fixer",
        # "anlysis",
        # "writer",
        # "citation",
        # "latex",
        # "readme",
        # "html",
    ]

    if filename:
        # stateをロード
        state = load_state(filename)
        # 実行対象のsubgraphリストを取得
        subgraph_name_list = retrieve_execution_subgraph_list(filename, subgraph_name_list)
    else:
        # 最初から実行
        state = {
            "base_queries": ["diffusion model"],
            "github_repository": github_repository,
            "branch_name": branch_name,
        }

    for subgraph_name in subgraph_name_list:
        if subgraph_name == "retriever":
            state = retriever.run(state)
            save_state(state, "retriever", save_dir)
            upload.run(state)
        elif subgraph_name == "retriever2":
            state = retriever2.run(state)
            save_state(state, "retriever2", save_dir)
            upload.run(state)
        elif subgraph_name == "retriever3":
            state = retriever3.run(state)
            save_state(state, "retriever3", save_dir)
            upload.run(state)
        elif subgraph_name == "creator":
            state = creator.run(state)
            save_state(state, "creator", save_dir)
            upload.run(state)
        elif subgraph_name == "creator2":
            state = creator2.run(state)
            save_state(state, "creator2", save_dir)
            upload.run(state)
        elif subgraph_name == "coder":
            state = coder.run(state)
            save_state(state, "coder", save_dir)
        elif subgraph_name == "executor":
            state = executor.run(state)
            save_state(state, "executor", save_dir)
        elif subgraph_name == "fixer":
            while True:
                state = fixer.run(state)
                save_state(state, "fixer", save_dir)
                if state.get("executed_flag") is True:
                    state = analysis.run(state)
                    save_state(state, "analysis", save_dir)
                    break
                else:
                    state = executor.run(state)
                    save_state(state, "executor", save_dir)
        elif subgraph_name == "analysis":
            state = analysis.run(state)
            save_state(state, "analysis", save_dir)
        elif subgraph_name == "writer":
            state = writer.run(state)
            save_state(state, "writer", save_dir)
        elif subgraph_name == "citation":
            state = citation.run(state)
            save_state(state, "citation", save_dir)
        elif subgraph_name == "latex":
            state = latex.run(state)
            save_state(state, "latex", save_dir)
        elif subgraph_name == "readme":
            state = readme.run(state)
            save_state(state, "readme", save_dir)
        elif subgraph_name == "html":
            state = html.run(state)
            save_state(state, "html", save_dir)
        

if __name__ == "__main__":
    github_repository = "auto-res2/experiment_script_matsuzawa_5"
    branch_name = "test"
    
    state = {
        "github_repository": github_repository,
        "branch_name": branch_name,
      }
    prepare.run(state)
    
    save_dir = datetime.now().strftime("%Y%m%d_%H%M%S")
    # file_name = "state_coder_20250610_160554.json"
    # run_from_state_file(github_repository, branch_name, file_name)
    run_from_state_file(github_repository, branch_name, save_dir = save_dir)

    # import sys
    # if len(sys.argv) > 1:
    #     run_from_state_file(sys.argv[1])
    # else:
    #     run_from_state_file()
