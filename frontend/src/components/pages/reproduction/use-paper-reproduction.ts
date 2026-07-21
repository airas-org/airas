import { useCallback, useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  type DispatchPaperReproductionGenerateRequestBody,
  type FetchPaperReproductionResultsResponseBody,
  type FetchParameterTuningResultsResponseBody,
  type GitHubConfig,
  type GitHubConfigRequest,
  GithubActionsService,
  type NodeLLMConfig,
  PaperReproductionService,
} from "@/lib/api";

const DEFAULT_GENERATE_LLM_CONFIG: NodeLLMConfig = {
  llm_name: "anthropic/claude-sonnet-4-5",
  params: { provider_type: "anthropic" },
};
const DEFAULT_JUDGE_LLM_CONFIG: NodeLLMConfig = {
  llm_name: "gpt-5.2",
  params: { provider_type: "openai", reasoning_effort: null },
};

// The backend requires an explicit model per node (no in-code default), so a "use default"
// selection in the UI is resolved to a concrete model here before the request is sent.
function resolveNodeLLMConfig(
  config: NodeLLMConfig | null,
  defaultConfig: NodeLLMConfig,
): NodeLLMConfig {
  return config ?? defaultConfig;
}

// Request bodies resolve the owner server-side; polling still needs the full config.
function toGitHubConfigRequest(githubConfig: GitHubConfig): GitHubConfigRequest {
  return {
    repository_name: githubConfig.repository_name,
    branch_name: githubConfig.branch_name,
  };
}

export type WorkflowStepStatus = "idle" | "dispatching" | "running" | "succeeded" | "failed";

export interface GenerateParams {
  paperUrl: string;
  instruction: string;
  repoUrl: string;
  githubActionsAgent: DispatchPaperReproductionGenerateRequestBody.github_actions_agent;
  llmConfig: NodeLLMConfig | null;
}

export function usePaperReproduction() {
  const { t } = useTranslation();

  const [generateStatus, setGenerateStatus] = useState<WorkflowStepStatus>("idle");
  const [runStatus, setRunStatus] = useState<WorkflowStepStatus>("idle");
  const [tuningStatus, setTuningStatus] = useState<WorkflowStepStatus>("idle");
  const [reproductionResults, setReproductionResults] =
    useState<FetchPaperReproductionResultsResponseBody | null>(null);
  const [tuningResults, setTuningResults] =
    useState<FetchParameterTuningResultsResponseBody | null>(null);
  const [isFetchingResults, setIsFetchingResults] = useState(false);
  const [isFetchingTuningResults, setIsFetchingTuningResults] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [reproId, setReproId] = useState<string | null>(null);

  const mountedRef = useRef(true);
  useEffect(() => {
    mountedRef.current = true;
    return () => {
      mountedRef.current = false;
    };
  }, []);

  const runWorkflowStep = useCallback(
    async (
      dispatch: () => Promise<{ dispatched: boolean }>,
      githubConfig: GitHubConfig,
      setStatus: (status: WorkflowStepStatus) => void,
    ): Promise<boolean> => {
      setError(null);
      setStatus("dispatching");
      try {
        const { dispatched } = await dispatch();
        if (!dispatched) {
          throw new Error(t("reproduction.errors.dispatchFailed"));
        }
        if (!mountedRef.current) return false;
        setStatus("running");
        // Blocks server-side until the dispatched workflow chain completes.
        const poll = await GithubActionsService.pollGithubActionsAirasV1GithubActionsPollingPost({
          github_config: githubConfig,
        });
        if (!mountedRef.current) return false;
        const succeeded = poll.status === "completed" && poll.conclusion === "success";
        setStatus(succeeded ? "succeeded" : "failed");
        if (!succeeded) {
          setError(
            t("reproduction.errors.workflowFailed", {
              conclusion: poll.conclusion ?? poll.status ?? "unknown",
            }),
          );
        }
        return succeeded;
      } catch (err) {
        if (!mountedRef.current) return false;
        setStatus("failed");
        setError(err instanceof Error ? err.message : t("reproduction.errors.dispatchFailed"));
        return false;
      }
    },
    [t],
  );

  const fetchResults = useCallback(
    async (githubConfig: GitHubConfig, llmConfig: NodeLLMConfig | null) => {
      if (reproId === null) {
        setError(t("reproduction.errors.missingReproId"));
        return;
      }
      setError(null);
      setIsFetchingResults(true);
      try {
        const results =
          await PaperReproductionService.fetchPaperReproductionResultsAirasV1PaperReproductionResultsPost(
            {
              github_config: toGitHubConfigRequest(githubConfig),
              repro_id: reproId,
              llm_mapping: {
                judge_reproduction: resolveNodeLLMConfig(llmConfig, DEFAULT_JUDGE_LLM_CONFIG),
              },
            },
          );
        if (!mountedRef.current) return;
        setReproductionResults(results);
      } catch (err) {
        if (!mountedRef.current) return;
        setError(err instanceof Error ? err.message : t("reproduction.errors.resultsFailed"));
      } finally {
        if (mountedRef.current) setIsFetchingResults(false);
      }
    },
    [t, reproId],
  );

  const fetchTuningResults = useCallback(
    async (githubConfig: GitHubConfig) => {
      if (reproId === null) {
        setError(t("reproduction.errors.missingReproId"));
        return;
      }
      setError(null);
      setIsFetchingTuningResults(true);
      try {
        const results =
          await PaperReproductionService.fetchParameterTuningResultsAirasV1PaperReproductionParameterTuningResultsPost(
            { github_config: toGitHubConfigRequest(githubConfig), repro_id: reproId },
          );
        if (!mountedRef.current) return;
        setTuningResults(results);
      } catch (err) {
        if (!mountedRef.current) return;
        setError(err instanceof Error ? err.message : t("reproduction.errors.resultsFailed"));
      } finally {
        if (mountedRef.current) setIsFetchingTuningResults(false);
      }
    },
    [t, reproId],
  );

  const startGenerate = useCallback(
    async (githubConfig: GitHubConfig, params: GenerateParams) => {
      setRunStatus("idle");
      setTuningStatus("idle");
      setReproductionResults(null);
      setTuningResults(null);
      setReproId(null);
      await runWorkflowStep(
        async () => {
          const res =
            await PaperReproductionService.dispatchPaperReproductionGenerateAirasV1PaperReproductionGenerateDispatchPost(
              {
                github_config: toGitHubConfigRequest(githubConfig),
                paper_url: params.paperUrl,
                instruction: params.instruction,
                repo_url: params.repoUrl,
                github_actions_agent: params.githubActionsAgent,
                llm_mapping: {
                  dispatch_paper_reproduction_generate: resolveNodeLLMConfig(
                    params.llmConfig,
                    DEFAULT_GENERATE_LLM_CONFIG,
                  ),
                },
              },
            );
          if (res.dispatched && mountedRef.current) {
            setReproId(res.repro_id);
          }
          return res;
        },
        githubConfig,
        setGenerateStatus,
      );
    },
    [runWorkflowStep],
  );

  const startRun = useCallback(
    async (githubConfig: GitHubConfig, repoUrl: string, llmConfig: NodeLLMConfig | null) => {
      if (reproId === null) {
        setError(t("reproduction.errors.missingReproId"));
        return;
      }
      setTuningStatus("idle");
      setReproductionResults(null);
      setTuningResults(null);
      const succeeded = await runWorkflowStep(
        () =>
          PaperReproductionService.dispatchPaperReproductionRunAirasV1PaperReproductionRunDispatchPost(
            {
              github_config: toGitHubConfigRequest(githubConfig),
              repro_id: reproId,
              repo_url: repoUrl,
            },
          ),
        githubConfig,
        setRunStatus,
      );
      if (succeeded) {
        await fetchResults(githubConfig, llmConfig);
      }
    },
    [runWorkflowStep, fetchResults, t, reproId],
  );

  const startTuning = useCallback(
    async (githubConfig: GitHubConfig, repoUrl: string) => {
      if (reproId === null) {
        setError(t("reproduction.errors.missingReproId"));
        return;
      }
      setTuningResults(null);
      const succeeded = await runWorkflowStep(
        () =>
          PaperReproductionService.dispatchParameterTuningRunAirasV1PaperReproductionParameterTuningDispatchPost(
            {
              github_config: toGitHubConfigRequest(githubConfig),
              repro_id: reproId,
              repo_url: repoUrl,
            },
          ),
        githubConfig,
        setTuningStatus,
      );
      if (succeeded) {
        await fetchTuningResults(githubConfig);
      }
    },
    [runWorkflowStep, fetchTuningResults, t, reproId],
  );

  return {
    generateStatus,
    runStatus,
    tuningStatus,
    reproId,
    reproductionResults,
    tuningResults,
    isFetchingResults,
    isFetchingTuningResults,
    error,
    startGenerate,
    startRun,
    startTuning,
    fetchResults,
    fetchTuningResults,
  };
}
