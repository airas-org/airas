import {
  FeatherArrowLeft,
  FeatherBarChart3,
  FeatherGithub,
  FeatherPlay,
  FeatherSettings,
} from "@subframe/core";
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { AllLLMConfig } from "@/components/features/llm-config";
import {
  defaultRunnerConfigFormState,
  isRunnerConfigFormValid,
  RunnerConfigForm,
  type RunnerConfigFormState,
  toRunnerConfigPayload,
} from "@/components/features/runner-config-form";
import {
  type ComputeEnvironment,
  type TopicOpenEndedResearchLLMMapping,
  TopicOpenEndedResearchRequestBody,
  TopicOpenEndedResearchService,
} from "@/lib/api";
import { Accordion } from "@/ui/components/Accordion";
import { Button } from "@/ui/components/Button";
import { LinkButton } from "@/ui/components/LinkButton";
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
  const [ceOs, setCeOs] = useState("");
  const [ceCpuCores, setCeCpuCores] = useState("");
  const [ceRamGb, setCeRamGb] = useState("");
  const [ceGpuType, setCeGpuType] = useState("");
  const [ceGpuCount, setCeGpuCount] = useState("");
  const [ceGpuMemoryGb, setCeGpuMemoryGb] = useState("");
  const [ceCudaVersion, setCeCudaVersion] = useState("");
  const [cePythonVersion, setCePythonVersion] = useState("");
  const [ceStorageType, setCeStorageType] = useState<"nvme" | "ssd" | "hdd" | "">("");
  const [ceStorageGb, setCeStorageGb] = useState("");
  const [ceDescription, setCeDescription] = useState("");

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

    const computeEnvironment: ComputeEnvironment = {
      os: ceOs || undefined,
      cpu_cores: toInteger(ceCpuCores),
      ram_gb: toInteger(ceRamGb),
      gpu_type: ceGpuType || undefined,
      gpu_count: toInteger(ceGpuCount),
      gpu_memory_gb: toInteger(ceGpuMemoryGb),
      cuda_version: ceCudaVersion || undefined,
      python_version: cePythonVersion || undefined,
      storage_type: (ceStorageType as "nvme" | "ssd" | "hdd") || undefined,
      storage_gb: toInteger(ceStorageGb),
      description: ceDescription || undefined,
    };

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
      const response =
        await TopicOpenEndedResearchService.executeTopicOpenEndedResearchAirasV1TopicOpenEndedResearchRunPost(
          payload,
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
    ceOs,
    ceCpuCores,
    ceRamGb,
    ceGpuType,
    ceGpuCount,
    ceGpuMemoryGb,
    ceCudaVersion,
    cePythonVersion,
    ceStorageType,
    ceStorageGb,
    ceDescription,
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
      <div className="flex w-full flex-col border-b border-solid border-neutral-border bg-default-background px-6 pt-1 pb-2 sticky top-0 z-10 gap-1">
        <div className="flex w-full items-center">
          <LinkButton variant="neutral" icon={<FeatherArrowLeft />} onClick={onBack}>
            <span className="text-caption font-caption">
              {t("autonomous.topicDriven.backToList")}
            </span>
          </LinkButton>
        </div>
        <span className="text-body-bold font-body-bold text-default-font">
          Topic-Driven Research
        </span>
      </div>
      <div className="flex w-full grow shrink-0 basis-0 flex-col items-center px-6 py-6 overflow-auto">
        <div className="flex w-full max-w-[1024px] flex-col items-start gap-6 rounded-xl border border-solid border-neutral-border bg-neutral-800 px-6 py-6 shadow-sm">
          <span className="text-heading-2 font-heading-2 text-default-font">
            {t("autonomous.topicDriven.newSessionTitle")}
          </span>
          <div className="flex h-px w-full flex-none flex-col items-center gap-2 bg-neutral-border" />

          <div className="flex w-full flex-col items-start gap-2">
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
            <div className="flex min-w-[320px] grow shrink-0 basis-0 flex-col items-start gap-4 rounded-lg bg-neutral-900 px-4 py-4">
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
              <div className="flex w-full flex-col items-start gap-4 rounded-lg bg-neutral-900 px-4 py-4">
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
                  <div className="flex w-full items-center gap-2 rounded-lg bg-neutral-900 px-4 py-3">
                    <FeatherSettings className="text-body font-body text-default-font" />
                    <span className="grow shrink-0 basis-0 text-body-bold font-body-bold text-default-font">
                      {t("autonomous.topicDriven.computeEnvironment")}
                    </span>
                    <Accordion.Chevron />
                  </div>
                }
                defaultOpen={false}
              >
                <div className="flex w-full flex-col items-start gap-3 px-4 py-4">
                  <div className="flex w-full flex-wrap items-start gap-3">
                    <TextField
                      className="h-auto min-w-[120px] grow shrink-0 basis-0"
                      variant="outline"
                      label="OS"
                      helpText=""
                    >
                      <TextField.Input
                        placeholder="Ubuntu 22.04"
                        value={ceOs}
                        onChange={(e) => setCeOs(e.target.value)}
                      />
                    </TextField>
                    <TextField
                      className="h-auto min-w-[120px] grow shrink-0 basis-0"
                      variant="outline"
                      label={t("autonomous.topicDriven.ceCpuCores")}
                      helpText=""
                    >
                      <TextField.Input
                        type="number"
                        placeholder="8"
                        value={ceCpuCores}
                        onChange={(e) => setCeCpuCores(e.target.value)}
                      />
                    </TextField>
                    <TextField
                      className="h-auto min-w-[120px] grow shrink-0 basis-0"
                      variant="outline"
                      label="RAM (GB)"
                      helpText=""
                    >
                      <TextField.Input
                        type="number"
                        placeholder="64"
                        value={ceRamGb}
                        onChange={(e) => setCeRamGb(e.target.value)}
                      />
                    </TextField>
                  </div>
                  <div className="flex w-full flex-wrap items-start gap-3">
                    <TextField
                      className="h-auto min-w-[120px] grow shrink-0 basis-0"
                      variant="outline"
                      label={t("autonomous.topicDriven.ceGpuType")}
                      helpText=""
                    >
                      <TextField.Input
                        placeholder="NVIDIA A100"
                        value={ceGpuType}
                        onChange={(e) => setCeGpuType(e.target.value)}
                      />
                    </TextField>
                    <TextField
                      className="h-auto min-w-[120px] grow shrink-0 basis-0"
                      variant="outline"
                      label={t("autonomous.topicDriven.ceGpuCount")}
                      helpText=""
                    >
                      <TextField.Input
                        type="number"
                        placeholder="1"
                        value={ceGpuCount}
                        onChange={(e) => setCeGpuCount(e.target.value)}
                      />
                    </TextField>
                    <TextField
                      className="h-auto min-w-[120px] grow shrink-0 basis-0"
                      variant="outline"
                      label="GPU VRAM (GB)"
                      helpText=""
                    >
                      <TextField.Input
                        type="number"
                        placeholder="40"
                        value={ceGpuMemoryGb}
                        onChange={(e) => setCeGpuMemoryGb(e.target.value)}
                      />
                    </TextField>
                  </div>
                  <div className="flex w-full flex-wrap items-start gap-3">
                    <TextField
                      className="h-auto min-w-[120px] grow shrink-0 basis-0"
                      variant="outline"
                      label="CUDA"
                      helpText=""
                    >
                      <TextField.Input
                        placeholder="12.1"
                        value={ceCudaVersion}
                        onChange={(e) => setCeCudaVersion(e.target.value)}
                      />
                    </TextField>
                    <TextField
                      className="h-auto min-w-[120px] grow shrink-0 basis-0"
                      variant="outline"
                      label="Python"
                      helpText=""
                    >
                      <TextField.Input
                        placeholder="3.11"
                        value={cePythonVersion}
                        onChange={(e) => setCePythonVersion(e.target.value)}
                      />
                    </TextField>
                    <Select
                      className="h-auto min-w-[120px] grow shrink-0 basis-0"
                      variant="outline"
                      label={t("autonomous.topicDriven.ceStorageType")}
                      placeholder="--"
                      helpText=""
                      value={ceStorageType}
                      onValueChange={(val) => setCeStorageType(val as "nvme" | "ssd" | "hdd" | "")}
                    >
                      <Select.Item value="nvme">NVMe</Select.Item>
                      <Select.Item value="ssd">SSD</Select.Item>
                      <Select.Item value="hdd">HDD</Select.Item>
                    </Select>
                    <TextField
                      className="h-auto min-w-[120px] grow shrink-0 basis-0"
                      variant="outline"
                      label={t("autonomous.topicDriven.ceStorageGb")}
                      helpText=""
                    >
                      <TextField.Input
                        type="number"
                        placeholder="500"
                        value={ceStorageGb}
                        onChange={(e) => setCeStorageGb(e.target.value)}
                      />
                    </TextField>
                  </div>
                  <TextArea
                    className="h-auto w-full flex-none"
                    variant="outline"
                    label={t("autonomous.topicDriven.ceDescription")}
                    helpText=""
                  >
                    <TextArea.Input
                      placeholder={t("autonomous.topicDriven.ceDescriptionPlaceholder")}
                      value={ceDescription}
                      onChange={(e) => setCeDescription(e.target.value)}
                    />
                  </TextArea>
                </div>
              </Accordion>

              {/* W&B */}
              <div className="flex w-full flex-col items-start gap-4 rounded-lg bg-neutral-900 px-4 py-4">
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
              <div className="flex w-full items-center gap-2 rounded-lg bg-neutral-900 px-4 py-3">
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
              <div className="flex w-full items-center gap-2 rounded-lg bg-neutral-900 px-4 py-3">
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

          <div className="flex h-px w-full flex-none flex-col items-center gap-2 bg-neutral-border" />
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
