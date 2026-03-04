import type { ExperimentResult, ImplementationInfo, ProposedMethod, Verification } from "./types";

const sharedProposedMethods: ProposedMethod[] = [
  {
    id: "method-1",
    title: "GLUEベンチマーク上での体系的比較",
    whatToVerify:
      "Sparse Attention（Top-k, Local+Global）を適用したTransformerモデルが、Full Attentionモデルと比較して推論速度・メモリ使用量でどの程度改善されるか。",
    method:
      "BERT-baseモデルをベースに、Full Attention, Top-k Sparse Attention, Local+Global Attentionの3パターンを実装し、GLUE benchmarkのSST-2タスクで精度・推論時間・メモリ使用量を比較する。シーケンス長128, 256, 512で測定。",
    pros: [
      "標準ベンチマークでの比較のため再現性が高い",
      "複数のシーケンス長での比較が可能",
      "先行研究との直接的な比較が容易",
    ],
    cons: [
      "SST-2は比較的短いテキストが多く、長文での優位性が見えにくい",
      "BERT-baseは比較的小さなモデルのため、大規模モデルでの効果は不明",
    ],
  },
  {
    id: "method-2",
    title: "長文テキストでのスケーラビリティ検証",
    whatToVerify:
      "シーケンス長を1024〜4096まで増加させた場合のSparse Attentionの速度・メモリ優位性のスケール特性。",
    method:
      "カスタムの長文テキストデータセットを用いて、シーケンス長1024, 2048, 4096でFull AttentionとSparse Attentionの推論時間・メモリ使用量を測定。精度よりもスケーラビリティに焦点。",
    pros: [
      "Sparse Attentionの真の優位性が出やすいシナリオ",
      "実用的なユースケースに直結",
      "O(n^2) vs O(n)の理論的予測を実証可能",
    ],
    cons: [
      "カスタムデータセットのため比較基準が曖昧",
      "GPUメモリの制約で実験条件が限定される可能性",
    ],
  },
  {
    id: "method-3",
    title: "アブレーションスタディ: Attention密度と精度の関係",
    whatToVerify:
      "Top-kのk値やLocal windowサイズを変化させた場合の精度と計算コストのトレードオフ曲線。",
    method:
      "BERT-baseとSST-2を用いて、Top-k AttentionのkをN/16, N/8, N/4, N/2と変化させ、またLocal windowサイズを32, 64, 128, 256と変化させた場合の精度と推論速度を測定。パレートフロンティアを描画。",
    pros: [
      "ハイパーパラメータの実用的な指針が得られる",
      "視覚的にわかりやすい結果が期待できる",
      "新規性が高く論文化しやすい",
    ],
    cons: ["実験数が多くなり計算時間がかかる", "パラメータ空間の網羅が不完全になる可能性"],
  },
];

/** Mock data used by detail/index.tsx when a new verification query is submitted */
export const mockProposedMethodsResponse: ProposedMethod[] = [
  {
    id: "pm-1",
    title: "対照実験による統計的検証",
    whatToVerify:
      "入力されたクエリに基づく仮説の検証。実験条件を変えた場合の結果の変動を測定し、統計的有意性を確認する。",
    method:
      "対照実験を設計し、独立変数を操作した3つの実験条件を設定。各条件でN=100のサンプルサイズで実験を実施し、ANOVA分析で条件間の有意差を検定。",
    pros: ["統計的に堅牢な結果が得られる", "先行研究との比較が容易", "再現性が高い"],
    cons: ["サンプルサイズが限定的", "実験条件が3つのみ"],
  },
  {
    id: "pm-2",
    title: "ベイズ推論を用いた適応的実験",
    whatToVerify:
      "同じ仮説をベイズ的アプローチで検証し、事前分布の設定が結果に与える影響を分析する。",
    method:
      "ベイズ推論フレームワークを構築し、事前分布を3パターン設定。MCMC法でパラメータを推定し、ベイズファクターで仮説を評価。",
    pros: ["事前知識を活用できる", "逐次的にデータを追加可能", "信用区間で不確実性を表現"],
    cons: ["事前分布の設定に恣意性がある", "計算コストが高い"],
  },
];

export const mockImplementationResponse: ImplementationInfo = {
  githubUrl: "https://github.com/airas-org/exp-generated",
  fixedParameters: [
    { name: "random_seed", description: "再現性を確保するための乱数シード値" },
    { name: "n_samples", description: "各実験条件ごとのサンプルサイズ" },
    { name: "significance_level", description: "統計的有意性の判定閾値（p値）" },
  ],
  experimentSettings: [
    {
      id: "exp-new-1",
      title: "条件A（対照群）",
      description: "標準的な条件でのベースライン測定。",
      parameters: [{ name: "condition", value: "control" }],
      status: "pending",
    },
    {
      id: "exp-new-2",
      title: "条件B（実験群1）",
      description: "変数Xを増加させた条件での測定。",
      parameters: [
        { name: "condition", value: "treatment_1" },
        { name: "factor_x", value: "2.0" },
      ],
      status: "pending",
    },
    {
      id: "exp-new-3",
      title: "条件C（実験群2）",
      description: "変数Xを最大化した条件での測定。",
      parameters: [
        { name: "condition", value: "treatment_2" },
        { name: "factor_x", value: "4.0" },
      ],
      status: "pending",
    },
  ],
};

export const mockExperimentResultResponse: ExperimentResult = {
  summary: "実験が正常に完了しました。統計的に有意な結果が得られました。",
  metrics: { accuracy: 0.89, p_value: 0.003, effect_size: 0.72 },
  details:
    "実験は正常に完了し、仮説を支持する結果が得られました。詳細な分析レポートを確認してください。",
};

export const mockVerifications: Verification[] = [
  {
    id: "v-1",
    title: "Transformer Attention機構の効率化検証",
    query:
      "Sparse Attentionを用いたTransformerモデルの推論速度改善について、従来のFull Attentionと比較してどの程度の効率化が可能か検証したい",
    createdAt: new Date("2026-02-28"),
    phase: "experiments-done",
    proposedMethods: sharedProposedMethods,
    selectedMethodId: "method-1",
    plan: {
      whatToVerify:
        "Sparse Attention（Top-k, Local+Global）を適用したTransformerモデルが、Full Attentionモデルと比較して推論速度・メモリ使用量でどの程度改善されるか。精度の低下が許容範囲内に収まるか。",
      method:
        "BERT-baseモデルをベースに、Full Attention, Top-k Sparse Attention, Local+Global Attentionの3パターンを実装し、GLUE benchmarkのSST-2タスクで精度・推論時間・メモリ使用量を比較する。シーケンス長128, 256, 512で測定。",
    },
    implementation: {
      githubUrl: "https://github.com/airas-org/exp-sparse-attention",
      fixedParameters: [
        { name: "model_base", description: "事前学習済みBERT-base-uncasedモデルを使用" },
        { name: "dataset", description: "GLUE BenchmarkのSST-2感情分析タスク" },
        { name: "batch_size", description: "学習・推論時のミニバッチサイズ" },
        { name: "epochs", description: "全データを3回学習するエポック数" },
      ],
      experimentSettings: [
        {
          id: "exp-1-1",
          title: "Full Attention (ベースライン)",
          description:
            "標準的なFull Attentionメカニズムでの実験。比較対象のベースラインとして使用。",
          parameters: [
            { name: "attention_type", value: "full" },
            { name: "seq_length", value: "256" },
          ],
          status: "completed",
          result: {
            summary: "ベースラインとして安定した結果。精度92.3%、推論時間45ms/batch。",
            metrics: {
              accuracy: 0.923,
              inference_time_ms: 45,
              memory_mb: 1240,
              f1_score: 0.921,
            },
            details:
              "Full Attentionモデルはシーケンス長256で安定した性能を示した。O(n^2)の計算量により、長いシーケンスではメモリ使用量が顕著に増加する傾向がある。",
          },
        },
        {
          id: "exp-1-2",
          title: "Top-k Sparse Attention",
          description: "各トークンが上位k個のアテンションスコアのみを保持するSparse Attention。",
          parameters: [
            { name: "attention_type", value: "top_k_sparse" },
            { name: "seq_length", value: "256" },
            { name: "top_k", value: "64" },
          ],
          status: "completed",
          result: {
            summary: "推論時間28%削減、メモリ18%削減。精度は0.8%低下のみ。",
            metrics: {
              accuracy: 0.915,
              inference_time_ms: 32,
              memory_mb: 1017,
              f1_score: 0.913,
            },
            details:
              "Top-k=64での実験では、精度の低下を最小限に抑えつつ推論速度とメモリ効率を大幅に改善。k値のチューニングにより精度と効率のトレードオフを調整可能。",
          },
        },
        {
          id: "exp-1-3",
          title: "Local+Global Sparse Attention",
          description:
            "ローカルウィンドウ内のAttentionとグローバルトークンへのAttentionを組み合わせたハイブリッド方式。",
          parameters: [
            { name: "attention_type", value: "local_global" },
            { name: "seq_length", value: "256" },
            { name: "local_window", value: "64" },
            { name: "global_tokens", value: "16" },
          ],
          status: "completed",
          result: {
            summary: "推論時間35%削減、メモリ25%削減。精度低下は0.5%と最小。",
            metrics: {
              accuracy: 0.918,
              inference_time_ms: 29,
              memory_mb: 930,
              f1_score: 0.916,
            },
            details:
              "Local+Global方式が最も効率的な結果を示した。ローカルウィンドウが局所的な依存関係を捉え、グローバルトークンが文全体のコンテキストを維持する。長いシーケンスでの優位性がさらに顕著になると予想される。",
          },
        },
      ],
    },
    paperDraft: {
      title: "Sparse Attention Mechanisms for Efficient Transformer Inference: A Comparative Study",
      selectedExperimentIds: ["exp-1-1", "exp-1-2", "exp-1-3"],
      overleafUrl: "https://www.overleaf.com/project/mock-project-id-12345",
      status: "ready",
    },
  },
  {
    id: "v-2",
    title: "データ拡張手法による小規模データセットの性能改善",
    query:
      "画像分類タスクにおいて、MixupとCutMixのデータ拡張手法が小規模データセット（1000枚以下）での性能改善にどの程度効果があるか検証したい",
    createdAt: new Date("2026-03-01"),
    phase: "code-generated",
    proposedMethods: [
      {
        id: "method-aug-1",
        title: "CIFAR-10サブセットでの体系的比較",
        whatToVerify:
          "MixupおよびCutMixデータ拡張手法が、小規模画像データセット（CIFAR-10のサブセット）でのResNetモデルの分類精度向上にどの程度寄与するか。",
        method:
          "CIFAR-10から500枚、1000枚のサブセットを作成し、データ拡張なし、Mixup、CutMix、Mixup+CutMixの4条件でResNet-18を学習。テストセット精度とオーバーフィッティングの程度を比較。",
        pros: ["複数のデータサイズでの比較", "組み合わせ効果も検証可能"],
        cons: ["CIFAR-10は比較的単純なデータセット"],
      },
    ],
    selectedMethodId: "method-aug-1",
    plan: {
      whatToVerify:
        "MixupおよびCutMixデータ拡張手法が、小規模画像データセット（CIFAR-10のサブセット）でのResNetモデルの分類精度向上にどの程度寄与するか。",
      method:
        "CIFAR-10から500枚、1000枚のサブセットを作成し、データ拡張なし、Mixup、CutMix、Mixup+CutMixの4条件でResNet-18を学習。テストセット精度とオーバーフィッティングの程度を比較。",
    },
    implementation: {
      githubUrl: "https://github.com/airas-org/exp-data-augmentation",
      fixedParameters: [
        { name: "model", description: "18層のResidual Networkアーキテクチャ" },
        { name: "dataset", description: "CIFAR-10から1000枚を抽出したサブセット" },
        { name: "learning_rate", description: "Adam optimizerの初期学習率" },
        { name: "epochs", description: "収束を確認するための十分なエポック数" },
      ],
      experimentSettings: [
        {
          id: "exp-2-1",
          title: "ベースライン（拡張なし）",
          description:
            "データ拡張を行わない標準的な学習。オーバーフィッティングのベースラインを測定。",
          parameters: [
            { name: "augmentation", value: "none" },
            { name: "dataset_size", value: "1000" },
          ],
          status: "pending",
        },
        {
          id: "exp-2-2",
          title: "Mixup拡張",
          description: "2つの画像とラベルを線形補間で混合するMixup手法を適用。",
          parameters: [
            { name: "augmentation", value: "mixup" },
            { name: "dataset_size", value: "1000" },
            { name: "mixup_alpha", value: "0.2" },
          ],
          status: "pending",
        },
        {
          id: "exp-2-3",
          title: "CutMix拡張",
          description: "画像の一部を別の画像で置換し、ラベルを面積比で混合するCutMix手法を適用。",
          parameters: [
            { name: "augmentation", value: "cutmix" },
            { name: "dataset_size", value: "1000" },
            { name: "cutmix_alpha", value: "1.0" },
          ],
          status: "pending",
        },
      ],
    },
  },
  {
    id: "v-3",
    title: "学習率スケジューラの比較研究",
    query:
      "Cosine AnnealingとWarm Restarts付きCosine Annealingの学習率スケジューラが、画像分類の収束速度と最終精度に与える影響を比較したい",
    createdAt: new Date("2026-03-02"),
    phase: "methods-proposed",
    proposedMethods: [
      {
        id: "method-lr-1",
        title: "CIFAR-100上でのスケジューラ3種比較",
        whatToVerify:
          "Cosine Annealing学習率スケジューラとSGDR（Warm Restarts）が、Step Decayスケジューラと比較して収束速度と最終精度でどのような差異を示すか。",
        method:
          "ResNet-50をCIFAR-100で学習し、Step Decay、Cosine Annealing、SGDRの3つのスケジューラを比較。各エポックの学習曲線、最終テスト精度、収束までのエポック数を記録・分析。",
        pros: ["実用的な比較が可能", "学習曲線の可視化で直感的に理解しやすい"],
        cons: ["CIFAR-100のみでは一般化が難しい"],
      },
      {
        id: "method-lr-2",
        title: "異なるモデルサイズでの効果検証",
        whatToVerify:
          "モデルサイズ（ResNet-18, 50, 101）によってスケジューラの効果に差異があるか。",
        method:
          "3つのResNet変種それぞれで3つのスケジューラを適用し、計9条件を比較。モデルサイズとスケジューラの交互作用を分析。",
        pros: ["一般化可能性が高い", "交互作用効果の発見が期待できる"],
        cons: ["計算コストが9倍", "結果の解釈が複雑"],
      },
    ],
  },
  {
    id: "v-4",
    title: "新規検証",
    query: "",
    createdAt: new Date("2026-03-03"),
    phase: "initial",
  },
];
