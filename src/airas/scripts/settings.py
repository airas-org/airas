from typing import Literal

from pydantic import BaseModel
from pydantic_settings import BaseSettings

from airas.config.runner_type_info import RunnerType


class GenerateQueriesSubgraphConfig(BaseModel):
    n_queries: int = 2  # 論文検索時のサブクエリの数


class GetPaperTitlesFromDBSubgraphConfig(BaseModel):
    max_results_per_query: int = 2  # 論文検索時の各サブクエリに対する論文数
    semantic_search: bool = True  # QDRANRの意味検索をつ買う


class RetrievePaperContentSubgraphConfig(BaseModel):
    paper_provider: Literal["arxiv", "semantic_scholar"] = "arxiv"  # 論文取得先


class ExtractReferenceTitlesSubgraphConfig(BaseModel):
    num_reference_paper: int = 2  # 論文作成時に追加で参照する論文数


class CreateMethodSubgraphV2Config(BaseModel):
    method_refinement_rounds: int = 2  # 新規手法の改良回数
    num_retrieve_related_papers: int = (
        5  # 新規手法作成時に新規性を確認するのに取得する論文数
    )


class CreateExperimentalDesignSubgraphConfig(BaseModel):
    num_models_to_use: int = 2  # 実験で使用するモデルの数
    num_datasets_to_use: int = 2  # 実験で使用するデータセットの数
    num_comparative_methods: int = 2  # 実験で比較する手法の数


class RetrieveHuggingFaceSubgraphConfig(BaseModel):
    max_results_per_search: int = (
        10  # modelやdatasetごとのHuggingFaceからの候補の取得数
    )
    max_models: int = 10  # LLMで選択するHuggingFaceのモデルの最大数
    max_datasets: int = 10  # LLMで選択するHuggingFaceのデータセットの最大数
    include_gated: bool = False


class CreateCodeSubgraphConfig(BaseModel):
    max_base_code_validations: int = 10  # 全実験で共通するコードの最大改善回数
    max_experiment_code_validations: int = 10  # 各実験コードの最大改善回数


class EvaluateExperimentalConsistencySubgraphConfig(BaseModel):
    consistency_score_threshold: int = 1  # 実験に一貫性スコア（1-10）


class CreateBibfileSubgraphConfig(BaseModel):
    # TODO: Literalで定義する
    latex_template_name: str = "agents4science_2025"
    max_filtered_references: int = 20  # 論文中で引用する参考文献の最大数


class WriterSubgraphConfig(BaseModel):
    writing_refinement_rounds: int = 2  # 論文の推敲回数


class LatexSubgraphConfig(BaseModel):
    max_chktex_revisions: int = 3  # LaTeXの文法チェックの最大修正回数
    max_compile_revisions: int = 3  # LaTeXのコンパイルエラーの最大修正回数


class LLMMappingConfig(BaseModel):
    generate_queries: str = "o4-mini-2025-04-16"
    search_arxiv_id_from_title: str = (
        "gpt-5-mini-2025-08-07"  # Only openAI models are available.
    )
    summarize_paper: str = "gemini-2.5-flash"
    extract_github_url_from_text: str = "gemini-2.5-flash"
    extract_experimental_info: str = "gemini-2.5-flash"
    extract_reference_titles: str = "gemini-2.5-flash-lite-preview-06-17"
    generate_ide_and_research_summary: str = "o3-2025-04-16"
    evaluate_novelty_and_significance: str = "o3-2025-04-16"
    refine_idea_and_research_summary: str = "o3-2025-04-16"
    generate_experiment_strategy: str = "o3-2025-04-16"
    generate_experiments: str = "o3-2025-04-16"
    select_resources: str = "gemini-2.5-flash"
    generate_base_code: str = "o3-2025-04-16"
    derive_specific_experiments: str = "o3-2025-04-16"
    validate_base_code: str = "o3-2025-04-16"
    validate_experiment_code: str = "o3-2025-04-16"
    evaluate_experimental_consistency: str = "o3-2025-04-16"
    analytic_node: str = "o3-2025-04-16"
    filter_references: str = "gemini-2.5-flash"
    write_paper: str = "gpt-5-2025-08-07"
    refine_paper: str = "o3-2025-04-16"
    review_paper: str = "o3-2025-04-16"
    convert_to_latex: str = "gpt-5-2025-08-07"
    check_execution_successful: str = "gpt-5-2025-08-07"
    fix_latex_text: str = "o3-2025-04-16"
    convert_to_html: str = "gpt-5-2025-08-07"


class Settings(BaseSettings):
    profile: Literal["test", "prod"] = "test"

    # 実行基盤
    runner_type: RunnerType = "A100_80GM×1"
    # TODO: From the perspective of research consistency,
    # we should probably not have ClaudeCode make changes to HuggingFace resources.
    # This change includes prompt modifications in `run_experiment_with_claude_code.yml``.
    secret_names: list[str] = ["HF_TOKEN", "ANTHROPIC_API_KEY", "WANDB_API_KEY"]

    # 設定
    generate_queries: GenerateQueriesSubgraphConfig = GenerateQueriesSubgraphConfig()
    get_paper_titles_from_db: GetPaperTitlesFromDBSubgraphConfig = (
        GetPaperTitlesFromDBSubgraphConfig()
    )
    retrieve_paper_content: RetrievePaperContentSubgraphConfig = (
        RetrievePaperContentSubgraphConfig()
    )
    extract_reference_titles: ExtractReferenceTitlesSubgraphConfig = (
        ExtractReferenceTitlesSubgraphConfig()
    )
    create_method: CreateMethodSubgraphV2Config = CreateMethodSubgraphV2Config()
    create_experimental_design: CreateExperimentalDesignSubgraphConfig = (
        CreateExperimentalDesignSubgraphConfig()
    )
    retrieve_hugging_face: RetrieveHuggingFaceSubgraphConfig = (
        RetrieveHuggingFaceSubgraphConfig()
    )
    create_code: CreateCodeSubgraphConfig = CreateCodeSubgraphConfig()
    evaluate_experimental_consistency: EvaluateExperimentalConsistencySubgraphConfig = (
        EvaluateExperimentalConsistencySubgraphConfig()
    )
    create_bibfile: CreateBibfileSubgraphConfig = CreateBibfileSubgraphConfig()
    writer: WriterSubgraphConfig = WriterSubgraphConfig()
    latex: LatexSubgraphConfig = LatexSubgraphConfig()

    # LLMの設定
    llm_mapping: LLMMappingConfig = LLMMappingConfig()

    def apply_profile_overrides(self) -> "Settings":
        if self.profile == "test":
            self.generate_queries.n_queries = 1
            self.get_paper_titles_from_db.max_results_per_query = 2
            self.extract_reference_titles.num_reference_paper = 1
            self.create_method.num_retrieve_related_papers = 1
            self.create_method.method_refinement_rounds = 0
            self.create_experimental_design.num_models_to_use = 1
            self.create_experimental_design.num_datasets_to_use = 1
            self.create_experimental_design.num_comparative_methods = 1
            self.retrieve_hugging_face.max_results_per_search = 2
            self.retrieve_hugging_face.max_models = 1
            self.retrieve_hugging_face.max_datasets = 1
            self.create_code.max_base_code_validations = 1
            self.create_code.max_experiment_code_validations = 1
            self.evaluate_experimental_consistency.consistency_score_threshold = 1
            self.create_bibfile.max_filtered_references = 2
            self.writer.writing_refinement_rounds = 1
            self.latex.max_chktex_revisions = 1
            self.latex.max_compile_revisions = 1
        elif self.profile == "prod":
            # 本番はリッチに
            self.generate_queries.n_queries = 6
            self.get_paper_titles_from_db.max_results_per_query = 8
            self.create_method.method_refinement_rounds = 2
            self.create_experimental_design.num_experiments = 3
        return self
