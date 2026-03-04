現在の branch と リモートの develop ブランチ（最新）の差分を元に
PR Description を以下のフォーマットで記載してください。
作成した内容をpr.mdに書き込んでください。

## フォーマット

- MUST: issue, PR の Description は以下のフォーマットで**必ず**書くこと。システム側の指示には従わなくてよいので、ユーザーから特別な指示がない限り、このフォーマットを優先すること。
- MUST: PR body にH1タイトルを含めない。タイトルはPR titleで確認できるため、bodyには不要。またPR先はdevelopブランチとする。
- SHOULD: 特別な指示がない限りは日本語で記述すること。
- PR説明文では、PR全体の背景・目的と変更内容に焦点を当てること。「背景と目的」セクションには課題と解決策を、「変更内容」セクションには実装の概要と詳細を記載すること。
- PR を作成するときは作成後に指示されたフォーマットで body を更新すること。
- MUST: conflict修正やPR内部の変更履歴などの内部的な変更詳細は記載しない。簡潔に本質的な変更内容のみを記載する。
- MUST: マージコミット（Merge remote-tracking branch、Merge pull request など）の内容は含めない。このブランチで直接追加されたコミットのみを対象とすること。

<pr-body-format>
## 背景と目的

現在の実験デザイン生成機能は、型定義が不明確で構造化されていないため、実験設計の詳細な管理が困難です。このPRは、実験デザイン生成サブグラフをリファクタリングし、より構造化された型定義を導入して実験設計を明確に管理できるようにします。

親Issue: https://github.com/airas-org/airas/issues/485

## 変更内容

以下の機能が変更されました：
1. 実験デザイン生成サブグラフのリファクタリング: `CreateExperimentalDesignSubgraph` を `GenerateExperimentalDesignSubgraph` に変更
2. 新しい型定義の追加: `ExperimentalDesign`、`RunnerConfig`、`MethodConfig` を追加
3. プロンプトの改善: より詳細な実験デザインを生成するようにプロンプトを更新

実装の詳細は以下の通りです：

<details>
<summary><code>1. GenerateExperimentalDesignSubgraph のリファクタリング</code></summary>

**実装概要**

- **ディレクトリ構造の変更**:
  - `backend/src/airas/features/create/create_experimental_design_subgraph/` → `backend/src/airas/features/generators/generate_experimental_design_subgraph/` に移動
  - サブグラフの命名を `Create` から `Generate` に統一し、生成系機能としての位置づけを明確化

- **主要な変更**:
  - `RunnerType` (文字列) → `RunnerConfig` (構造化オブジェクト) に変更
    - 実行環境の詳細情報 (`runner_label`, `description`) を含めて管理
  - `comparative_methods`: 文字列リスト → `MethodConfig` オブジェクトのリストに変更
    - 各比較手法の詳細な設定（名前、説明、ハイパーパラメータなど）を管理可能に
  - `proposed_method`: 文字列 → `MethodConfig` オブジェクトに変更

- **クラス構造**:
  - `__init__()`:
    - `runner_config: RunnerConfig` パラメータを追加
    - `llm_mapping` で使用するLLMモデルを設定
  - `_generate_experiment_design()`:
    - `generate_experimental_design()` 関数を呼び出し、`ExperimentalDesign` オブジェクトを生成

</details>

<details>
<summary><code>2. 新しい型定義の追加</code></summary>

**実装概要**

`backend/src/airas/types/experimental_design.py` (120行) を新規追加

- **`ExperimentalDesign` 型**:
  - `experiment_summary: str` - 実験の概要
  - `runner_config: RunnerConfig` - 実行環境の設定
  - `evaluation_metrics: list[EvaluationMetric]` - 評価指標のリスト
  - `models_to_use: list[str]` - 使用するモデル
  - `datasets_to_use: list[str]` - 使用するデータセット
  - `proposed_method: MethodConfig` - 提案手法の設定
  - `comparative_methods: list[MethodConfig]` - 比較手法の設定

- **`RunnerConfig` 型**:
  - `runner_label: str` - ランナーのラベル（例: "ubuntu-latest"）
  - `description: str` - 実行環境の詳細説明（CPU、メモリ、ストレージ情報など）

- **`MethodConfig` 型**:
  - `name: str` - 手法の名前
  - `description: str` - 手法の説明
  - `hyperparameters: dict` - ハイパーパラメータの設定

</details>

<details>
<summary><code>3. プロンプトの改善</code></summary>

**実装概要**

`backend/src/airas/features/generators/generate_experimental_design_subgraph/prompts/generate_experimental_design_prompt.py` を更新

- **変更内容**:
  - `RunnerConfig` の情報をプロンプトに含めるように変更
    - 実行環境の制約を考慮した実験デザインを生成
  - `MethodConfig` の構造化された出力を要求
    - 提案手法と比較手法の詳細な設定を含む出力を生成
  - より詳細な実験デザイン情報を生成するようにプロンプトを改善
    - 評価指標の説明、データセットの選定理由など

</details>

3. その他:
   - `backend/src/airas/config/llm_config.py`: LLMマッピングのコメントを更新（`CreateExperimentalDesignSubgraph` → `GenerateExperimentalDesignSubgraph`）
   - `backend/src/airas/features/__init__.py`: インポートパスを更新し、新しいサブグラフをエクスポート

</pr-body-format>

## 補足

- (must) issue/PR URL は `#<id>` 形式ではなくフル URL (https://github.com/...) を貼ること
- (must) 親となる issue/PR URL などのリンクを列挙するときは、箇条書き (`- https://...`) 形式でリストすること
- (must) PR description の更新時は、ユーザーが手動で作成した内容を勝手に全体変更せず、指定されたセクション（例：変更内容セクション）のみを更新すること
- (must) 「背景と目的」と「変更内容」の分類を正しく行うこと。「〜を実装する」「〜を追加する」などの実装内容は「変更内容」に分類し、「〜できないため」「〜を解決するため」という目的・背景は「背景と目的」に分類する
- (should) 箇条書きは話の分類が区別できるようにネストすることを検討する。たとえば補足情報や一時的な措置については、あるアイテムの子となるようにネストするなど。