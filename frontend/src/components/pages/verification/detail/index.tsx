import { useCallback, useMemo } from "react";
import { Loader } from "@/ui";
import {
  mockExperimentResultResponse,
  mockImplementationResponse,
  mockProposedMethodsResponse,
} from "../mock-data";
import type { PaperDraft, ProposedMethod, Verification, VerificationPlan } from "../types";
import { ChatInput } from "./chat-input";
import { ExperimentDashboard } from "./experiment-dashboard";
import { ImplementationResult } from "./implementation-result";
import { PaperWritingSection } from "./paper-writing";
import { ProposedMethodsList } from "./proposed-methods";
import { TocNav } from "./toc-nav";
import { VerificationPlanView } from "./verification-plan";

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
          proposedMethods: mockProposedMethodsResponse,
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
        implementation: mockImplementationResponse,
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
            ? { ...exp, status: "completed" as const, result: mockExperimentResultResponse }
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
    const anyCompleted = verification.implementation?.experimentSettings.some(
      (exp) => exp.status === "completed",
    );
    const entries: { id: string; label: string }[] = [];
    if (hasProposedMethods) entries.push({ id: "sec-methods", label: "検証方針" });
    if (verification.plan) entries.push({ id: "sec-plan", label: "検証方法" });
    if (verification.implementation) {
      entries.push({ id: "sec-code", label: "実験コード" });
      entries.push({ id: "sec-settings", label: "実験設定" });
    }
    if (anyCompleted) {
      entries.push({ id: "sec-dashboard", label: "実験結果" });
    }
    if (anyCompleted) {
      entries.push({ id: "sec-paper", label: "論文執筆" });
    }
    return entries;
  }, [verification]);

  if (!verification) return null;

  const hasQuery = verification.phase !== "initial";
  const isGenerating = verification.phase === "code-generating";
  const showMethods = verification.proposedMethods && verification.proposedMethods.length > 0;
  const hasAnyCompleted = verification.implementation?.experimentSettings.some(
    (exp) => exp.status === "completed",
  );

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
                  showButton={!isGenerating && !verification.implementation}
                />
              </div>
            )}
            {isGenerating && (
              <div className="flex items-center gap-2 px-3 py-4">
                <Loader size="small" />
                <span className="text-xs text-muted-foreground">Generating experiment code...</span>
              </div>
            )}
            {verification.implementation && (
              <ImplementationResult
                implementation={verification.implementation}
                onRunExperiment={handleRunExperiment}
              />
            )}
            {hasAnyCompleted && verification.implementation && (
              <div id="sec-dashboard">
                <ExperimentDashboard experiments={verification.implementation.experimentSettings} />
              </div>
            )}
            {hasAnyCompleted && verification.implementation && (
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
