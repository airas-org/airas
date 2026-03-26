import type React from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { GenerateVerificationCodeRequestBody } from "@/lib/api/models/GenerateVerificationCodeRequestBody";
import { VerificationService } from "@/lib/api/services/VerificationService";
import { Loader } from "@/ui";
import { mockExperimentResultResponse } from "../mock-data";
import type { PaperDraft, ProposedMethod, Verification, VerificationMethod } from "../types";
import { ChatInput } from "./chat-input";
import { ExperimentDashboard } from "./experiment-dashboard";
import { ImplementationResult } from "./implementation-result";
import { PaperWritingSection } from "./paper-writing";
import { ProposedMethodsList } from "./proposed-methods";
import { TocNav } from "./toc-nav";
import { VerificationPlanView } from "./verification-plan";

interface UserInputCardProps {
  query: string;
  title: string;
  onTitleChange: (title: string) => void;
}

function UserInputCard({ query, title, onTitleChange }: UserInputCardProps) {
  const { t } = useTranslation();
  const [draft, setDraft] = useState(title);

  useEffect(() => {
    setDraft(title);
  }, [title]);

  const handleBlur = () => {
    const trimmed = draft.trim();
    if (trimmed && trimmed !== title) {
      onTitleChange(trimmed);
    } else if (!trimmed) {
      setDraft(title);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      e.currentTarget.blur();
    } else if (e.key === "Escape") {
      setDraft(title);
      e.currentTarget.blur();
    }
  };

  return (
    <div className="space-y-2">
      <input
        type="text"
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onBlur={handleBlur}
        onKeyDown={handleKeyDown}
        placeholder={t("verification.detail.userInput.titlePlaceholder")}
        className="w-full text-heading-3 font-heading-3 text-default-font bg-transparent border-none outline-none focus:ring-0 placeholder:text-neutral-400"
      />
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="text-lg font-semibold text-foreground">
          {t("verification.detail.userInput.cardTitle")}
        </h2>
        <p className="text-sm text-muted-foreground mt-1">{query}</p>
      </div>
    </div>
  );
}

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
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [isPaperGenerating, setIsPaperGenerating] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const pollingTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const isPollingRef = useRef(false);

  const stopPolling = useCallback(() => {
    isPollingRef.current = false;
    if (pollingTimerRef.current !== null) {
      clearTimeout(pollingTimerRef.current);
      pollingTimerRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  const startPolling = useCallback(
    (workflowRunId: number, repositoryName: string, verificationId: string) => {
      stopPolling();
      isPollingRef.current = true;

      const poll = async () => {
        if (!isPollingRef.current) return;

        try {
          const data =
            await VerificationService.getVerificationCodeStatusAirasV1VerificationCodeStatusRepositoryNameWorkflowRunIdGet(
              repositoryName,
              workflowRunId,
            );

          if (!isPollingRef.current) return;

          onUpdateVerification(verificationId, {
            codeGenerationStatus: data.status,
            codeGenerationConclusion: data.conclusion ?? null,
          });

          if (data.status === "completed" || data.conclusion != null) {
            stopPolling();
            onUpdateVerification(verificationId, { phase: "code-generated" });
            return;
          }
        } catch {
          // ignore transient errors during polling
        }

        if (isPollingRef.current) {
          pollingTimerRef.current = setTimeout(poll, 10000);
        }
      };

      poll();
    },
    [onUpdateVerification, stopPolling],
  );

  // Resume polling when returning to a verification that is still generating
  useEffect(() => {
    if (
      verification?.phase === "code-generating" &&
      verification.workflowRunId &&
      verification.repositoryName
    ) {
      startPolling(verification.workflowRunId, verification.repositoryName, verification.id);
    }
  }, [
    verification?.id,
    verification?.phase,
    verification?.workflowRunId,
    verification?.repositoryName,
    startPolling,
  ]);

  const handleChatSubmit = useCallback(
    async (query: string) => {
      if (!verification) return;
      setErrorMessage(null);
      onUpdateVerification(verification.id, {
        query,
        phase: "proposing-policies",
      });

      try {
        const data =
          await VerificationService.proposePoliciesAirasV1VerificationProposePoliciesPost({
            user_query: query,
            verification_id: verification.id,
          });

        if (!data.feasible) {
          setErrorMessage(data.infeasible_reason ?? "This query is not feasible for verification.");
          return;
        }

        const methods: ProposedMethod[] = data.proposed_methods.map((m) => ({
          id: m.id,
          title: m.title,
          whatToVerify: m.what_to_verify,
          method: m.method,
          pros: m.pros ?? [],
          cons: m.cons ?? [],
        }));

        onUpdateVerification(verification.id, {
          phase: "methods-proposed",
          proposedMethods: methods,
        });
      } catch (err) {
        setErrorMessage(err instanceof Error ? err.message : "An unexpected error occurred.");
      }
    },
    [verification, onUpdateVerification],
  );

  const handleSelectMethod = useCallback(
    async (methodId: string) => {
      if (!verification?.proposedMethods) return;
      const selected = verification.proposedMethods.find((m) => m.id === methodId);
      if (!selected) return;

      onUpdateVerification(verification.id, { selectedMethodId: methodId });

      try {
        const data = await VerificationService.generateMethodAirasV1VerificationGenerateMethodPost({
          user_query: verification.query,
          selected_policy: {
            id: selected.id,
            title: selected.title,
            what_to_verify: selected.whatToVerify,
            method: selected.method,
            pros: selected.pros,
            cons: selected.cons,
          },
          verification_id: verification.id,
        });

        const verificationMethod: VerificationMethod = {
          whatToVerify: data.what_to_verify,
          experimentSettings: data.experiment_settings,
          steps: data.steps,
        };

        onUpdateVerification(verification.id, {
          phase: "plan-generated",
          verificationMethod,
        });
      } catch (err) {
        setErrorMessage(err instanceof Error ? err.message : "An unexpected error occurred.");
      }
    },
    [verification, onUpdateVerification],
  );

  const handleGenerateCode = useCallback(
    async (
      modificationNotes: string,
      repositoryName: string,
      updatedSettings: Record<string, string>,
    ) => {
      if (!verification?.verificationMethod) return;

      const updatedMethod: VerificationMethod = {
        ...verification.verificationMethod,
        experimentSettings: updatedSettings,
      };

      onUpdateVerification(verification.id, {
        phase: "code-generating",
        modificationNotes,
        repositoryName,
        verificationMethod: updatedMethod,
      });

      try {
        const data =
          await VerificationService.generateVerificationCodeAirasV1VerificationGenerateCodePost({
            user_query: verification.query,
            what_to_verify: updatedMethod.whatToVerify,
            experiment_settings: updatedMethod.experimentSettings,
            steps: updatedMethod.steps,
            modification_notes: modificationNotes,
            github_config: {
              repository_name: repositoryName,
              branch_name: "main",
            },
            github_actions_agent:
              GenerateVerificationCodeRequestBody.github_actions_agent.CLAUDE_CODE,
            verification_id: verification.id,
          });

        onUpdateVerification(verification.id, {
          workflowRunId: data.workflow_run_id ?? null,
          githubUrl: data.github_url ?? null,
        });

        if (data.dispatched && data.workflow_run_id) {
          startPolling(data.workflow_run_id, repositoryName, verification.id);
        } else if (!data.dispatched) {
          setErrorMessage("Failed to dispatch workflow.");
          onUpdateVerification(verification.id, { phase: "plan-generated" });
        } else {
          onUpdateVerification(verification.id, { phase: "code-generated" });
        }
      } catch (err) {
        setErrorMessage(err instanceof Error ? err.message : "An unexpected error occurred.");
        onUpdateVerification(verification.id, { phase: "plan-generated" });
      }
    },
    [verification, onUpdateVerification, startPolling],
  );

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
            ? {
                ...exp,
                status: "completed" as const,
                result: mockExperimentResultResponse,
              }
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
      setIsPaperGenerating(true);
      setTimeout(() => {
        const draft: PaperDraft = {
          title: `${verification.title}: A Comparative Study`,
          selectedExperimentIds,
          paperUrl:
            "https://github.com/airas-org/exp-data-augmentation/.research/generated_paper.pdf",
          overleafUrl: "https://www.overleaf.com/project/mock-project-id-67890",
          status: "ready",
        };
        onUpdateVerification(verification.id, {
          phase: "paper-writing",
          paperDraft: draft,
        });
        setIsPaperGenerating(false);
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
    if (hasProposedMethods)
      entries.push({
        id: "sec-methods",
        label: t("verification.detail.tocLabels.methods"),
      });
    if (verification.verificationMethod)
      entries.push({
        id: "sec-plan",
        label: t("verification.detail.tocLabels.plan"),
      });
    if (verification.implementation) {
      entries.push({
        id: "sec-code",
        label: t("verification.detail.tocLabels.code"),
      });
      entries.push({
        id: "sec-settings",
        label: t("verification.detail.tocLabels.settings"),
      });
    }
    if (anyCompleted) {
      entries.push(
        {
          id: "sec-dashboard",
          label: t("verification.detail.tocLabels.results"),
        },
        {
          id: "sec-paper",
          label: t("verification.detail.tocLabels.paperWriting"),
        },
      );
    }
    if (verification.paperDraft) {
      entries.push({
        id: "sec-generated-paper",
        label: t("verification.detail.tocLabels.paper"),
      });
    }
    return entries;
  }, [verification, t]);

  if (!verification) return null;

  const hasQuery = verification.phase !== "initial";
  const isGenerating = verification.phase === "code-generating";
  const showMethods = verification.proposedMethods && verification.proposedMethods.length > 0;
  const hasAnyCompleted = verification.implementation?.experimentSettings.some(
    (exp) => exp.status === "completed",
  );

  return (
    <div className="flex-1 flex flex-col overflow-y-auto">
      <div className="flex-shrink-0 px-4 pt-3">
        <button
          type="button"
          onClick={() => navigate("/verification")}
          className="rounded-md px-2 py-1 text-xs text-subtext-color hover:bg-neutral-50 active:bg-neutral-100 transition-colors cursor-pointer"
        >
          {t("verification.home.title")}
        </button>
      </div>
      {!hasQuery && (
        <div className="flex-1 flex items-center justify-center pb-[20vh] p-6">
          <ChatInput onSubmit={handleChatSubmit} />
        </div>
      )}

      {hasQuery && (
        <div className="flex-1">
          {tocEntries.length > 0 && <TocNav entries={tocEntries} />}
          <div className="flex-1 p-6 xl:pr-44 space-y-6 w-full">
            {errorMessage && (
              <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3">
                <p className="text-sm text-red-700">{errorMessage}</p>
              </div>
            )}

            <UserInputCard
              query={verification.query}
              title={verification.title}
              onTitleChange={(title) => onUpdateVerification(verification.id, { title })}
            />

            {verification.phase === "proposing-policies" && (
              <div className="flex items-center gap-2 px-3 py-4">
                <Loader size="small" />
                <span className="text-xs text-muted-foreground">
                  {t("verification.detail.proposingPolicies")}
                </span>
              </div>
            )}

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

            {verification.selectedMethodId && !verification.verificationMethod && (
              <div className="flex items-center gap-2 px-3 py-4">
                <Loader size="small" />
                <span className="text-xs text-muted-foreground">
                  {t("verification.detail.generatingPlan")}
                </span>
              </div>
            )}

            {verification.verificationMethod && (
              <div id="sec-plan">
                <VerificationPlanView
                  verificationMethod={verification.verificationMethod}
                  onGenerateCode={handleGenerateCode}
                  showButton={!isGenerating && !verification.implementation}
                />
              </div>
            )}

            {isGenerating && (
              <div className="flex flex-col gap-2 px-3 py-4">
                <div className="flex items-center gap-2">
                  <Loader size="small" />
                  <span className="text-xs text-muted-foreground">
                    {t("verification.detail.generatingCode")}
                  </span>
                </div>
                {verification.githubUrl && (
                  <a
                    href={verification.githubUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-brand-600 hover:underline ml-7"
                  >
                    {verification.githubUrl}
                  </a>
                )}
                {verification.codeGenerationStatus && (
                  <p className="text-xs text-muted-foreground ml-7">
                    Status: {verification.codeGenerationStatus}
                    {verification.codeGenerationConclusion
                      ? ` (${verification.codeGenerationConclusion})`
                      : ""}
                  </p>
                )}
              </div>
            )}

            {verification.phase === "code-generated" &&
              verification.githubUrl &&
              !verification.implementation && (
                <div className="rounded-md border border-border bg-card p-4 space-y-1">
                  <p className="text-sm font-medium text-foreground">
                    {t("verification.detail.codeGenerated")}
                  </p>
                  <a
                    href={verification.githubUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-brand-600 hover:underline"
                  >
                    {verification.githubUrl}
                  </a>
                  {verification.codeGenerationStatus && (
                    <p className="text-xs text-muted-foreground">
                      Status: {verification.codeGenerationStatus}
                      {verification.codeGenerationConclusion
                        ? ` (${verification.codeGenerationConclusion})`
                        : ""}
                    </p>
                  )}
                </div>
              )}

            {verification.implementation && (
              <ImplementationResult
                implementation={verification.implementation}
                onRunExperiment={handleRunExperiment}
              />
            )}

            {hasAnyCompleted && verification.implementation && (
              <>
                <div id="sec-dashboard">
                  <ExperimentDashboard
                    experiments={verification.implementation.experimentSettings}
                  />
                </div>
                <div id="sec-paper" className="space-y-6">
                  <PaperWritingSection
                    experiments={verification.implementation.experimentSettings}
                    paperDraft={verification.paperDraft}
                    isGenerating={isPaperGenerating}
                    onGeneratePaper={handleGeneratePaper}
                  />
                </div>
              </>
            )}

            {isPaperGenerating && !verification.paperDraft && (
              <div className="flex items-center gap-2 px-3 py-4">
                <Loader size="small" />
                <span className="text-xs text-muted-foreground">
                  {t("verification.detail.paperWriting.generatingPaper")}
                </span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
