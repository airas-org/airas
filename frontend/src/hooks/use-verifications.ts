import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import type {
  ExperimentResult,
  ExperimentSetting,
  PaperDraft,
  ProposedMethod,
  Verification,
  VerificationPhase,
} from "@/components/pages/verification/types";
import type { VerificationSessionResponse } from "@/lib/api/models/VerificationSessionResponse";
import { VerificationService } from "@/lib/api/services/VerificationService";

// ---------- Guards ----------

const VERIFICATION_PHASES: readonly string[] = [
  "initial",
  "proposing-policies",
  "methods-proposed",
  "plan-generated",
  "code-generating",
  "code-generated",
  "experiments-done",
  "paper-writing",
] satisfies readonly VerificationPhase[];

function isVerificationPhase(v: unknown): v is VerificationPhase {
  return typeof v === "string" && VERIFICATION_PHASES.includes(v);
}

// ---------- Conversion ----------

function parseExperimentSetting(es: Record<string, unknown>): ExperimentSetting {
  return {
    id: String(es.id ?? ""),
    title: String(es.title ?? ""),
    description: String(es.description ?? ""),
    parameters: Array.isArray(es.parameters)
      ? (es.parameters as { name: string; value: string }[])
      : [],
    status:
      es.status === "running" ? "running" : es.status === "completed" ? "completed" : "pending",
    result: (es.result as ExperimentResult) ?? undefined,
  };
}

function parsePaperDraft(raw: Record<string, unknown>): PaperDraft {
  return {
    title: String(raw.title ?? ""),
    selectedExperimentIds: Array.isArray(raw.selected_experiment_ids)
      ? (raw.selected_experiment_ids as string[])
      : [],
    paperUrl: String(raw.paper_url ?? ""),
    overleafUrl: String(raw.overleaf_url ?? ""),
    status: raw.status === "generating" ? "generating" : "ready",
  };
}

function sessionToVerification(session: VerificationSessionResponse): Verification {
  return {
    id: session.id,
    title: session.title,
    query: session.query,
    createdAt: new Date(session.created_at),
    phase: isVerificationPhase(session.phase) ? session.phase : "initial",
    proposedMethods:
      session.proposed_methods?.map(
        (m): ProposedMethod => ({
          id: m.id,
          title: m.title,
          whatToVerify: m.what_to_verify,
          method: m.method,
          pros: m.pros ?? [],
          cons: m.cons ?? [],
        }),
      ) ?? undefined,
    selectedMethodId: session.selected_method_id ?? undefined,
    verificationMethod: session.verification_method
      ? {
          whatToVerify: session.verification_method.what_to_verify,
          experimentSettings: session.verification_method.experiment_settings,
          steps: session.verification_method.steps,
        }
      : undefined,
    plan: session.plan
      ? {
          whatToVerify: session.plan.what_to_verify,
          method: session.plan.method,
        }
      : undefined,
    repositoryName: session.repository_name ?? undefined,
    githubUrl: session.github_url ?? undefined,
    workflowRunId: session.workflow_run_id ?? undefined,
    modificationNotes: session.modification_notes ?? undefined,
    codeGenerationStatus: session.code_generation_status ?? undefined,
    codeGenerationConclusion: session.code_generation_conclusion ?? undefined,
    implementation: session.implementation
      ? {
          githubUrl: String(session.implementation.github_url ?? ""),
          fixedParameters: Array.isArray(session.implementation.fixed_parameters)
            ? (session.implementation.fixed_parameters as { name: string; description: string }[])
            : [],
          experimentSettings: Array.isArray(session.implementation.experiment_settings)
            ? session.implementation.experiment_settings.map(parseExperimentSetting)
            : [],
        }
      : undefined,
    paperDraft: session.paper_draft ? parsePaperDraft(session.paper_draft) : undefined,
  };
}

// ---------- Frontend → API field mapping ----------

type PatchBody = Record<string, unknown>;

function buildPatchBody(updates: Partial<Verification>): PatchBody {
  const body: PatchBody = {};

  if (updates.title !== undefined) body.title = updates.title;
  if (updates.query !== undefined) body.query = updates.query;
  if (updates.phase !== undefined) body.phase = updates.phase;
  if (updates.proposedMethods !== undefined) {
    body.proposed_methods = updates.proposedMethods.map((m) => ({
      id: m.id,
      title: m.title,
      what_to_verify: m.whatToVerify,
      method: m.method,
      pros: m.pros,
      cons: m.cons,
    }));
  }
  if (updates.selectedMethodId !== undefined)
    body.selected_method_id = updates.selectedMethodId ?? null;
  if (updates.verificationMethod !== undefined) {
    body.verification_method = updates.verificationMethod
      ? {
          what_to_verify: updates.verificationMethod.whatToVerify,
          experiment_settings: updates.verificationMethod.experimentSettings,
          steps: updates.verificationMethod.steps,
        }
      : null;
  }
  if (updates.modificationNotes !== undefined)
    body.modification_notes = updates.modificationNotes ?? null;
  if (updates.repositoryName !== undefined) body.repository_name = updates.repositoryName ?? null;
  if (updates.githubUrl !== undefined) body.github_url = updates.githubUrl ?? null;
  if (updates.workflowRunId !== undefined) body.workflow_run_id = updates.workflowRunId ?? null;
  if (updates.codeGenerationStatus !== undefined)
    body.code_generation_status = updates.codeGenerationStatus ?? null;
  if (updates.codeGenerationConclusion !== undefined)
    body.code_generation_conclusion = updates.codeGenerationConclusion ?? null;

  return body;
}

// ---------- Hook ----------

export function useVerifications() {
  const navigate = useNavigate();
  const [verifications, setVerifications] = useState<Verification[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const data = await VerificationService.listSessionsAirasV1VerificationSessionsGet();
        const sessions = data.sessions ?? [];
        setVerifications(sessions.map(sessionToVerification));
      } catch (error) {
        console.error("Failed to fetch verification sessions", error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchSessions();
  }, []);

  async function handleCreateVerification() {
    try {
      const session = await VerificationService.createSessionAirasV1VerificationSessionsPost({});
      const newVerification = sessionToVerification(session);
      setVerifications((prev) => [newVerification, ...prev]);
      navigate(`/verification/${newVerification.id}`);
    } catch (error) {
      console.error("Failed to create verification session", error);
    }
  }

  async function handleUpdateVerification(id: string, updates: Partial<Verification>) {
    setVerifications((prev) => prev.map((v) => (v.id === id ? { ...v, ...updates } : v)));

    const body = buildPatchBody(updates);
    if (Object.keys(body).length === 0) return;

    try {
      await VerificationService.updateSessionAirasV1VerificationSessionsVerificationIdPatch(
        id,
        body as Parameters<
          typeof VerificationService.updateSessionAirasV1VerificationSessionsVerificationIdPatch
        >[1],
      );
    } catch (error) {
      // No rollback — keep optimistic state
      console.error("Failed to update verification session", error);
    }
  }

  async function handleDeleteVerification(id: string) {
    setVerifications((prev) => prev.filter((v) => v.id !== id));

    if (window.location.pathname === `/verification/${id}`) {
      navigate("/home");
    }

    try {
      await VerificationService.deleteSessionAirasV1VerificationSessionsVerificationIdDelete(id);
    } catch (error) {
      console.error("Failed to delete verification session", error);
    }
  }

  function handleAddVerification(session: VerificationSessionResponse) {
    setVerifications((prev) => [sessionToVerification(session), ...prev]);
  }

  async function handleDuplicateVerification(id: string) {
    const source = verifications.find((v) => v.id === id);
    if (!source) return;

    const copyLabel = navigator.language.startsWith("ja") ? "(コピー)" : "(copy)";
    const copyTitle = `${source.title} ${copyLabel}`;

    try {
      const newSession = await VerificationService.createSessionAirasV1VerificationSessionsPost({
        title: copyTitle,
      });

      const copyUpdates: Partial<Verification> = {
        title: copyTitle,
        query: source.query,
        phase: source.phase,
        proposedMethods: source.proposedMethods,
        selectedMethodId: source.selectedMethodId,
        verificationMethod: source.verificationMethod,
        plan: source.plan,
        repositoryName: source.repositoryName,
        githubUrl: source.githubUrl,
        workflowRunId: source.workflowRunId,
        modificationNotes: source.modificationNotes,
        codeGenerationStatus: source.codeGenerationStatus,
        codeGenerationConclusion: source.codeGenerationConclusion,
      };

      const patchBody = buildPatchBody(copyUpdates);
      if (Object.keys(patchBody).length > 0) {
        await VerificationService.updateSessionAirasV1VerificationSessionsVerificationIdPatch(
          newSession.id,
          patchBody as Parameters<
            typeof VerificationService.updateSessionAirasV1VerificationSessionsVerificationIdPatch
          >[1],
        );
      }

      const copy: Verification = {
        ...source,
        id: newSession.id,
        title: copyTitle,
        createdAt: new Date(newSession.created_at),
      };
      setVerifications((prev) => [copy, ...prev]);
    } catch (error) {
      console.error("Failed to duplicate verification session", error);
    }
  }

  async function handleCreateWithMethod(sourceVerification: Verification, method: ProposedMethod) {
    let newId: string | null = null;
    try {
      const session = await VerificationService.createSessionAirasV1VerificationSessionsPost({
        title: method.title,
      });
      newId = session.id;

      handleAddVerification(session);
      handleUpdateVerification(newId, {
        title: method.title,
        query: sourceVerification.query,
        proposedMethods: [method],
        selectedMethodId: method.id,
        phase: "methods-proposed",
      });

      navigate(`/verification/${newId}`);

      const data = await VerificationService.generateMethodAirasV1VerificationGenerateMethodPost({
        user_query: sourceVerification.query,
        selected_policy: {
          id: method.id,
          title: method.title,
          what_to_verify: method.whatToVerify,
          method: method.method,
          pros: method.pros,
          cons: method.cons,
        },
        verification_id: newId,
      });

      handleUpdateVerification(newId, {
        phase: "plan-generated",
        verificationMethod: {
          whatToVerify: data.what_to_verify,
          experimentSettings: data.experiment_settings,
          steps: data.steps,
        },
      });
    } catch (error) {
      console.error("handleCreateWithMethod failed", error);
      if (newId !== null) {
        handleUpdateVerification(newId, {
          selectedMethodId: undefined,
          phase: "methods-proposed",
        });
      }
    }
  }

  async function handleCreateWithQuery(query: string) {
    let newId: string | null = null;
    try {
      const session = await VerificationService.createSessionAirasV1VerificationSessionsPost({});
      newId = session.id;

      handleAddVerification(session);
      handleUpdateVerification(newId, { query, phase: "proposing-policies" });
      navigate(`/verification/${newId}`);

      const data = await VerificationService.proposePoliciesAirasV1VerificationProposePoliciesPost({
        user_query: query,
        verification_id: newId,
      });

      if (!data.feasible) {
        handleUpdateVerification(newId, { phase: "initial" });
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
      handleUpdateVerification(newId, {
        phase: "methods-proposed",
        proposedMethods: methods,
      });
    } catch (error) {
      console.error("handleCreateWithQuery failed", error);
      if (newId !== null) {
        handleUpdateVerification(newId, { phase: "initial" });
      }
    }
  }

  return {
    verifications,
    isLoading,
    handleCreateVerification,
    handleUpdateVerification,
    handleDeleteVerification,
    handleDuplicateVerification,
    handleAddVerification,
    handleCreateWithMethod,
    handleCreateWithQuery,
  };
}
