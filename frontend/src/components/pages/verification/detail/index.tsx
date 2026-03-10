import { FeatherArrowLeft } from "@subframe/core";
import type React from "react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { OpenAPI } from "@/lib/api/core/OpenAPI";
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

async function getAuthHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {};
  if (OpenAPI.TOKEN) {
    const token =
      typeof OpenAPI.TOKEN === "function" ? await OpenAPI.TOKEN({} as never) : OpenAPI.TOKEN;
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }
  if (OpenAPI.HEADERS) {
    const extraHeaders =
      typeof OpenAPI.HEADERS === "function" ? await OpenAPI.HEADERS({} as never) : OpenAPI.HEADERS;
    Object.assign(headers, extraHeaders);
  }
  return headers;
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
  const pollingIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current !== null) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
  }, []);

  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  const startPolling = useCallback(
    (
      workflowRunId: number,
      githubOwner: string,
      repositoryName: string,
      verificationId: string,
    ) => {
      stopPolling();
      const apiBase = OpenAPI.BASE;

      pollingIntervalRef.current = setInterval(async () => {
        try {
          const authHeaders = await getAuthHeaders();
          const res = await fetch(
            `${apiBase}/airas/v1/verification/experiment-code-status/${githubOwner}/${repositoryName}/${workflowRunId}`,
            { headers: authHeaders },
          );
          if (!res.ok) return;
          const data = await res.json();
          onUpdateVerification(verificationId, {
            codeGenerationStatus: data.status,
            codeGenerationConclusion: data.conclusion ?? null,
          });
          if (data.status === "completed" || data.conclusion != null) {
            stopPolling();
            onUpdateVerification(verificationId, { phase: "code-generated" });
          }
        } catch {
          // ignore transient errors during polling
        }
      }, 10000);
    },
    [onUpdateVerification, stopPolling],
  );

  const handleChatSubmit = useCallback(
    async (query: string) => {
      if (!verification) return;
      setErrorMessage(null);
      onUpdateVerification(verification.id, {
        query,
        phase: "proposing-policies",
      });

      try {
        const apiBase = OpenAPI.BASE;
        const authHeaders = await getAuthHeaders();
        const res = await fetch(`${apiBase}/airas/v1/verification/propose-policies`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...authHeaders,
          },
          body: JSON.stringify({ user_query: query, verification_id: verification.id }),
        });

        if (!res.ok) {
          setErrorMessage(`Failed to propose policies: ${res.statusText}`);
          return;
        }

        const data = await res.json();

        if (!data.feasible) {
          setErrorMessage(data.infeasible_reason ?? "This query is not feasible for verification.");
          return;
        }

        const methods: ProposedMethod[] = data.proposed_methods.map(
          (m: {
            id: string;
            title: string;
            what_to_verify: string;
            method: string;
            pros?: string[];
            cons?: string[];
          }) => ({
            id: m.id,
            title: m.title,
            whatToVerify: m.what_to_verify,
            method: m.method,
            pros: m.pros ?? [],
            cons: m.cons ?? [],
          }),
        );

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
        const apiBase = OpenAPI.BASE;
        const authHeaders = await getAuthHeaders();
        const res = await fetch(`${apiBase}/airas/v1/verification/generate-method`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...authHeaders,
          },
          body: JSON.stringify({
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
          }),
        });

        if (!res.ok) {
          setErrorMessage(`Failed to generate method: ${res.statusText}`);
          return;
        }

        const data = await res.json();
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
        const apiBase = OpenAPI.BASE;
        const authHeaders = await getAuthHeaders();
        const githubOwner = "airas-org";

        const res = await fetch(`${apiBase}/airas/v1/verification/generate-experiment-code`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...authHeaders,
          },
          body: JSON.stringify({
            user_query: verification.query,
            what_to_verify: updatedMethod.whatToVerify,
            experiment_settings: updatedMethod.experimentSettings,
            steps: updatedMethod.steps,
            modification_notes: modificationNotes,
            repository_name: repositoryName,
            github_owner: githubOwner,
            branch_name: "main",
            github_actions_agent: "claude_code",
            verification_id: verification.id,
          }),
        });

        if (!res.ok) {
          setErrorMessage(`Failed to generate experiment code: ${res.statusText}`);
          onUpdateVerification(verification.id, { phase: "plan-generated" });
          return;
        }

        const data = await res.json();

        onUpdateVerification(verification.id, {
          workflowRunId: data.workflow_run_id ?? null,
          githubUrl: data.github_url ?? null,
        });

        if (data.workflow_run_id) {
          startPolling(data.workflow_run_id, githubOwner, repositoryName, verification.id);
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
      entries.push({
        id: "sec-dashboard",
        label: t("verification.detail.tocLabels.results"),
      });
    }
    if (anyCompleted) {
      entries.push({
        id: "sec-paper",
        label: t("verification.detail.tocLabels.paperWriting"),
      });
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
          className="flex items-center gap-1.5 text-xs text-subtext-color hover:text-default-font transition-colors cursor-pointer"
        >
          <FeatherArrowLeft className="h-3.5 w-3.5" />
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
                  Generating verification plan...
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
                    Generating experiment code...
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
                  <p className="text-sm font-medium text-foreground">Experiment code generated</p>
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
              <div id="sec-dashboard">
                <ExperimentDashboard experiments={verification.implementation.experimentSettings} />
              </div>
            )}

            {hasAnyCompleted && verification.implementation && (
              <div id="sec-paper" className="space-y-6">
                <PaperWritingSection
                  experiments={verification.implementation.experimentSettings}
                  paperDraft={verification.paperDraft}
                  isGenerating={isPaperGenerating}
                  onGeneratePaper={handleGeneratePaper}
                />
              </div>
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
