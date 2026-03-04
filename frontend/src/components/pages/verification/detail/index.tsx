import { useCallback, useMemo } from "react";
import { Loader } from "@/ui";
import type {
  ImplementationInfo,
  PaperDraft,
  ProposedMethod,
  Verification,
  VerificationPlan,
} from "../types";
import { ChatInput } from "./chat-input";
import { ExperimentDashboard } from "./experiment-dashboard";
import { ImplementationResult } from "./implementation-result";
import { PaperWritingSection } from "./paper-writing";
import { ProposedMethodsList } from "./proposed-methods";
import { TocNav } from "./toc-nav";
import { VerificationPlanView } from "./verification-plan";

const mockProposedMethods: ProposedMethod[] = [
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

const mockImplementation: ImplementationInfo = {
  githubUrl: "https://github.com/airas-org/exp-generated",
  fixedParameters: [
    { name: "random_seed", value: "42" },
    { name: "n_samples", value: "100" },
    { name: "significance_level", value: "0.05" },
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

const mockExperimentResult = {
  summary: "実験が正常に完了しました。統計的に有意な結果が得られました。",
  metrics: { accuracy: 0.89, p_value: 0.003, effect_size: 0.72 },
  details:
    "実験は正常に完了し、仮説を支持する結果が得られました。詳細な分析レポートを確認してください。",
};

interface VerificationDetailPageProps {
  verification: Verification | null;
  onUpdateVerification: (id: string, updates: Partial<Verification>) => void;
  onCreateWithMethod?: (sourceVerification: Verification, method: ProposedMethod) => void;
}

export function VerificationDetailPage({
  verification,
  onUpdateVerification,
  onCreateWithMethod,
}: VerificationDetailPageProps) {
  const handleChatSubmit = useCallback(
    (query: string) => {
      if (!verification) return;
      onUpdateVerification(verification.id, {
        query,
        title: query.slice(0, 30) + (query.length > 30 ? "..." : ""),
      });
      setTimeout(() => {
        onUpdateVerification(verification.id, {
          phase: "methods-proposed",
          proposedMethods: mockProposedMethods,
        });
      }, 1500);
    },
    [verification, onUpdateVerification],
  );

  const handleSelectMethod = useCallback(
    (methodId: string) => {
      if (!verification?.proposedMethods) return;
      const selected = verification.proposedMethods.find((m) => m.id === methodId);
      if (!selected) return;
      onUpdateVerification(verification.id, {
        selectedMethodId: methodId,
      });
      setTimeout(() => {
        const plan: VerificationPlan = {
          whatToVerify: selected.whatToVerify,
          method: selected.method,
        };
        onUpdateVerification(verification.id, {
          phase: "plan-generated",
          plan,
        });
      }, 1500);
    },
    [verification, onUpdateVerification],
  );

  const handleGenerateCode = useCallback(() => {
    if (!verification) return;
    onUpdateVerification(verification.id, { phase: "code-generating" });
    setTimeout(() => {
      onUpdateVerification(verification.id, {
        phase: "code-generated",
        implementation: mockImplementation,
      });
    }, 2000);
  }, [verification, onUpdateVerification]);

  const handleRunExperiment = useCallback(
    (experimentId: string) => {
      if (!verification?.implementation) return;
      const impl = verification.implementation;
      const updatedSettings = impl.experimentSettings.map((exp) =>
        exp.id === experimentId ? { ...exp, status: "running" as const } : exp,
      );
      onUpdateVerification(verification.id, {
        implementation: {
          ...impl,
          experimentSettings: updatedSettings,
        },
      });
      setTimeout(() => {
        const completedSettings = updatedSettings.map((exp) =>
          exp.id === experimentId
            ? { ...exp, status: "completed" as const, result: mockExperimentResult }
            : exp,
        );
        const allDone = completedSettings.every((exp) => exp.status === "completed");
        onUpdateVerification(verification.id, {
          phase: allDone ? "experiments-done" : "code-generated",
          implementation: {
            ...impl,
            experimentSettings: completedSettings,
          },
        });
      }, 3000);
    },
    [verification, onUpdateVerification],
  );

  const handleGeneratePaper = useCallback(
    (selectedExperimentIds: string[]) => {
      if (!verification) return;
      setTimeout(() => {
        const draft: PaperDraft = {
          title: `${verification.title}: A Comparative Study`,
          selectedExperimentIds,
          overleafUrl: "https://www.overleaf.com/project/mock-project-id-67890",
          status: "ready",
        };
        onUpdateVerification(verification.id, {
          phase: "paper-writing",
          paperDraft: draft,
        });
      }, 2000);
    },
    [verification, onUpdateVerification],
  );

  const tocEntries = useMemo(() => {
    if (!verification) return [];
    const hasProposedMethods =
      verification.proposedMethods && verification.proposedMethods.length > 0;
    const isDone =
      verification.phase === "experiments-done" || verification.phase === "paper-writing";
    const entries: { id: string; label: string }[] = [];
    if (hasProposedMethods) entries.push({ id: "sec-methods", label: "検証方針" });
    if (verification.plan) entries.push({ id: "sec-plan", label: "検証方法" });
    if (verification.implementation) {
      entries.push({ id: "sec-code", label: "実験コード" });
      entries.push({ id: "sec-settings", label: "実験設定" });
    }
    if (isDone) {
      entries.push({ id: "sec-dashboard", label: "実験結果" });
      entries.push({ id: "sec-paper", label: "論文執筆" });
    }
    return entries;
  }, [verification]);

  if (!verification) return null;

  const hasQuery = verification.phase !== "initial";
  const isGenerating = verification.phase === "code-generating";
  const showMethods = verification.proposedMethods && verification.proposedMethods.length > 0;
  const allExperimentsDone =
    verification.phase === "experiments-done" || verification.phase === "paper-writing";

  return (
    <div className="flex-1 flex flex-col overflow-y-auto">
      {!hasQuery && (
        <div className="flex-1 flex items-center justify-center p-6">
          <ChatInput onSubmit={handleChatSubmit} />
        </div>
      )}

      {hasQuery && (
        <div className="flex-1">
          {tocEntries.length > 0 && <TocNav entries={tocEntries} />}
          <div className="flex-1 p-6 lg:pr-28 space-y-6 max-w-4xl mx-auto w-full">
            <div className="border-b border-solid border-neutral-border pb-4">
              <h2 className="text-heading-3 font-heading-3 text-default-font">
                {verification.title}
              </h2>
              <p className="text-body font-body text-subtext-color mt-1">{verification.query}</p>
            </div>
            {showMethods && verification.proposedMethods && (
              <div id="sec-methods">
                <ProposedMethodsList
                  methods={verification.proposedMethods}
                  selectedMethodId={verification.selectedMethodId}
                  onSelectMethod={handleSelectMethod}
                  onCreateWithMethod={
                    onCreateWithMethod
                      ? (method) => onCreateWithMethod(verification, method)
                      : undefined
                  }
                />
              </div>
            )}
            {verification.selectedMethodId && !verification.plan && (
              <div className="flex items-center gap-2 px-3 py-4">
                <Loader size="small" />
                <span className="text-xs text-muted-foreground">
                  Generating verification plan...
                </span>
              </div>
            )}
            {verification.plan && (
              <div id="sec-plan">
                <VerificationPlanView
                  plan={verification.plan}
                  onGenerateCode={handleGenerateCode}
                  isGenerating={isGenerating}
                />
              </div>
            )}
            {verification.implementation && (
              <ImplementationResult
                implementation={verification.implementation}
                onRunExperiment={handleRunExperiment}
              />
            )}
            {allExperimentsDone && verification.implementation && (
              <div id="sec-dashboard">
                <ExperimentDashboard experiments={verification.implementation.experimentSettings} />
              </div>
            )}
            {allExperimentsDone && verification.implementation && (
              <div id="sec-paper">
                <PaperWritingSection
                  experiments={verification.implementation.experimentSettings}
                  paperDraft={verification.paperDraft}
                  onGeneratePaper={handleGeneratePaper}
                />
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
