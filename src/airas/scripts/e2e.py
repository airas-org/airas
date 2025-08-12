import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Type, TypeVar

from pydantic import TypeAdapter

from airas.features import (
    AnalyticSubgraph,
    CreateBibfileSubgraph,
    # CreateCodeWithDevinSubgraph,
    CreateCodeSubgraph,
    CreateExperimentalDesignSubgraph,
    CreateMethodSubgraph,
    ExtractReferenceTitlesSubgraph,
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
from airas.types.github import GitHubRepositoryInfo
from airas.types.research_hypothesis import ResearchHypothesis
from airas.types.research_study import ResearchStudy

# llm_name = "o3-mini-2025-01-31"
llm_name = "gemini-2.5-flash"
save_dir = "/workspaces/airas/data"

prepare = PrepareRepositorySubgraph()
generate_queries = GenerateQueriesSubgraph(llm_name=llm_name, n_queries=1)
get_paper_titles = GetPaperTitlesFromDBSubgraph(
    max_results_per_query=1, semantic_search=True
)
retrieve_paper_content = RetrievePaperContentSubgraph(
    target_study_list_source="research_study_list"
)
summarize_paper = SummarizePaperSubgraph(llm_name=llm_name)
retrieve_code = RetrieveCodeSubgraph(llm_name=llm_name)
create_method = CreateMethodSubgraph(llm_name=llm_name)
create_experimental_design = CreateExperimentalDesignSubgraph(llm_name=llm_name)
# coder = CreateCodeWithDevinSubgraph()
coder = CreateCodeSubgraph(llm_name=llm_name)
reference_extractor = ExtractReferenceTitlesSubgraph(
    llm_name=llm_name, paper_retrieval_limit=1
)
retrieve_reference_paper_content = RetrievePaperContentSubgraph(
    target_study_list_source="reference_research_study_list"
)
executor = GitHubActionsExecutorSubgraph(gpu_enabled=True)
# fixer = FixCodeWithDevinSubgraph(llm_name="o3-mini-2025-01-31")
fixer = FixCodeSubgraph(llm_name=llm_name)
analysis = AnalyticSubgraph(llm_name=llm_name)
writer = WriterSubgraph(llm_name=llm_name)
citation = CreateBibfileSubgraph(llm_name=llm_name, latex_template="iclr2024")
latex = LatexSubgraph(llm_name=llm_name)
readme = ReadmeSubgraph()
html = HtmlSubgraph(llm_name=llm_name)
upload = GithubUploadSubgraph()
download = GithubDownloadSubgraph()


_TA_ANY = TypeAdapter(Any)

T = TypeVar("T")


def save_state(
    state: Any,
    step_name: str,
    save_dir: str,
    *,
    by_alias: bool = False,
    exclude_none: bool = False,
):
    filename = f"{step_name}.json"
    state_save_dir = f"/workspaces/airas/data/{save_dir}"
    os.makedirs(state_save_dir, exist_ok=True)
    filepath = os.path.join(state_save_dir, filename)

    # ★ ここがポイント：BaseModel を含むオブジェクトを再帰的に「素のPython型」に変換
    plain = _TA_ANY.dump_python(state, by_alias=by_alias, exclude_none=exclude_none)

    # そのままJSON保存（default=str は不要）
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(plain, f, indent=2, ensure_ascii=True)


def load_state(
    path: str | bytes | os.PathLike,
    *,
    field_type_map: dict[str, Any]
    | None = None,  # 例: {"user": UserModel, "items": list[ItemModel]}
    base_target: Type[T] | None = None,  # 例: 全体を UserEnvelope にしたいとき
) -> dict | T:
    text = Path(path).read_text(encoding="utf-8")

    # まずは全体をプリミティブ型でロード
    data: Any = TypeAdapter(Any).validate_json(text)

    # 必要なら全体を一括で Pydantic モデルへ（包絡モデルがある場合）
    if base_target is not None:
        return TypeAdapter(base_target).validate_python(data)

    # 特定フィールドだけ型変換
    if field_type_map:
        for field, target_ann in field_type_map.items():
            if isinstance(data, dict) and field in data and data[field] is not None:
                data[field] = TypeAdapter(target_ann).validate_python(data[field])

    return data


def retrieve_execution_subgraph_list(
    file_path: str, subgraph_name_list: list[str]
) -> list[str]:
    filename = os.path.basename(file_path)
    START_FROM_STEP = os.path.splitext(filename)[0]
    start_index = subgraph_name_list.index(START_FROM_STEP)
    subgraph_name_list = subgraph_name_list[start_index + 1 :]
    return subgraph_name_list


def run_from_state_file(state: dict, save_dir: str, file_path: str | None = None):
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
        "reference_extractor",
        "retrieve_reference_paper_content",
        "writer",
        "citation",
        "latex",
        "readme",
        "html",
    ]

    field_type_map = {
        "github_repository_info": GitHubRepositoryInfo,
        "research_study_list": list[ResearchStudy],
        "reference_research_study_list": list[ResearchStudy],
        "new_method": ResearchHypothesis,
    }

    if file_path:
        # stateをロード
        state = load_state(file_path, field_type_map=field_type_map)
        # 実行対象のsubgraphリストを取得
        subgraph_name_list = retrieve_execution_subgraph_list(
            file_path, subgraph_name_list
        )

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
        elif subgraph_name == "retrieve_code":
            state = retrieve_code.run(state)
            save_state(state, "retrieve_code", save_dir)
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
                if state.get("executed_flag") is True:
                    state = analysis.run(state)
                    save_state(state, "analysis", save_dir)
                    break
                else:
                    state = fixer.run(state)
                    save_state(state, "fixer", save_dir)
                    state = executor.run(state)
                    save_state(state, "executor", save_dir)
        elif subgraph_name == "analysis":
            state = analysis.run(state)
            save_state(state, "analysis", save_dir)
        elif subgraph_name == "reference_extractor":
            state = reference_extractor.run(state)
            save_state(state, "reference_extractor", save_dir)
        elif subgraph_name == "retrieve_reference_paper_content":
            state = retrieve_reference_paper_content.run(state)
            save_state(state, "retrieve_reference_paper_content", save_dir)
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
    input_data = {
        "github_repository_info": GitHubRepositoryInfo(
            github_owner="auto-res2",
            repository_name="tanaka-20250812-v4",
            branch_name="develop-2",
        ),
        "research_topic": "Research on diffusion models and reinforcement learning",
    }
    prepare.run(input_data)
    if file_path:
        run_from_state_file(input_data, save_dir=save_dir, file_path=file_path)
    else:
        run_from_state_file(input_data, save_dir=save_dir)


if __name__ == "__main__":
    # Execute from the beginning
    main()

    # If you want to run from the middle, specify the file path.
    # file_path = "/workspaces/airas/data/20250812_111116/retrieve_reference_paper_content.json"
    # main(file_path=file_path)
