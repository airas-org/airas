import { useCallback, useEffect, useState } from "react";
import { OpenAPI } from "@/lib/api/core/OpenAPI";
import type { ExperimentResult, ProposedMethod, Verification, VerificationPhase } from "./types";

// ---------- Server response types ----------

interface VerificationSessionResponse {
  id: string;
  title: string;
  query: string;
  created_by: string;
  created_at: string;
  updated_at: string;
  phase: string;
  proposed_methods: Array<{
    id: string;
    title: string;
    what_to_verify: string;
    method: string;
    pros: string[];
    cons: string[];
  }> | null;
  selected_method_id: string | null;
  verification_method: {
    what_to_verify: string;
    experiment_settings: Record<string, string>;
    steps: string[];
  } | null;
  plan: { what_to_verify: string; method: string } | null;
  repository_name: string | null;
  github_owner: string | null;
  github_url: string | null;
  workflow_run_id: number | null;
  modification_notes: string | null;
  code_generation_status: string | null;
  code_generation_conclusion: string | null;
  implementation: {
    github_url: string;
    fixed_parameters: { name: string; description: string }[];
    experiment_settings: {
      id: string;
      title: string;
      description: string;
      parameters: { name: string; value: string }[];
      status: string;
      result?: unknown;
    }[];
  } | null;
  paper_draft: {
    title: string;
    selected_experiment_ids: string[];
    paper_url: string;
    overleaf_url: string;
    status: string;
  } | null;
}

// ---------- Auth helpers ----------

export async function getAuthHeaders(): Promise<Record<string, string>> {
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

// ---------- Conversion ----------

function sessionToVerification(session: VerificationSessionResponse): Verification {
  return {
    id: session.id,
    title: session.title,
    query: session.query,
    createdAt: new Date(session.created_at),
    phase: session.phase as VerificationPhase,
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
          githubUrl: session.implementation.github_url,
          fixedParameters: session.implementation.fixed_parameters,
          experimentSettings: session.implementation.experiment_settings.map((es) => ({
            id: es.id,
            title: es.title,
            description: es.description,
            parameters: es.parameters,
            status: es.status as "pending" | "running" | "completed",
            result: es.result as ExperimentResult | undefined,
          })),
        }
      : undefined,
    paperDraft: session.paper_draft
      ? {
          title: session.paper_draft.title,
          selectedExperimentIds: session.paper_draft.selected_experiment_ids,
          paperUrl: session.paper_draft.paper_url,
          overleafUrl: session.paper_draft.overleaf_url,
          status: session.paper_draft.status as "generating" | "ready",
        }
      : undefined,
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

export function useVerifications(navigate: (path: string) => void) {
  const [verifications, setVerifications] = useState<Verification[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  // Fetch sessions on mount
  useEffect(() => {
    const fetchSessions = async () => {
      try {
        const apiBase = OpenAPI.BASE;
        const authHeaders = await getAuthHeaders();
        const res = await fetch(`${apiBase}/airas/v1/verification/sessions`, {
          headers: authHeaders,
        });
        if (!res.ok) return;
        const data = await res.json();
        const sessions: VerificationSessionResponse[] = data.sessions ?? [];
        setVerifications(sessions.map(sessionToVerification));
      } catch {
        // ignore fetch errors on mount
      } finally {
        setIsLoading(false);
      }
    };

    fetchSessions();
  }, []);

  const handleCreateVerification = useCallback(async () => {
    try {
      const apiBase = OpenAPI.BASE;
      const authHeaders = await getAuthHeaders();
      const res = await fetch(`${apiBase}/airas/v1/verification/sessions`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...authHeaders,
        },
        body: JSON.stringify({}),
      });
      if (!res.ok) return;
      const session: VerificationSessionResponse = await res.json();
      const newVerification = sessionToVerification(session);
      setVerifications((prev) => [newVerification, ...prev]);
      navigate(`/verification/${newVerification.id}`);
    } catch {
      // ignore
    }
  }, [navigate]);

  const handleUpdateVerification = useCallback(
    async (id: string, updates: Partial<Verification>) => {
      // Optimistic local update
      setVerifications((prev) => prev.map((v) => (v.id === id ? { ...v, ...updates } : v)));

      const body = buildPatchBody(updates);
      if (Object.keys(body).length === 0) return;

      try {
        const apiBase = OpenAPI.BASE;
        const authHeaders = await getAuthHeaders();
        await fetch(`${apiBase}/airas/v1/verification/sessions/${id}`, {
          method: "PATCH",
          headers: {
            "Content-Type": "application/json",
            ...authHeaders,
          },
          body: JSON.stringify(body),
        });
      } catch {
        // No rollback — keep optimistic state
      }
    },
    [],
  );

  const handleDeleteVerification = useCallback(
    async (id: string) => {
      setVerifications((prev) => prev.filter((v) => v.id !== id));

      if (window.location.pathname === `/verification/${id}`) {
        navigate("/home");
      }

      try {
        const apiBase = OpenAPI.BASE;
        const authHeaders = await getAuthHeaders();
        await fetch(`${apiBase}/airas/v1/verification/sessions/${id}`, {
          method: "DELETE",
          headers: authHeaders,
        });
      } catch {
        // ignore
      }
    },
    [navigate],
  );

  const handleDuplicateVerification = useCallback(
    async (id: string) => {
      const source = verifications.find((v) => v.id === id);
      if (!source) return;

      try {
        const apiBase = OpenAPI.BASE;
        const authHeaders = await getAuthHeaders();

        // Create a new session
        const createRes = await fetch(`${apiBase}/airas/v1/verification/sessions`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            ...authHeaders,
          },
          body: JSON.stringify({ title: `${source.title} (copy)` }),
        });
        if (!createRes.ok) return;
        const newSession: VerificationSessionResponse = await createRes.json();

        // Copy relevant fields to the new session
        const copyUpdates: Partial<Verification> = {
          title: `${source.title} (copy)`,
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
          await fetch(`${apiBase}/airas/v1/verification/sessions/${newSession.id}`, {
            method: "PATCH",
            headers: {
              "Content-Type": "application/json",
              ...authHeaders,
            },
            body: JSON.stringify(patchBody),
          });
        }

        const copy: Verification = {
          ...source,
          id: newSession.id,
          title: `${source.title} (copy)`,
          createdAt: new Date(newSession.created_at),
        };
        setVerifications((prev) => [copy, ...prev]);
      } catch {
        // ignore
      }
    },
    [verifications],
  );

  return {
    verifications,
    isLoading,
    handleCreateVerification,
    handleUpdateVerification,
    handleDeleteVerification,
    handleDuplicateVerification,
  };
}
