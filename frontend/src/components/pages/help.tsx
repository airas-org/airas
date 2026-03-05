"use client";

import { FeatherBookOpen, FeatherGitBranch, FeatherPlay, FeatherSettings } from "@subframe/core";
import { Accordion } from "@/ui/components/Accordion";

const gettingStartedSteps = [
  {
    title: "1. 検証を作成する",
    description:
      "サイドバーの「新規検証」ボタンから検証を作成します。検証したい仮説や研究テーマを入力すると、AIが関連論文の検索と検証方針の提案を行います。",
  },
  {
    title: "2. 検証方針を選択する",
    description:
      "AIが複数の検証方針を提示します。各方針のPros/Consを比較して、最適な方針を選択してください。",
  },
  {
    title: "3. 実験を実行する",
    description:
      "選択した検証方針に基づいて実験コードが生成されます。パラメータを設定して実験を実行し、結果を確認します。",
  },
  {
    title: "4. 論文を執筆する",
    description:
      "実験結果をもとに、AIが論文ドラフトを生成します。Overleafと連携して編集を続けることもできます。",
  },
];

const featureGuides = [
  {
    icon: <FeatherPlay />,
    title: "検証ワークフロー",
    items: [
      {
        question: "検証の各フェーズについて",
        answer:
          "検証は「検証方針 → 検証方法 → 実験コード → 実験設定 → 実験結果 → 情報収集 → 論文」の順に進みます。各フェーズは検証一覧ページでカテゴリ別に確認できます。",
      },
      {
        question: "検証を途中から再開できますか？",
        answer:
          "はい、検証一覧ページから検証を選択すると、前回の状態から再開できます。各フェーズの結果は自動的に保存されています。",
      },
    ],
  },
  {
    icon: <FeatherGitBranch />,
    title: "自動研究（Topic-Driven / Hypothesis-Driven）",
    items: [
      {
        question: "Topic-Driven と Hypothesis-Driven の違い",
        answer:
          "Topic-Drivenは研究テーマを入力すると、AIが自動的に仮説生成から論文執筆まで一貫して行います。Hypothesis-Drivenは既に検証したい仮説がある場合に、その仮説に基づいて実験と論文執筆を行います。",
      },
      {
        question: "GitHub / W&B の設定は必須ですか？",
        answer:
          "はい、実験コードの管理にGitHubリポジトリ、実験メトリクスの記録にWeights & Biasesが必要です。それぞれのアカウントを事前にご用意ください。",
      },
    ],
  },
  {
    icon: <FeatherSettings />,
    title: "インテグレーション設定",
    items: [
      {
        question: "APIキーの設定方法",
        answer:
          "Settings > Integrationページから各サービスのAPIキーを設定できます。OpenAI、Anthropic、Google等のLLM APIキーと、GitHub Personal Access Tokenが必要です。",
      },
      {
        question: "LLMモデルのカスタマイズ",
        answer:
          "自動研究の詳細設定で、各プロセス（論文検索、仮説生成、コード生成等）に使用するLLMモデルを個別に指定できます。",
      },
    ],
  },
  {
    icon: <FeatherBookOpen />,
    title: "論文関連",
    items: [
      {
        question: "対応しているLaTeXテンプレート",
        answer:
          "現在、MDPI、ICLR 2024、Agents4Science 2025のテンプレートに対応しています。詳細設定から選択できます。",
      },
      {
        question: "生成された論文の編集方法",
        answer:
          "論文はGitHubリポジトリに保存されます。PDFリンクから確認でき、「Edit on Overleaf」ボタンからOverleafで直接編集することもできます。",
      },
    ],
  },
];

const faqItems = [
  {
    question: "AIRASは無料で利用できますか？",
    answer:
      "基本的な機能は無料でご利用いただけます。月間の検証回数やAIモデルの選択に制限がありますが、有料プランにアップグレードすることで制限を解除できます。",
  },
  {
    question: "データのプライバシーは保護されていますか？",
    answer:
      "すべてのデータは暗号化された通信で転送され、セキュアなクラウドインフラストラクチャに保管されます。ユーザーの研究データは他のユーザーと共有されることはありません。",
  },
  {
    question: "バグや問題を見つけた場合はどうすればいいですか？",
    answer:
      "サイドバーの「お問い合わせ」ページからバグ報告を送信していただくか、GitHubのIssuesページで報告してください。",
  },
];

export function HelpPage() {
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-5xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font">ヘルプ</h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          AIRASの使い方や各機能について
        </p>

        <div className="mt-6 space-y-6">
          {/* Getting Started */}
          <div className="rounded-lg border border-border bg-card p-5">
            <h2 className="text-body-bold font-body-bold text-default-font mb-3">
              はじめに — 基本的な使い方
            </h2>
            <div className="grid gap-3 md:grid-cols-2">
              {gettingStartedSteps.map((step) => (
                <div key={step.title} className="rounded-md bg-neutral-50 p-3">
                  <p className="text-sm font-semibold text-default-font">{step.title}</p>
                  <p className="text-caption font-caption text-subtext-color mt-1">
                    {step.description}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Feature Guides */}
          {featureGuides.map((guide) => (
            <div key={guide.title} className="rounded-lg border border-border bg-card p-5">
              <h2 className="text-body-bold font-body-bold text-default-font mb-3 flex items-center gap-2">
                <span className="text-subtext-color">{guide.icon}</span>
                {guide.title}
              </h2>
              <div className="flex flex-col gap-1">
                {guide.items.map((item) => (
                  <Accordion
                    key={item.question}
                    trigger={
                      <div className="flex w-full items-center justify-between rounded-md px-3 py-2 hover:bg-neutral-50">
                        <span className="text-body font-body text-default-font pr-2">
                          {item.question}
                        </span>
                        <Accordion.Chevron />
                      </div>
                    }
                  >
                    <p className="text-caption font-caption text-subtext-color px-3 pb-2 leading-relaxed">
                      {item.answer}
                    </p>
                  </Accordion>
                ))}
              </div>
            </div>
          ))}

          {/* FAQ */}
          <div className="rounded-lg border border-border bg-card p-5">
            <h2 className="text-body-bold font-body-bold text-default-font mb-3">よくある質問</h2>
            <div className="flex flex-col gap-1">
              {faqItems.map((item) => (
                <Accordion
                  key={item.question}
                  trigger={
                    <div className="flex w-full items-center justify-between rounded-md px-3 py-2 hover:bg-neutral-50">
                      <span className="text-body font-body text-default-font pr-2">
                        {item.question}
                      </span>
                      <Accordion.Chevron />
                    </div>
                  }
                >
                  <p className="text-caption font-caption text-subtext-color px-3 pb-2 leading-relaxed">
                    {item.answer}
                  </p>
                </Accordion>
              ))}
            </div>
          </div>

          {/* External Links */}
          <div className="flex gap-3">
            <a
              href="https://airas-org.github.io/airas/"
              target="_blank"
              rel="noreferrer"
              className="flex-1 rounded-lg border border-border bg-card p-4 hover:bg-neutral-50 transition-colors"
            >
              <p className="text-sm font-semibold text-default-font">ドキュメント</p>
              <p className="text-caption font-caption text-subtext-color mt-1">
                詳しい技術ドキュメントはこちら
              </p>
            </a>
            <a
              href="https://discord.gg/KGm5FGY5"
              target="_blank"
              rel="noreferrer"
              className="flex-1 rounded-lg border border-border bg-card p-4 hover:bg-neutral-50 transition-colors"
            >
              <p className="text-sm font-semibold text-default-font">Discordコミュニティ</p>
              <p className="text-caption font-caption text-subtext-color mt-1">
                コミュニティで質問や議論ができます
              </p>
            </a>
            <a
              href="https://github.com/airas-org/airas"
              target="_blank"
              rel="noreferrer"
              className="flex-1 rounded-lg border border-border bg-card p-4 hover:bg-neutral-50 transition-colors"
            >
              <p className="text-sm font-semibold text-default-font">GitHub</p>
              <p className="text-caption font-caption text-subtext-color mt-1">
                ソースコードとIssue管理
              </p>
            </a>
          </div>
        </div>
      </div>
    </div>
  );
}
