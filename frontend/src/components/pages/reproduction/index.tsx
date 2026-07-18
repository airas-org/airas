import {
  FeatherBarChart3,
  FeatherCode,
  FeatherPlay,
  FeatherSettings,
  FeatherSliders,
} from "@subframe/core";
import { type ReactNode, useEffect, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { DispatchPaperReproductionGenerateRequestBody, type GitHubConfig } from "@/lib/api";
import { CredentialsService } from "@/lib/api/services/CredentialsService";
import { Accordion } from "@/ui/components/Accordion";
import { Badge } from "@/ui/components/Badge";
import { Button } from "@/ui/components/Button";
import { Loader } from "@/ui/components/Loader";
import { Select } from "@/ui/components/Select";
import { TextArea } from "@/ui/components/TextArea";
import { TextField } from "@/ui/components/TextField";
import { usePaperReproduction, type WorkflowStepStatus } from "./use-paper-reproduction";

function StatusBadge({ status }: { status: WorkflowStepStatus }) {
  const { t } = useTranslation();
  if (status === "idle") {
    return <Badge variant="neutral">{t("reproduction.status.idle")}</Badge>;
  }
  if (status === "dispatching" || status === "running") {
    return (
      <div className="flex items-center gap-2">
        <Loader size="small" />
        <Badge variant="brand">
          {status === "dispatching"
            ? t("reproduction.status.dispatching")
            : t("reproduction.status.running")}
        </Badge>
      </div>
    );
  }
  if (status === "succeeded") {
    return <Badge variant="success">{t("reproduction.status.succeeded")}</Badge>;
  }
  return <Badge variant="error">{t("reproduction.status.failed")}</Badge>;
}

function StepCard({
  icon,
  title,
  status,
  children,
}: {
  icon: ReactNode;
  title: string;
  status?: WorkflowStepStatus;
  children?: ReactNode;
}) {
  return (
    <div className="flex w-full flex-col items-start gap-4 rounded-lg bg-card border border-border px-4 py-4">
      <div className="flex w-full items-center gap-2">
        {icon}
        <span className="grow shrink-0 basis-0 text-body-bold font-body-bold text-default-font">
          {title}
        </span>
        {status !== undefined && <StatusBadge status={status} />}
      </div>
      {children}
    </div>
  );
}

function JsonBlock({ label, value }: { label: string; value: unknown }) {
  if (value == null) return null;
  return (
    <div className="flex w-full flex-col items-start gap-1">
      <span className="text-caption-bold font-caption-bold text-default-font">{label}</span>
      <pre className="w-full overflow-auto rounded-md bg-neutral-50 px-3 py-2 text-caption font-mono text-default-font whitespace-pre-wrap">
        {typeof value === "string" ? value : JSON.stringify(value, null, 2)}
      </pre>
    </div>
  );
}

function Base64Image({ label, base64 }: { label: string; base64: string | null | undefined }) {
  if (!base64) return null;
  return (
    <div className="flex w-full flex-col items-start gap-1">
      <span className="text-caption-bold font-caption-bold text-default-font">{label}</span>
      <img
        className="max-w-full rounded-md border border-border"
        alt={label}
        src={`data:image/png;base64,${base64}`}
      />
    </div>
  );
}

export function ReproductionPage() {
  const { t } = useTranslation();

  // Owner is configured via Settings > API Keys (GITHUB_OWNER) and resolved
  // server-side for dispatch; the client still needs it for Actions polling.
  const [githubOwner, setGithubOwner] = useState<string | null>(null);
  const [isLoadingOwner, setIsLoadingOwner] = useState(true);
  useEffect(() => {
    CredentialsService.listCredentialsAirasV1CredentialsGet()
      .then((res) => {
        const owner = res.credentials.find((c) => c.name === "GITHUB_OWNER");
        setGithubOwner(owner?.preview ?? null);
      })
      .catch(() => setGithubOwner(null))
      .finally(() => setIsLoadingOwner(false));
  }, []);

  const [repositoryName, setRepositoryName] = useState("");
  const [branchName, setBranchName] = useState("main");
  const [paperUrl, setPaperUrl] = useState("");
  const [instruction, setInstruction] = useState("");
  const [repoUrl, setRepoUrl] = useState("");
  const [githubActionsAgent, setGithubActionsAgent] =
    useState<DispatchPaperReproductionGenerateRequestBody.github_actions_agent>(
      DispatchPaperReproductionGenerateRequestBody.github_actions_agent.CLAUDE_CODE,
    );

  const {
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
  } = usePaperReproduction();

  const githubConfig = useMemo<GitHubConfig>(
    () => ({
      github_owner: githubOwner ?? "",
      repository_name: repositoryName.trim(),
      branch_name: branchName.trim(),
    }),
    [githubOwner, repositoryName, branchName],
  );

  const isOwnerConfigured = githubOwner !== null && githubOwner.length > 0;
  const isRepoConfigValid =
    isOwnerConfigured && [repositoryName, branchName].every((v) => v.trim().length > 0);
  const isGenerateFormValid = isRepoConfigValid && paperUrl.trim().length > 0;

  const isBusy =
    ["dispatching", "running"].includes(generateStatus) ||
    ["dispatching", "running"].includes(runStatus) ||
    ["dispatching", "running"].includes(tuningStatus) ||
    isFetchingResults ||
    isFetchingTuningResults;

  return (
    <div className="flex w-full grow shrink-0 basis-0 flex-col items-start gap-4 overflow-auto px-6 py-6">
      <div className="flex w-full flex-col items-start gap-1">
        <h1 className="text-heading-2 font-heading-2 text-default-font">
          {t("reproduction.title")}
        </h1>
        <p className="text-body font-body text-subtext-color">{t("reproduction.description")}</p>
      </div>

      {error !== null && (
        <div className="flex w-full items-center gap-2 rounded-md border border-error-300 bg-error-50 px-3 py-2">
          <span className="text-body font-body text-error-700">{error}</span>
        </div>
      )}

      {/* Step 1: Configuration */}
      <StepCard
        icon={<FeatherSettings className="text-body font-body text-default-font" />}
        title={t("reproduction.steps.configure")}
      >
        {!isLoadingOwner && !isOwnerConfigured && (
          <div className="flex w-full items-center gap-2 rounded-md border border-warning-300 bg-warning-50 px-3 py-2">
            <span className="text-body font-body text-warning-700">
              {t("reproduction.form.ownerNotSet")}
            </span>
          </div>
        )}
        <div className="flex w-full flex-wrap items-start gap-4">
          <TextField
            className="h-auto min-w-[144px] grow shrink-0 basis-0"
            variant="outline"
            label={t("reproduction.form.repositoryName")}
            helpText=""
          >
            <TextField.Input
              placeholder="repository-name"
              value={repositoryName}
              onChange={(e) => setRepositoryName(e.target.value)}
            />
          </TextField>
          <TextField
            className="h-auto min-w-[112px] grow shrink-0 basis-0"
            variant="outline"
            label={t("reproduction.form.branchName")}
            helpText=""
          >
            <TextField.Input
              placeholder="main"
              value={branchName}
              onChange={(e) => setBranchName(e.target.value)}
            />
          </TextField>
        </div>
        <TextField
          className="h-auto w-full flex-none"
          variant="outline"
          label={t("reproduction.form.paperUrl")}
          helpText=""
        >
          <TextField.Input
            placeholder="https://arxiv.org/abs/..."
            value={paperUrl}
            onChange={(e) => setPaperUrl(e.target.value)}
          />
        </TextField>
        <TextArea
          className="h-auto w-full flex-none"
          variant="outline"
          label={t("reproduction.form.instruction")}
          helpText={t("reproduction.form.instructionHelp")}
        >
          <TextArea.Input
            className="min-h-[96px] w-full"
            placeholder={t("reproduction.form.instructionPlaceholder")}
            value={instruction}
            onChange={(e) => setInstruction(e.target.value)}
          />
        </TextArea>
        <Accordion
          trigger={
            <div className="flex w-full items-center gap-2 rounded-md border border-border px-3 py-2">
              <span className="grow shrink-0 basis-0 text-body-bold font-body-bold text-default-font">
                {t("reproduction.form.advanced")}
              </span>
              <Accordion.Chevron />
            </div>
          }
          defaultOpen={false}
        >
          <div className="flex w-full flex-wrap items-start gap-4 px-1 py-4">
            <TextField
              className="h-auto min-w-[240px] grow shrink-0 basis-0"
              variant="outline"
              label={t("reproduction.form.repoUrl")}
              helpText={t("reproduction.form.repoUrlHelp")}
            >
              <TextField.Input
                placeholder="https://github.com/..."
                value={repoUrl}
                onChange={(e) => setRepoUrl(e.target.value)}
              />
            </TextField>
            <Select
              className="h-auto min-w-[176px] grow shrink-0 basis-0"
              variant="outline"
              label={t("reproduction.form.githubActionsAgent")}
              placeholder=""
              helpText=""
              value={githubActionsAgent}
              onValueChange={(val) =>
                setGithubActionsAgent(
                  val as DispatchPaperReproductionGenerateRequestBody.github_actions_agent,
                )
              }
            >
              <Select.Item
                value={
                  DispatchPaperReproductionGenerateRequestBody.github_actions_agent.CLAUDE_CODE
                }
              >
                Claude Code
              </Select.Item>
              <Select.Item
                value={DispatchPaperReproductionGenerateRequestBody.github_actions_agent.OPEN_CODE}
              >
                Open Code
              </Select.Item>
            </Select>
          </div>
        </Accordion>
      </StepCard>

      {/* Step 2: Code generation */}
      <StepCard
        icon={<FeatherCode className="text-body font-body text-default-font" />}
        title={t("reproduction.steps.generate")}
        status={generateStatus}
      >
        <span className="text-caption font-caption text-subtext-color">
          {t("reproduction.steps.generateHelp")}
        </span>
        {reproId !== null && (
          <span className="text-caption font-caption text-subtext-color">
            {t("reproduction.form.reproId")}: {reproId}
          </span>
        )}
        <Button
          disabled={!isGenerateFormValid || isBusy}
          onClick={() =>
            startGenerate(githubConfig, {
              paperUrl: paperUrl.trim(),
              instruction: instruction.trim(),
              repoUrl: repoUrl.trim(),
              githubActionsAgent,
            })
          }
        >
          {t("reproduction.actions.startGenerate")}
        </Button>
      </StepCard>

      {/* Step 3: Reproduction run */}
      <StepCard
        icon={<FeatherPlay className="text-body font-body text-default-font" />}
        title={t("reproduction.steps.run")}
        status={runStatus}
      >
        <span className="text-caption font-caption text-subtext-color">
          {t("reproduction.steps.runHelp")}
        </span>
        <Button
          disabled={!isRepoConfigValid || generateStatus !== "succeeded" || isBusy}
          onClick={() => startRun(githubConfig, repoUrl.trim())}
        >
          {t("reproduction.actions.startRun")}
        </Button>
      </StepCard>

      {/* Step 4: Results */}
      <StepCard
        icon={<FeatherBarChart3 className="text-body font-body text-default-font" />}
        title={t("reproduction.steps.results")}
      >
        <Button
          variant="neutral-secondary"
          disabled={
            !isRepoConfigValid || ["idle", "dispatching", "running"].includes(runStatus) || isBusy
          }
          loading={isFetchingResults}
          onClick={() => fetchResults(githubConfig)}
        >
          {t("reproduction.actions.fetchResults")}
        </Button>
        {reproductionResults !== null && (
          <div className="flex w-full flex-col items-start gap-3">
            <JsonBlock
              label={t("reproduction.results.finalStatus")}
              value={reproductionResults.final_status}
            />
            <JsonBlock
              label={t("reproduction.results.validation")}
              value={reproductionResults.validation}
            />
            <JsonBlock
              label={t("reproduction.results.result")}
              value={reproductionResults.result}
            />
            <JsonBlock
              label={t("reproduction.results.reproMd")}
              value={reproductionResults.repro_md}
            />
            <Base64Image
              label={t("reproduction.results.reproImage")}
              base64={reproductionResults.repro_png_base64}
            />
          </div>
        )}
      </StepCard>

      {/* Step 5: Parameter tuning (optional) */}
      <StepCard
        icon={<FeatherSliders className="text-body font-body text-default-font" />}
        title={t("reproduction.steps.tuning")}
        status={tuningStatus}
      >
        <span className="text-caption font-caption text-subtext-color">
          {t("reproduction.steps.tuningHelp")}
        </span>
        <div className="flex items-center gap-2">
          <Button
            disabled={!isRepoConfigValid || reproductionResults === null || isBusy}
            onClick={() => startTuning(githubConfig, repoUrl.trim())}
          >
            {t("reproduction.actions.startTuning")}
          </Button>
          <Button
            variant="neutral-secondary"
            disabled={!isRepoConfigValid || reproductionResults === null || isBusy}
            loading={isFetchingTuningResults}
            onClick={() => fetchTuningResults(githubConfig)}
          >
            {t("reproduction.actions.fetchTuningResults")}
          </Button>
        </div>
        {tuningResults !== null && (
          <div className="flex w-full flex-col items-start gap-3">
            <JsonBlock
              label={t("reproduction.results.finalStatus")}
              value={tuningResults.final_status}
            />
            <JsonBlock label={t("reproduction.results.result")} value={tuningResults.result} />
            <Base64Image
              label={t("reproduction.results.tuningFigure")}
              base64={tuningResults.tuning_figure_png_base64}
            />
          </div>
        )}
      </StepCard>
    </div>
  );
}
