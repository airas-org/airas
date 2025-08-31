import concurrent.futures
import csv
import os
from datetime import datetime

from airas.config.llm_config import BASE_MODEL
from airas.features import (
    AnalyticSubgraph,
    CheckExperimentalResultsSubgraph,
    CreateBibfileSubgraph,
    CreateBranchSubgraph,  # noqa: F401
    CreateCodeSubgraph,  # noqa: F401
    # CreateCodeWithDevinSubgraph,
    CreateExperimentalDesignSubgraph,
    CreateMethodSubgraph,
    ExtractReferenceTitlesSubgraph,
    FixCodeSubgraph,
    # FixCodeWithDevinSubgraph,
    GenerateQueriesSubgraph,
    GetPaperTitlesFromDBSubgraph,
    GitHubActionsExecutorSubgraph,
    GithubDownloadSubgraph,  # noqa: F401
    GithubUploadSubgraph,
    HtmlSubgraph,
    JudgeExperimentExecutionSubgraph,
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

github_owner = "auto-res2"
repository_name = "experiment_matsuzawa_20250826_6"

results_csv_file = "research_results.csv"


def _save_result_to_csv(research_topic, github_pages_url, branch_name):
    file_exists = os.path.exists(results_csv_file)

    with open(results_csv_file, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = [
            "timestamp",
            "research_topic",
            "llm_name",
            "branch_url",
            "github_pages_url",
            "paper_url",
        ]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        branch_url = (
            f"https://github.com/{github_owner}/{repository_name}/tree/{branch_name}"
            if branch_name
            else "N/A"
        )
        paper_url = (
            f"https://github.com/{github_owner}/{repository_name}/blob/{branch_name}/.research/paper.pdf"
            if branch_name
            else "N/A"
        )

        writer.writerow(
            {
                "timestamp": datetime.now().isoformat(),
                "research_topic": research_topic,
                "llm_name": BASE_MODEL,
                "branch_url": branch_url,
                "github_pages_url": github_pages_url or "N/A",
                "paper_url": paper_url,
            }
        )


research_topics = [
    # "Test-Time Adaptationを収束速度に関して改善したい",
    "Vision Mambaのメモリ効率に関して改善したい",
    # "離散拡散モデルの推論速度に関して改善したい",
    # "SHViT (Single-Head Vision Transformer)の精度-速度トレードオフに関して改善したい",
    # "QLoRAの量子化誤差に関して改善したい",
    # "Few-shot Prototypical Networksの汎化性能に関して改善したい",
    # "Flash Attention 3の消費電力効率に関して改善したい",
    # "知識蒸留における分布ミスマッチに関して改善したい",
    "Continuous Learningのメモリ効率に関して改善したい",
    # "Mixture of Expertsのルーティング効率に関して改善したい",
    # "Visual Autoregressiveモデルの解像度予測効率に関して改善したい",
    # "論理ゲートネットワークの学習安定性に関して改善したい",
    # "Autoguidanceの多様性保持に関して改善したい",
    # "KVキャッシュ圧縮の適応性に関して改善したい",
    # "Mamba-2の状態空間双対性を活用した視覚認識に関して改善したい",
    # "グラフ対比学習の表現散乱に関して改善したい",
    # "Flow Matchingの幾何学的効率に関して改善したい",
    # "メタ継続学習のヘシアン近似に関して改善したい",
    "階層的拡散モデルの計算効率に関して改善したい",
    # "LLMの不確実性推定に関して改善したい",
    # "MoE-Mambaのエキスパート選択効率に関して改善したい",
    # "パラメータ効率的ファインチューニングの忘却問題に関して改善したい",
    # "視覚トランスフォーマーのレジスタ最適化に関して改善したい",
    # "確率的テイラー微分推定の高次元拡張に関して改善したい",
    # "小規模データでのSSM事前学習に関して改善したい",
    # "グラデーション累積の動的最適化に関して改善したい",
    # "Mixture-of-Depthsの動的計算割り当てに関して改善したい",
    # "自己デバッグLLMのエラー検出精度に関して改善したい",
    # "リバーサルカースの克服に関して改善したい",
    # "ハイブリッドSSM-Transformerの最適配合に関して改善したい",
    # "フェデレーテッド学習のプライバシー効率トレードオフに関して改善したい",
    # "マルチモーダルVLMの計算効率に関して改善したい",
    # "敵対的ロバスト性の認証半径に関して改善したい",
    # "グリーンAIの学習時炭素排出に関して改善したい",
    # "グラフニューラルネットワークの過平滑化に関して改善したい",
    # "エッジデバイスでのオンデバイス学習に関して改善したい",
    # "データ選択の効率性に関して改善したい",
    # "時系列予測の不確実性定量化に関して改善したい",
    # "説明可能AIの計算コストに関して改善したい",
    # "プロンプト最適化の自動化に関して改善したい",
    # "ニューロモーフィックコンピューティングの学習効率に関して改善したい",
    # "因果推論の計算効率に関して改善したい",
    # "メタ学習の収束速度に関して改善したい",
    # "動的ニューラルネットワークの推論効率に関して改善したい",
    # "3D点群処理のメモリ効率に関して改善したい",
    # "合成データ生成の品質効率バランスに関して改善したい",
    # "自己教師あり学習の負例選択に関して改善したい",
    # "バックドア攻撃への防御効率に関して改善したい",
    # "ハイパーパラメータ最適化の効率に関して改善したい",
    # "マルチタスク学習の負の転移抑制に関して改善したい"
]


def create_subgraph_list():
    return [
        GenerateQueriesSubgraph(
            n_queries=5,
        ),
        GetPaperTitlesFromDBSubgraph(max_results_per_query=5, semantic_search=True),
        RetrievePaperContentSubgraph(
            target_study_list_source="research_study_list",
            paper_provider="arxiv",
        ),
        SummarizePaperSubgraph(),
        RetrieveCodeSubgraph(),
        CreateMethodSubgraph(
            refine_iterations=5,
        ),
        CreateExperimentalDesignSubgraph(),
        CreateCodeSubgraph(),
        GitHubActionsExecutorSubgraph(gpu_enabled=True),
        JudgeExperimentExecutionSubgraph(),
        FixCodeSubgraph(),
        AnalyticSubgraph(),
        ExtractReferenceTitlesSubgraph(
            paper_retrieval_limit=20,
        ),
        RetrievePaperContentSubgraph(
            target_study_list_source="reference_research_study_list",
            paper_provider="arxiv",
        ),
        CreateBibfileSubgraph(
            latex_template_name="agents4science_2025",
            max_filtered_references=30,
        ),
        WriterSubgraph(
            max_refinement_count=2,
        ),
        CheckExperimentalResultsSubgraph(),
        ReviewPaperSubgraph(),
        LatexSubgraph(
            latex_template_name="agents4science_2025",
            max_revision_count=5,
        ),
        HtmlSubgraph(),
        ReadmeSubgraph(),
    ]


def create_state_for_topic(research_topic, topic_index, session_id):
    branch_name = f"research-{session_id}-{topic_index:03d}"
    return {
        "github_repository_info": GitHubRepositoryInfo(
            github_owner=github_owner,
            repository_name=repository_name,
            branch_name=branch_name,
        ),
        "research_topic": research_topic,
    }


def run_subgraphs_for_topic(research_topic, topic_index, session_id):
    try:
        print(f"=== Starting processing for topic {topic_index}: {research_topic} ===")
        state = create_state_for_topic(research_topic, topic_index, session_id)

        subgraph_list = create_subgraph_list()
        uploader = GithubUploadSubgraph()

        # NOTE: リポジトリは事前作成済み、各workerでブランチを作成
        _ = PrepareRepositorySubgraph().run(state)

        for subgraph in subgraph_list:
            subgraph_name = subgraph.__class__.__name__
            print(f"--- Running Subgraph: {subgraph_name} for {research_topic} ---")

            try:
                if isinstance(subgraph, (FixCodeSubgraph, AnalyticSubgraph)):
                    continue

                elif isinstance(subgraph, (JudgeExperimentExecutionSubgraph)):
                    judge_experiment_execution = JudgeExperimentExecutionSubgraph()
                    analysis = AnalyticSubgraph()
                    fixer = FixCodeSubgraph()
                    executor = GitHubActionsExecutorSubgraph(gpu_enabled=True)

                    max_fix_attempts = 5
                    fix_attempts = 0
                    while fix_attempts < max_fix_attempts:
                        state = judge_experiment_execution.run(state)
                        if state.get("is_experiment_successful") is True:
                            state = analysis.run(state)
                            break
                        else:
                            state = fixer.run(state)
                            state = executor.run(state)
                            fix_attempts += 1
                    else:
                        print(
                            f"!!! Max fix attempts ({max_fix_attempts}) reached for {research_topic}. Moving on. !!!"
                        )
                        state = analysis.run(state)
                else:
                    state = subgraph.run(state)

                _ = uploader.run(state)
                print(
                    f"--- Finished Subgraph: {subgraph_name} for {research_topic} ---"
                )
            except Exception as e:
                print(
                    f"!!! Error in {subgraph_name} for {research_topic}: {str(e)} - Skipping subgraph !!!"
                )
                continue

        github_pages_url = state.get("github_pages_url")
        github_repo_info = state.get("github_repository_info")
        branch_name = github_repo_info.branch_name if github_repo_info else None
        _save_result_to_csv(research_topic, github_pages_url, branch_name)

        print(f"=== Completed processing for topic: {research_topic} ===")
        if github_pages_url:
            print(f"GitHub Pages URL: {github_pages_url}")
        return True
    except Exception as e:
        print(
            f"!!! Critical error for topic {research_topic}: {str(e)} - Skipping entire topic !!!"
        )
        _save_result_to_csv(research_topic, None, None)
        return False


def run_all_topics_parallel(max_workers: int):
    successful_count = 0
    failed_count = 0
    session_id = datetime.now().strftime("%Y%m%d-%H%M%S")

    # NOTE: リポジトリを事前に作成（競合を避けるため）
    print("=== Preparing repository ===")
    dummy_state = create_state_for_topic(research_topics[0], 1, session_id)
    try:
        PrepareRepositorySubgraph().run(dummy_state)
        print("✓ Repository prepared successfully")
    except Exception as e:
        print(f"!!! Repository preparation failed: {e}")
        return

    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_topic = {
            executor.submit(
                run_subgraphs_for_topic,
                topic,
                index + 1,
                session_id,
            ): topic
            for index, topic in enumerate(research_topics)
        }

        for future in concurrent.futures.as_completed(future_to_topic):
            topic = future_to_topic[future]
            try:
                success = future.result()
                if success:
                    successful_count += 1
                else:
                    failed_count += 1
            except Exception as e:
                print(f"!!! Exception for topic {topic}: {str(e)} !!!")
                failed_count += 1

    print("\n=== SUMMARY ===")
    print(f"Total topics: {len(research_topics)}")
    print(f"Successful: {successful_count}")
    print(f"Failed: {failed_count}")


if __name__ == "__main__":
    run_all_topics_parallel(max_workers=3)
