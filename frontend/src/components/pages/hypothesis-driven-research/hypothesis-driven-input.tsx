import {
  FeatherBarChart3,
  FeatherGithub,
  FeatherLayoutList,
  FeatherLightbulb,
  FeatherPlay,
  FeatherSettings,
} from "@subframe/core";
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ComputeEnvironmentForm,
  type ComputeEnvironmentFormState,
  defaultComputeEnvironmentFormState,
  toComputeEnvironmentPayload,
} from "@/components/features/compute-environment-form";
import { HypothesisAllLLMConfig } from "@/components/features/llm-config";
import {
  defaultRunnerConfigFormState,
  isRunnerConfigFormValid,
  RunnerConfigForm,
  type RunnerConfigFormState,
  toRunnerConfigPayload,
} from "@/components/features/runner-config-form";
import {
  type HypothesisDrivenResearchLLMMapping,
  HypothesisDrivenResearchRequestBody,
  HypothesisDrivenResearchService,
} from "@/lib/api";
import { Accordion } from "@/ui/components/Accordion";
import { Button } from "@/ui/components/Button";
import { Select } from "@/ui/components/Select";
import { Switch } from "@/ui/components/Switch";
import { TextArea } from "@/ui/components/TextArea";
import { TextField } from "@/ui/components/TextField";

interface HypothesisDrivenInputProps {
  onBack: () => void;
  onResearchStarted: (taskId: string) => void;
}

export function HypothesisDrivenInput({ onBack, onResearchStarted }: HypothesisDrivenInputProps) {
  const { t } = useTranslation();
  // Research hypothesis fields
  const [openProblems, setOpenProblems] = useState("");
  const [method, setMethod] = useState("");
  const [experimentalSetup, setExperimentalSetup] = useState("");
  const [primaryMetric, setPrimaryMetric] = useState("");
  const [experimentalCode, setExperimentalCode] = useState("");
  const [expectedResult, setExpectedResult] = useState("");
  const [expectedConclusion, setExpectedConclusion] = useState("");

  // Optional research topic
  const [researchTopic, setResearchTopic] = useState("");

  // GitHub config
  const [repoName, setRepoName] = useState("");
  const [branch, setBranch] = useState("main");
  const [isPrivate, setIsPrivate] = useState(false);

  // Runner config
  const [runnerConfig, setRunnerConfig] = useState<RunnerConfigFormState>(
    defaultRunnerConfigFormState,
  );

  // Compute environment
  const [computeEnv, setComputeEnv] = useState<ComputeEnvironmentFormState>(
    defaultComputeEnvironmentFormState,
  );

  // W&B config
  const [wandbEntity, setWandbEntity] = useState("");
  const [wandbProject, setWandbProject] = useState("");

  // Advanced settings
  const [githubActionsAgent, setGithubActionsAgent] = useState<
    HypothesisDrivenResearchRequestBody.github_actions_agent | ""
  >("");
  const [numExperimentModels, setNumExperimentModels] = useState("1");
  const [numExperimentDatasets, setNumExperimentDatasets] = useState("1");
  const [numComparativeMethods, setNumComparativeMethods] = useState("1");
  const [paperContentRefinementIterations, setPaperContentRefinementIterations] = useState("2");
  const [latexTemplateName, setLatexTemplateName] = useState("mdpi");

  // LLM config
  const [llmMapping, setLlmMapping] = useState<HypothesisDrivenResearchLLMMapping | null>(null);

  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isFormValid =
    [
      openProblems,
      method,
      experimentalSetup,
      primaryMetric,
      experimentalCode,
      expectedResult,
      expectedConclusion,
      repoName,
      branch,
      wandbEntity,
      wandbProject,
    ].every((v) => v.trim().length > 0) && isRunnerConfigFormValid(runnerConfig);

  const handleRun = useCallback(async () => {
    if (!isFormValid) return;
    setError(null);
    setIsRunning(true);

    const toInteger = (value: string): number | undefined => {
      if (value.trim() === "") return undefined;
      const parsed = Number(value);
      return Number.isInteger(parsed) ? parsed : undefined;
    };

    const computeEnvironment = toComputeEnvironmentPayload(computeEnv);
    const runnerConfigPayload = toRunnerConfigPayload(runnerConfig);

    const payload = {
      github_config: {
        repository_name: repoName,
        branch_name: branch,
      },
      research_hypothesis: {
        open_problems: openProblems,
        method,
        experimental_setup: experimentalSetup,
        primary_metric: primaryMetric,
        experimental_code: experimentalCode,
        expected_result: expectedResult,
        expected_conclusion: expectedConclusion,
      },
      research_topic: researchTopic.trim() || undefined,
      compute_environment: computeEnvironment,
      runner_config: runnerConfigPayload,
      wandb_config: {
        entity: wandbEntity,
        project: wandbProject,
      },
      is_github_repo_private: isPrivate,
      github_actions_agent: githubActionsAgent || undefined,
      num_experiment_models: toInteger(numExperimentModels),
      num_experiment_datasets: toInteger(numExperimentDatasets),
      num_comparison_methods: toInteger(numComparativeMethods),
      paper_content_refinement_iterations: toInteger(paperContentRefinementIterations),
      latex_template_name: latexTemplateName.trim() || undefined,
      llm_mapping: llmMapping,
    };

    try {
      const githubSession = localStorage.getItem("github_session_token");
      const response =
        await HypothesisDrivenResearchService.executeHypothesisDrivenResearchAirasV1HypothesisDrivenResearchRunPost(
          payload,
          githubSession,
        );
      onResearchStarted(response.task_id);
    } catch (err) {
      const message =
        err instanceof Error ? err.message : t("autonomous.hypothesisDriven.runError");
      setError(message);
      setIsRunning(false);
    }
  }, [
    isFormValid,
    openProblems,
    method,
    experimentalSetup,
    primaryMetric,
    experimentalCode,
    expectedResult,
    expectedConclusion,
    researchTopic,
    repoName,
    branch,
    isPrivate,
    runnerConfig,
    computeEnv,
    wandbEntity,
    wandbProject,
    githubActionsAgent,
    numExperimentModels,
    numExperimentDatasets,
    numComparativeMethods,
    paperContentRefinementIterations,
    latexTemplateName,
    llmMapping,
    onResearchStarted,
    t,
  ]);

  return (
    <div className="flex h-full w-full flex-col bg-default-background">
      <div className="flex-shrink-0 px-6 py-6">
        <button
          type="button"
          onClick={onBack}
          className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium text-neutral-500 hover:bg-neutral-50 active:bg-neutral-100 transition-colors cursor-pointer"
        >
          <FeatherLayoutList className="h-4 w-4" />
          {t("autonomous.hypothesisDriven.backToList")}
        </button>
      </div>
      <div className="flex-1 overflow-auto px-6 pb-6">
        <div className="flex w-full max-w-[768px] flex-col items-start gap-6">
          <div className="flex w-full flex-col items-start gap-2 rounded-lg bg-card border border-border px-4 py-4">
            <span className="text-body font-body text-subtext-color">
              {t("autonomous.hypothesisDriven.researchTopic")}
            </span>
            <TextField className="h-auto w-full flex-none" variant="outline" label="" helpText="">
              <TextField.Input
                placeholder={t("autonomous.hypothesisDriven.researchTopicPlaceholder")}
                value={researchTopic}
                onChange={(e) => setResearchTopic(e.target.value)}
              />
            </TextField>
          </div>

          <div className="flex w-full flex-col items-start gap-4 rounded-lg bg-card border border-border px-4 py-4">
            <div className="flex w-full items-center gap-2">
              <FeatherLightbulb className="text-body font-body text-default-font" />
              <span className="text-body-bold font-body-bold text-default-font">
                {t("autonomous.hypothesisDriven.hypothesis")}
              </span>
            </div>
            <div className="flex w-full flex-wrap items-start gap-4">
              <div className="flex min-w-[280px] grow shrink-0 basis-0 flex-col items-start gap-1">
                <div className="flex items-center gap-1">
                  <span className="text-caption font-caption text-default-font">
                    {t("autonomous.hypothesisDriven.openProblems")}
                  </span>
                  <span className="text-caption font-caption text-error-500">*</span>
                </div>
                <TextArea
                  className="h-auto w-full flex-none"
                  variant="outline"
                  label=""
                  helpText=""
                >
                  <TextArea.Input
                    placeholder="例: Existing models struggle with temporal reasoning in long videos"
                    value={openProblems}
                    onChange={(e) => setOpenProblems(e.target.value)}
                  />
                </TextArea>
              </div>
              <div className="flex min-w-[280px] grow shrink-0 basis-0 flex-col items-start gap-1">
                <div className="flex items-center gap-1">
                  <span className="text-caption font-caption text-default-font">
                    {t("autonomous.hypothesisDriven.proposedMethod")}
                  </span>
                  <span className="text-caption font-caption text-error-500">*</span>
                </div>
                <TextArea
                  className="h-auto w-full flex-none"
                  variant="outline"
                  label=""
                  helpText=""
                >
                  <TextArea.Input
                    placeholder="例: A hierarchical attention mechanism that models temporal dependencies"
                    value={method}
                    onChange={(e) => setMethod(e.target.value)}
                  />
                </TextArea>
              </div>
            </div>
            <div className="flex w-full flex-wrap items-start gap-4">
              <div className="flex min-w-[280px] grow shrink-0 basis-0 flex-col items-start gap-1">
                <div className="flex items-center gap-1">
                  <span className="text-caption font-caption text-default-font">
                    {t("autonomous.hypothesisDriven.experimentalSetup")}
                  </span>
                  <span className="text-caption font-caption text-error-500">*</span>
                </div>
                <TextArea
                  className="h-auto w-full flex-none"
                  variant="outline"
                  label=""
                  helpText=""
                >
                  <TextArea.Input
                    placeholder="例: Evaluate on ActivityNet-QA and EgoSchema benchmarks"
                    value={experimentalSetup}
                    onChange={(e) => setExperimentalSetup(e.target.value)}
                  />
                </TextArea>
              </div>
              <div className="flex min-w-[280px] grow shrink-0 basis-0 flex-col items-start gap-1">
                <div className="flex items-center gap-1">
                  <span className="text-caption font-caption text-default-font">
                    {t("autonomous.hypothesisDriven.primaryMetric")}
                  </span>
                  <span className="text-caption font-caption text-error-500">*</span>
                </div>
                <TextField
                  className="h-auto w-full flex-none"
                  variant="outline"
                  label=""
                  helpText=""
                >
                  <TextField.Input
                    placeholder="例: Accuracy on ActivityNet-QA"
                    value={primaryMetric}
                    onChange={(e) => setPrimaryMetric(e.target.value)}
                  />
                </TextField>
              </div>
            </div>
            <div className="flex w-full flex-wrap items-start gap-4">
              <div className="flex min-w-[280px] grow shrink-0 basis-0 flex-col items-start gap-1">
                <div className="flex items-center gap-1">
                  <span className="text-caption font-caption text-default-font">
                    {t("autonomous.hypothesisDriven.experimentalCode")}
                  </span>
                  <span className="text-caption font-caption text-error-500">*</span>
                </div>
                <TextArea
                  className="h-auto w-full flex-none"
                  variant="outline"
                  label=""
                  helpText=""
                >
                  <TextArea.Input
                    placeholder="例: PyTorch implementation using transformers library"
                    value={experimentalCode}
                    onChange={(e) => setExperimentalCode(e.target.value)}
                  />
                </TextArea>
              </div>
              <div className="flex min-w-[280px] grow shrink-0 basis-0 flex-col items-start gap-1">
                <div className="flex items-center gap-1">
                  <span className="text-caption font-caption text-default-font">
                    {t("autonomous.hypothesisDriven.expectedResult")}
                  </span>
                  <span className="text-caption font-caption text-error-500">*</span>
                </div>
                <TextArea
                  className="h-auto w-full flex-none"
                  variant="outline"
                  label=""
                  helpText=""
                >
                  <TextArea.Input
                    placeholder="例: 5% accuracy improvement over baseline on ActivityNet-QA"
                    value={expectedResult}
                    onChange={(e) => setExpectedResult(e.target.value)}
                  />
                </TextArea>
              </div>
            </div>
            <div className="flex w-full flex-col items-start gap-1">
              <div className="flex items-center gap-1">
                <span className="text-caption font-caption text-default-font">
                  {t("autonomous.hypothesisDriven.expectedConclusion")}
                </span>
                <span className="text-caption font-caption text-error-500">*</span>
              </div>
              <TextArea className="h-auto w-full flex-none" variant="outline" label="" helpText="">
                <TextArea.Input
                  placeholder="例: Hierarchical temporal attention significantly improves video QA"
                  value={expectedConclusion}
                  onChange={(e) => setExpectedConclusion(e.target.value)}
                />
              </TextArea>
            </div>
          </div>

          <div className="flex w-full flex-wrap items-start gap-4">
            <div className="flex min-w-[320px] grow shrink-0 basis-0 flex-col items-start gap-4 rounded-lg bg-card border border-border px-4 py-4">
              <div className="flex w-full items-center gap-2">
                <FeatherGithub className="text-body font-body text-default-font" />
                <span className="text-body-bold font-body-bold text-default-font">
                  {t("autonomous.hypothesisDriven.githubSettings")}
                </span>
              </div>
              <div className="flex w-full flex-wrap items-start gap-3">
                <div className="flex min-w-[112px] grow shrink-0 basis-0 flex-col items-start gap-1">
                  <div className="flex items-center gap-1">
                    <span className="text-caption font-caption text-default-font">
                      {t("autonomous.hypothesisDriven.repository")}
                    </span>
                    <span className="text-caption font-caption text-error-500">*</span>
                  </div>
                  <TextField
                    className="h-auto w-full flex-none"
                    variant="outline"
                    label=""
                    helpText=""
                  >
                    <TextField.Input
                      placeholder="repository-name"
                      value={repoName}
                      onChange={(e) => setRepoName(e.target.value)}
                    />
                  </TextField>
                </div>
                <div className="flex min-w-[112px] grow shrink-0 basis-0 flex-col items-start gap-1">
                  <div className="flex items-center gap-1">
                    <span className="text-caption font-caption text-default-font">
                      {t("autonomous.hypothesisDriven.branch")}
                    </span>
                    <span className="text-caption font-caption text-error-500">*</span>
                  </div>
                  <TextField
                    className="h-auto w-full flex-none"
                    variant="outline"
                    label=""
                    helpText=""
                  >
                    <TextField.Input
                      placeholder="main"
                      value={branch}
                      onChange={(e) => setBranch(e.target.value)}
                    />
                  </TextField>
                </div>
              </div>
              <div className="flex w-full items-center gap-3">
                <Switch checked={isPrivate} onCheckedChange={setIsPrivate} />
                <span className="text-body font-body text-default-font">
                  {t("autonomous.hypothesisDriven.makePrivate")}
                </span>
              </div>
            </div>

            <div className="flex min-w-[320px] grow shrink-0 basis-0 flex-col items-start gap-4">
              {/* Runner Config */}
              <div className="flex w-full flex-col items-start gap-4 rounded-lg bg-card border border-border px-4 py-4">
                <div className="flex w-full items-center gap-2">
                  <FeatherPlay className="text-body font-body text-default-font" />
                  <span className="text-body-bold font-body-bold text-default-font">
                    GitHub Actions Runner
                  </span>
                </div>
                <RunnerConfigForm
                  value={runnerConfig}
                  onChange={setRunnerConfig}
                  labels={{
                    runnerType: t("autonomous.hypothesisDriven.runnerType"),
                    runnerTypeStatic: t("autonomous.hypothesisDriven.runnerTypeStatic"),
                    runnerTypeCloud: t("autonomous.hypothesisDriven.runnerTypeCloud"),
                    runnerLabel: t("autonomous.hypothesisDriven.runnerLabel"),
                    cloudProvider: t("autonomous.hypothesisDriven.cloudProvider"),
                    gpuInstanceType: t("autonomous.hypothesisDriven.gpuInstanceType"),
                    maxInstanceHours: t("autonomous.hypothesisDriven.maxInstanceHours"),
                  }}
                />
              </div>

              {/* Compute Environment */}
              <Accordion
                trigger={
                  <div className="flex w-full items-center gap-2 rounded-lg bg-card border border-border px-4 py-3">
                    <FeatherSettings className="text-body font-body text-default-font" />
                    <span className="grow shrink-0 basis-0 text-body-bold font-body-bold text-default-font">
                      {t("autonomous.hypothesisDriven.computeEnvironment")}
                    </span>
                    <Accordion.Chevron />
                  </div>
                }
                defaultOpen={false}
              >
                <div className="px-4 py-4">
                  <ComputeEnvironmentForm
                    value={computeEnv}
                    onChange={setComputeEnv}
                    labels={{
                      cpuCores: t("autonomous.hypothesisDriven.ceCpuCores"),
                      gpuType: t("autonomous.hypothesisDriven.ceGpuType"),
                      gpuCount: t("autonomous.hypothesisDriven.ceGpuCount"),
                      storageType: t("autonomous.hypothesisDriven.ceStorageType"),
                      storageGb: t("autonomous.hypothesisDriven.ceStorageGb"),
                      description: t("autonomous.hypothesisDriven.ceDescription"),
                      descriptionPlaceholder: t(
                        "autonomous.hypothesisDriven.ceDescriptionPlaceholder",
                      ),
                    }}
                  />
                </div>
              </Accordion>

              {/* W&B */}
              <div className="flex w-full flex-col items-start gap-4 rounded-lg bg-card border border-border px-4 py-4">
                <div className="flex w-full items-center gap-2">
                  <FeatherBarChart3 className="text-body font-body text-default-font" />
                  <span className="text-body-bold font-body-bold text-default-font">
                    Weights &amp; Biases
                  </span>
                </div>
                <div className="flex w-full flex-wrap items-start gap-3">
                  <div className="flex min-w-[144px] grow shrink-0 basis-0 flex-col items-start gap-1">
                    <div className="flex items-center gap-1">
                      <span className="text-caption font-caption text-default-font">Entity</span>
                      <span className="text-caption font-caption text-error-500">*</span>
                    </div>
                    <TextField
                      className="h-auto w-full flex-none"
                      variant="outline"
                      label=""
                      helpText=""
                    >
                      <TextField.Input
                        placeholder="team-name"
                        value={wandbEntity}
                        onChange={(e) => setWandbEntity(e.target.value)}
                      />
                    </TextField>
                  </div>
                  <div className="flex min-w-[144px] grow shrink-0 basis-0 flex-col items-start gap-1">
                    <div className="flex items-center gap-1">
                      <span className="text-caption font-caption text-default-font">Project</span>
                      <span className="text-caption font-caption text-error-500">*</span>
                    </div>
                    <TextField
                      className="h-auto w-full flex-none"
                      variant="outline"
                      label=""
                      helpText=""
                    >
                      <TextField.Input
                        placeholder="project-name"
                        value={wandbProject}
                        onChange={(e) => setWandbProject(e.target.value)}
                      />
                    </TextField>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <Accordion
            trigger={
              <div className="flex w-full items-center gap-2 rounded-lg bg-card border border-border px-4 py-3">
                <FeatherSettings className="text-body font-body text-default-font" />
                <span className="grow shrink-0 basis-0 text-body-bold font-body-bold text-default-font">
                  {t("autonomous.hypothesisDriven.advancedSettings")}
                </span>
                <Accordion.Chevron />
              </div>
            }
            defaultOpen={false}
          >
            <div className="flex w-full grow shrink-0 basis-0 flex-col items-start gap-4 px-4 py-4">
              <div className="flex w-full flex-wrap items-start gap-4">
                <Select
                  className="h-auto min-w-[176px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.hypothesisDriven.githubActionsAgent")}
                  placeholder={t("autonomous.hypothesisDriven.selectPlaceholder")}
                  helpText=""
                  value={githubActionsAgent}
                  onValueChange={(val) =>
                    setGithubActionsAgent(
                      val as HypothesisDrivenResearchRequestBody.github_actions_agent | "",
                    )
                  }
                >
                  <Select.Item
                    value={HypothesisDrivenResearchRequestBody.github_actions_agent.CLAUDE_CODE}
                  >
                    Claude Code
                  </Select.Item>
                  <Select.Item
                    value={HypothesisDrivenResearchRequestBody.github_actions_agent.OPEN_CODE}
                  >
                    Open Code
                  </Select.Item>
                </Select>
                <TextField
                  className="h-auto min-w-[144px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.hypothesisDriven.numExperimentModels")}
                  helpText=""
                >
                  <TextField.Input
                    type="number"
                    placeholder="1"
                    value={numExperimentModels}
                    onChange={(e) => setNumExperimentModels(e.target.value)}
                  />
                </TextField>
              </div>
              <div className="flex w-full flex-wrap items-start gap-4">
                <TextField
                  className="h-auto min-w-[144px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.hypothesisDriven.numExperimentDatasets")}
                  helpText=""
                >
                  <TextField.Input
                    type="number"
                    placeholder="1"
                    value={numExperimentDatasets}
                    onChange={(e) => setNumExperimentDatasets(e.target.value)}
                  />
                </TextField>
                <TextField
                  className="h-auto min-w-[144px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.hypothesisDriven.numComparativeMethods")}
                  helpText=""
                >
                  <TextField.Input
                    type="number"
                    placeholder="1"
                    value={numComparativeMethods}
                    onChange={(e) => setNumComparativeMethods(e.target.value)}
                  />
                </TextField>
              </div>
              <div className="flex w-full flex-wrap items-start gap-4">
                <TextField
                  className="h-auto min-w-[144px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.hypothesisDriven.paperRefinementIterations")}
                  helpText=""
                >
                  <TextField.Input
                    type="number"
                    placeholder="2"
                    value={paperContentRefinementIterations}
                    onChange={(e) => setPaperContentRefinementIterations(e.target.value)}
                  />
                </TextField>
                <Select
                  className="h-auto min-w-[176px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.hypothesisDriven.latexTemplate")}
                  placeholder={t("autonomous.hypothesisDriven.selectPlaceholder")}
                  helpText=""
                  value={latexTemplateName}
                  onValueChange={setLatexTemplateName}
                >
                  <Select.Item value="mdpi">mdpi</Select.Item>
                  <Select.Item value="iclr2024">iclr2024</Select.Item>
                  <Select.Item value="agents4science_2025">agents4science_2025</Select.Item>
                </Select>
              </div>
            </div>
          </Accordion>

          <Accordion
            trigger={
              <div className="flex w-full items-center gap-2 rounded-lg bg-card border border-border px-4 py-3">
                <FeatherSettings className="text-body font-body text-default-font" />
                <span className="grow shrink-0 basis-0 text-body-bold font-body-bold text-default-font">
                  {t("autonomous.hypothesisDriven.llmSettings")}
                </span>
                <Accordion.Chevron />
              </div>
            }
            defaultOpen={false}
          >
            <div className="flex w-full grow shrink-0 basis-0 flex-col items-start gap-4 px-4 py-4">
              <HypothesisAllLLMConfig llmMapping={llmMapping} onChange={setLlmMapping} hideToggle />
            </div>
          </Accordion>

          {error && (
            <div className="flex w-full items-center rounded-md bg-error-50 px-4 py-3">
              <span className="text-body font-body text-error-600">{error}</span>
            </div>
          )}

          <div className="flex w-full items-center justify-end gap-3">
            <Button variant="neutral-secondary" onClick={onBack}>
              {t("autonomous.hypothesisDriven.cancel")}
            </Button>
            <Button
              className="disabled:bg-neutral-600 disabled:opacity-60 hover:disabled:bg-neutral-600 active:disabled:bg-neutral-600"
              variant="brand-primary"
              size="large"
              icon={isRunning ? undefined : <FeatherPlay />}
              loading={isRunning}
              disabled={isRunning || !isFormValid}
              onClick={handleRun}
            >
              {isRunning
                ? t("autonomous.hypothesisDriven.running")
                : t("autonomous.hypothesisDriven.run")}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
