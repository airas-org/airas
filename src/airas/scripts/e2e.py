import json
import os
from datetime import datetime

from airas.features import (
    AnalyticSubgraph,
    CreateBibfileSubgraph,
    # CreateCodeWithDevinSubgraph,
    CreateCodeSubgraph,
    CreateExperimentalDesignSubgraph,
    CreateMethodSubgraph,
    FixCodeSubgraph,
    # FixCodeWithDevinSubgraph,
    GenerateQueriesSubgraph,
    GetPaperTitlesFromDBSubgraph,
    GitHubActionsExecutorSubgraph,
    GithubDownloadSubgraph,
    GithubUploadSubgraph,
    HtmlSubgraph,
    LatexSubgraph,
    PrepareRepositorySubgraph,
    ReadmeSubgraph,
    RetrieveCodeSubgraph,
    RetrievePaperContentSubgraph,
    SummarizePaperSubgraph,
    WriterSubgraph,
)

# llm_name = "o3-mini-2025-01-31"
llm_name = "gemini-2.5-flash"
save_dir = "/workspaces/airas/data"

prepare = PrepareRepositorySubgraph()
generate_queries = GenerateQueriesSubgraph(llm_name=llm_name)
get_paper_titles = GetPaperTitlesFromDBSubgraph(semantic_search=True)
retrieve_paper_content = RetrievePaperContentSubgraph(
    save_dir=save_dir, target_study_list_source="research_study_list"
)
summarize_paper = SummarizePaperSubgraph(llm_name=llm_name)
retrieve_code = RetrieveCodeSubgraph(llm_name=llm_name)
create_method = CreateMethodSubgraph(llm_name="o3-2025-04-16")
create_experimental_design = CreateExperimentalDesignSubgraph(llm_name="o3-2025-04-16")
# coder = CreateCodeWithDevinSubgraph()
coder = CreateCodeSubgraph(llm_name="o3-mini-2025-01-31")
executor = GitHubActionsExecutorSubgraph(gpu_enabled=True)
# fixer = FixCodeWithDevinSubgraph(llm_name="o3-mini-2025-01-31")
fixer = FixCodeSubgraph(llm_name="o3-mini-2025-01-31")
analysis = AnalyticSubgraph("o3-mini-2025-01-31")
writer = WriterSubgraph("o3-mini-2025-01-31")
citation = CreateBibfileSubgraph(
    llm_name="o3-mini-2025-01-31", latex_template="iclr2024"
)
latex = LatexSubgraph("o3-mini-2025-01-31")
readme = ReadmeSubgraph()
html = HtmlSubgraph("o3-mini-2025-01-31")
upload = GithubUploadSubgraph()
download = GithubDownloadSubgraph()


def save_state(state, step_name: str, save_dir: str):
    filename = f"{step_name}.json"
    state_save_dir = f"/workspaces/airas/data/{save_dir}"
    os.makedirs(state_save_dir, exist_ok=True)
    filepath = os.path.join(state_save_dir, filename)
    with open(filepath, "w", encoding="utf-8", errors="replace") as f:
        json.dump(state, f, indent=2, ensure_ascii=False, default=str)

    print(f"State saved: {filepath}")
    return state_save_dir


def load_state(file_path: str) -> dict:
    with open(file_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    print(f"State loaded: {file_path}")
    return state


def retrieve_execution_subgraph_list(
    file_path: str, subgraph_name_list: list[str]
) -> list[str]:
    filename = os.path.basename(file_path)
    START_FROM_STEP = os.path.splitext(filename)[0]
    start_index = subgraph_name_list.index(START_FROM_STEP)
    subgraph_name_list = subgraph_name_list[start_index + 1 :]
    return subgraph_name_list


def run_from_state_file(
    github_repository, branch_name, save_dir: str, file_path: str | None = None
):
    """
    filenameが指定されていればそのstateファイルから、指定されていなければ最初からsubgraphを順次実行し、各ステップの結果を保存する
    """
    subgraph_name_list = [
        "generate_queries",
        "get_paper_titles",
        "retrieve_paper_content",
        "summarize_paper",
        "retrieve_code",
        "create_method",
        "create_experimental_design",
        "coder",
        "executor",
        "fixer",
        "analysis",
        "writer",
        "citation",
        "latex",
        "readme",
        "html",
    ]

    if file_path:
        # stateをロード
        state = load_state(file_path)
        # 実行対象のsubgraphリストを取得
        subgraph_name_list = retrieve_execution_subgraph_list(
            file_path, subgraph_name_list
        )
    else:
        # 最初から実行
        state = {
            "research_topic": "Research on quantization to reduce the number of parameters in LLM models",
            "github_repository": github_repository,
            "branch_name": branch_name,
        }

    for subgraph_name in subgraph_name_list:
        if subgraph_name == "generate_queries":
            state = generate_queries.run(state)
            save_state(state, "generate_queries", save_dir)
        elif subgraph_name == "get_paper_titles":
            state = get_paper_titles.run(state)
            save_state(state, "get_paper_titles", save_dir)
        elif subgraph_name == "retrieve_paper_content":
            state = retrieve_paper_content.run(state)
            save_state(state, "retrieve_paper_content", save_dir)
        elif subgraph_name == "summarize_paper":
            state = summarize_paper.run(state)
            save_state(state, "summarize_paper", save_dir)
        elif subgraph_name == "create_method":
            state = create_method.run(state)
            save_state(state, "create_method", save_dir)
        elif subgraph_name == "create_experimental_design":
            state = create_experimental_design.run(state)
            save_state(state, "create_experimental_design", save_dir)
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
        # state = upload.run(state)
        # state = download.run(state)


def main(file_path: str | None = None):
    """
    E2E実行のメイン関数
    """
    save_dir = datetime.now().strftime("%Y%m%d_%H%M%S")
    github_repository = "auto-res2/tanaka-20250808-v2"
    branch_name = "develop"
    state = {
        "github_repository": github_repository,
        "branch_name": branch_name,
        "research_topic": "Research on quantization to reduce the number of parameters in LLM models",
    }
    prepare.run(state)
    if file_path:
        run_from_state_file(
            github_repository, branch_name, save_dir=save_dir, file_path=file_path
        )
    else:
        run_from_state_file(github_repository, branch_name, save_dir=save_dir)


if __name__ == "__main__":
    # Execute from the beginning
    main()

    # If you want to run from the middle, specify the file path.
    # file_path = "/workspaces/airas/data/20250727_113330/executor.json"
    # main(file_path=file_path)
