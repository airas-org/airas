import { FeatherBarChart3, FeatherGithub, FeatherPlay, FeatherSettings } from "@subframe/core";
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import {
  ComputeEnvironmentForm,
  type ComputeEnvironmentFormState,
  defaultComputeEnvironmentFormState,
  toComputeEnvironmentPayload,
} from "@/components/features/compute-environment-form";
import { AllLLMConfig } from "@/components/features/llm-config";
import {
  defaultRunnerConfigFormState,
  isRunnerConfigFormValid,
  RunnerConfigForm,
  type RunnerConfigFormState,
  toRunnerConfigPayload,
} from "@/components/features/runner-config-form";
import {
  type TopicOpenEndedResearchLLMMapping,
  TopicOpenEndedResearchRequestBody,
  TopicOpenEndedResearchService,
} from "@/lib/api";
import { Accordion } from "@/ui/components/Accordion";
import { Button } from "@/ui/components/Button";
import { Select } from "@/ui/components/Select";
import { Switch } from "@/ui/components/Switch";
import { TextArea } from "@/ui/components/TextArea";
import { TextField } from "@/ui/components/TextField";

interface TopicDrivenInputProps {
  onBack: () => void;
  onResearchStarted: (taskId: string) => void;
}

export function TopicDrivenInput({ onBack, onResearchStarted }: TopicDrivenInputProps) {
  const { t } = useTranslation();
  const [researchTopic, setResearchTopic] = useState(
    "Proposing an improved Chain-of-Thought based on human thinking methods, evaluated purely through prompt tuning without fine-tuning or time-intensive experiments",
  );
  const [repoName, setRepoName] = useState("");
  const [branch, setBranch] = useState("main");

  // Runner config
  const [runnerConfig, setRunnerConfig] = useState<RunnerConfigFormState>(
    defaultRunnerConfigFormState,
  );

  // Compute environment
  const [computeEnv, setComputeEnv] = useState<ComputeEnvironmentFormState>(
    defaultComputeEnvironmentFormState,
  );

  const [wandbEntity, setWandbEntity] = useState("airas");
  const [wandbProject, setWandbProject] = useState("");
  const [isPrivate, setIsPrivate] = useState(false);

  const [numPaperSearchQueries, setNumPaperSearchQueries] = useState("2");
  const [papersPerQuery, setPapersPerQuery] = useState("2");
  const [hypothesisRefinementIterations, setHypothesisRefinementIterations] = useState("1");
  const [numExperimentModels, setNumExperimentModels] = useState("1");
  const [numExperimentDatasets, setNumExperimentDatasets] = useState("1");
  const [numComparativeMethods, setNumComparativeMethods] = useState("1");
  const [experimentCodeValidationIterations, setExperimentCodeValidationIterations] = useState("4");
  const [paperContentRefinementIterations, setPaperContentRefinementIterations] = useState("2");
  const [githubActionsAgent, setGithubActionsAgent] = useState<
    TopicOpenEndedResearchRequestBody.github_actions_agent | ""
  >("");
  const [latexTemplateName, setLatexTemplateName] = useState("mdpi");
  const [llmMapping, setLlmMapping] = useState<TopicOpenEndedResearchLLMMapping | null>(null);

  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isFormValid =
    [researchTopic, repoName, branch, wandbEntity, wandbProject].every(
      (value) => value.trim().length > 0,
    ) && isRunnerConfigFormValid(runnerConfig);

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

    const payload: TopicOpenEndedResearchRequestBody = {
      github_config: {
        repository_name: repoName,
        branch_name: branch,
      },
      research_topic: researchTopic,
      compute_environment: computeEnvironment,
      runner_config: runnerConfigPayload,
      wandb_config: {
        entity: wandbEntity,
        project: wandbProject,
      },
      is_github_repo_private: isPrivate,
      num_paper_search_queries: toInteger(numPaperSearchQueries),
      papers_per_query: toInteger(papersPerQuery),
      hypothesis_refinement_iterations: toInteger(hypothesisRefinementIterations),
      num_experiment_models: toInteger(numExperimentModels),
      num_experiment_datasets: toInteger(numExperimentDatasets),
      num_comparison_methods: toInteger(numComparativeMethods),
      paper_content_refinement_iterations: toInteger(paperContentRefinementIterations),
      github_actions_agent: githubActionsAgent || undefined,
      latex_template_name: latexTemplateName.trim() || undefined,
      llm_mapping: llmMapping,
    };

    try {
      const githubSession = localStorage.getItem("github_session_token");
      const response =
        await TopicOpenEndedResearchService.executeTopicOpenEndedResearchAirasV1TopicOpenEndedResearchRunPost(
          payload,
          githubSession,
        );
      onResearchStarted(response.task_id);
    } catch (err) {
      const message = err instanceof Error ? err.message : t("autonomous.topicDriven.runError");
      setError(message);
      setIsRunning(false);
    }
  }, [
    isFormValid,
    researchTopic,
    repoName,
    branch,
    runnerConfig,
    computeEnv,
    wandbEntity,
    wandbProject,
    isPrivate,
    numPaperSearchQueries,
    papersPerQuery,
    hypothesisRefinementIterations,
    numExperimentModels,
    numExperimentDatasets,
    numComparativeMethods,
    paperContentRefinementIterations,
    githubActionsAgent,
    latexTemplateName,
    llmMapping,
    onResearchStarted,
    t,
  ]);

  return (
    <div className="flex h-full w-full flex-col items-start bg-default-background">
      <div className="relative flex w-full items-center bg-default-background px-6 py-3 sticky top-0 z-10">
        <button
          type="button"
          onClick={onBack}
          className="rounded-md px-2 py-1 text-sm font-medium text-neutral-700 hover:bg-neutral-50 active:bg-neutral-100 transition-colors cursor-pointer"
        >
          {t("autonomous.topicDriven.backToList")}
        </button>
        <span className="absolute left-1/2 -translate-x-1/2 text-body-bold font-body-bold text-default-font">
          Topic-Driven Research
        </span>
      </div>
      <div className="flex w-full grow shrink-0 basis-0 flex-col items-center px-6 py-6 overflow-auto">
        <div className="flex w-full max-w-[1024px] flex-col items-start gap-6">
          <div className="flex w-full flex-col items-start gap-2 rounded-lg bg-card border border-border px-4 py-4">
            <div className="flex items-center gap-1">
              <span className="text-body-bold font-body-bold text-default-font">
                {t("autonomous.topicDriven.researchTopic")}
              </span>
              <span className="text-body font-body text-error-500">*</span>
            </div>
            <TextArea className="h-auto w-full flex-none" variant="outline" label="" helpText="">
              <TextArea.Input
                placeholder={t("autonomous.topicDriven.researchTopicPlaceholder")}
                value={researchTopic}
                onChange={(e) => setResearchTopic(e.target.value)}
              />
            </TextArea>
          </div>

          <div className="flex w-full flex-wrap items-start gap-4">
            <div className="flex min-w-[320px] grow shrink-0 basis-0 flex-col items-start gap-4 rounded-lg bg-card border border-border px-4 py-4">
              <div className="flex w-full items-center gap-2">
                <FeatherGithub className="text-body font-body text-default-font" />
                <span className="text-body-bold font-body-bold text-default-font">
                  {t("autonomous.topicDriven.githubSettings")}
                </span>
              </div>
              <div className="flex w-full flex-wrap items-start gap-3">
                <div className="flex min-w-[112px] grow shrink-0 basis-0 flex-col items-start gap-1">
                  <div className="flex items-center gap-1">
                    <span className="text-caption font-caption text-default-font">
                      {t("autonomous.topicDriven.repository")}
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
                      {t("autonomous.topicDriven.branch")}
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
                  {t("autonomous.topicDriven.makePrivate")}
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
                    runnerType: t("autonomous.topicDriven.runnerType"),
                    runnerTypeStatic: t("autonomous.topicDriven.runnerTypeStatic"),
                    runnerTypeCloud: t("autonomous.topicDriven.runnerTypeCloud"),
                    runnerLabel: t("autonomous.topicDriven.runnerLabel"),
                    cloudProvider: t("autonomous.topicDriven.cloudProvider"),
                    gpuInstanceType: t("autonomous.topicDriven.gpuInstanceType"),
                    maxInstanceHours: t("autonomous.topicDriven.maxInstanceHours"),
                  }}
                />
              </div>

              {/* Compute Environment */}
              <Accordion
                trigger={
                  <div className="flex w-full items-center gap-2 rounded-lg bg-card border border-border px-4 py-3">
                    <FeatherSettings className="text-body font-body text-default-font" />
                    <span className="grow shrink-0 basis-0 text-body-bold font-body-bold text-default-font">
                      {t("autonomous.topicDriven.computeEnvironment")}
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
                      cpuCores: t("autonomous.topicDriven.ceCpuCores"),
                      gpuType: t("autonomous.topicDriven.ceGpuType"),
                      gpuCount: t("autonomous.topicDriven.ceGpuCount"),
                      storageType: t("autonomous.topicDriven.ceStorageType"),
                      storageGb: t("autonomous.topicDriven.ceStorageGb"),
                      description: t("autonomous.topicDriven.ceDescription"),
                      descriptionPlaceholder: t("autonomous.topicDriven.ceDescriptionPlaceholder"),
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
                  {t("autonomous.topicDriven.advancedSettings")}
                </span>
                <Accordion.Chevron />
              </div>
            }
            defaultOpen={false}
          >
            <div className="flex w-full grow shrink-0 basis-0 flex-col items-start gap-4 px-4 py-4">
              <div className="flex w-full flex-wrap items-start gap-4">
                <TextField
                  className="h-auto min-w-[144px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.topicDriven.numPaperSearchQueries")}
                  helpText=""
                >
                  <TextField.Input
                    type="number"
                    placeholder="2"
                    value={numPaperSearchQueries}
                    onChange={(e) => setNumPaperSearchQueries(e.target.value)}
                  />
                </TextField>
                <TextField
                  className="h-auto min-w-[144px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.topicDriven.papersPerQuery")}
                  helpText=""
                >
                  <TextField.Input
                    type="number"
                    placeholder="2"
                    value={papersPerQuery}
                    onChange={(e) => setPapersPerQuery(e.target.value)}
                  />
                </TextField>
                <TextField
                  className="h-auto min-w-[144px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.topicDriven.hypothesisRefinementIterations")}
                  helpText=""
                >
                  <TextField.Input
                    type="number"
                    placeholder="1"
                    value={hypothesisRefinementIterations}
                    onChange={(e) => setHypothesisRefinementIterations(e.target.value)}
                  />
                </TextField>
              </div>
              <div className="flex w-full flex-wrap items-start gap-4">
                <TextField
                  className="h-auto min-w-[144px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.topicDriven.numExperimentModels")}
                  helpText=""
                >
                  <TextField.Input
                    type="number"
                    placeholder="1"
                    value={numExperimentModels}
                    onChange={(e) => setNumExperimentModels(e.target.value)}
                  />
                </TextField>
                <TextField
                  className="h-auto min-w-[144px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.topicDriven.numExperimentDatasets")}
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
                  label={t("autonomous.topicDriven.numComparativeMethods")}
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
                  label={t("autonomous.topicDriven.codeValidationIterations")}
                  helpText=""
                >
                  <TextField.Input
                    type="number"
                    placeholder="4"
                    value={experimentCodeValidationIterations}
                    onChange={(e) => setExperimentCodeValidationIterations(e.target.value)}
                  />
                </TextField>
                <TextField
                  className="h-auto min-w-[144px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.topicDriven.paperRefinementIterations")}
                  helpText=""
                >
                  <TextField.Input
                    type="number"
                    placeholder="2"
                    value={paperContentRefinementIterations}
                    onChange={(e) => setPaperContentRefinementIterations(e.target.value)}
                  />
                </TextField>
              </div>
              <div className="flex w-full flex-wrap items-start gap-4">
                <Select
                  className="h-auto min-w-[176px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.topicDriven.githubActionsAgent")}
                  placeholder={t("autonomous.topicDriven.selectPlaceholder")}
                  helpText=""
                  value={githubActionsAgent}
                  onValueChange={(val) =>
                    setGithubActionsAgent(
                      val as TopicOpenEndedResearchRequestBody.github_actions_agent | "",
                    )
                  }
                >
                  <Select.Item
                    value={TopicOpenEndedResearchRequestBody.github_actions_agent.CLAUDE_CODE}
                  >
                    Claude Code
                  </Select.Item>
                  <Select.Item
                    value={TopicOpenEndedResearchRequestBody.github_actions_agent.OPEN_CODE}
                  >
                    Open Code
                  </Select.Item>
                </Select>
                <Select
                  className="h-auto min-w-[176px] grow shrink-0 basis-0"
                  variant="outline"
                  label={t("autonomous.topicDriven.latexTemplate")}
                  placeholder={t("autonomous.topicDriven.selectPlaceholder")}
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
                  {t("autonomous.topicDriven.llmSettings")}
                </span>
                <Accordion.Chevron />
              </div>
            }
            defaultOpen={false}
          >
            <div className="flex w-full grow shrink-0 basis-0 flex-col items-start gap-4 px-4 py-4">
              <AllLLMConfig llmMapping={llmMapping} onChange={setLlmMapping} hideToggle />
            </div>
          </Accordion>

          {error && (
            <div className="flex w-full items-center rounded-md bg-error-50 px-4 py-3">
              <span className="text-body font-body text-error-600">{error}</span>
            </div>
          )}

          <div className="flex w-full items-center justify-end gap-3">
            <Button variant="neutral-secondary" onClick={onBack}>
              {t("autonomous.topicDriven.cancel")}
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
              {isRunning ? t("autonomous.topicDriven.running") : t("autonomous.topicDriven.run")}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
