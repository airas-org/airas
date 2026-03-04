export type VerificationPhase =
  | "initial"
  | "methods-proposed"
  | "plan-generated"
  | "code-generating"
  | "code-generated"
  | "experiments-done"
  | "paper-writing";

export interface ProposedMethod {
  id: string;
  title: string;
  whatToVerify: string;
  method: string;
  pros: string[];
  cons: string[];
}

export interface PaperDraft {
  title: string;
  selectedExperimentIds: string[];
  overleafUrl: string;
  status: "generating" | "ready";
}

export interface Verification {
  id: string;
  title: string;
  query: string;
  createdAt: Date;
  phase: VerificationPhase;
  plan?: VerificationPlan;
  implementation?: ImplementationInfo;
  proposedMethods?: ProposedMethod[];
  selectedMethodId?: string;
  paperDraft?: PaperDraft;
}

export interface VerificationPlan {
  whatToVerify: string;
  method: string;
}

export interface ImplementationInfo {
  githubUrl: string;
  fixedParameters: { name: string; value: string }[];
  experimentSettings: ExperimentSetting[];
}

export interface ExperimentSetting {
  id: string;
  title: string;
  description: string;
  parameters: { name: string; value: string }[];
  status: "pending" | "running" | "completed";
  result?: ExperimentResult;
}

export interface ExperimentResult {
  summary: string;
  metrics: Record<string, number>;
  details: string;
}
