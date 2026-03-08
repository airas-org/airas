"use client";

import {
  FeatherArrowLeft,
  FeatherBarChart3,
  FeatherGithub,
  FeatherLightbulb,
  FeatherPlay,
  FeatherSettings,
} from "@subframe/core";
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { HypothesisAllLLMConfig } from "@/components/features/llm-config";
import {
  type HypothesisDrivenResearchLLMMapping,
  HypothesisDrivenResearchRequestBody,
  HypothesisDrivenResearchService,
} from "@/lib/api";
import { Accordion } from "@/ui/components/Accordion";
import { Button } from "@/ui/components/Button";
import { LinkButton } from "@/ui/components/LinkButton";
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
  const [githubOwner, setGithubOwner] = useState("");
  const [repoName, setRepoName] = useState("");
  const [branch, setBranch] = useState("main");
  const [isPrivate, setIsPrivate] = useState(false);

  // Runner config
  const [runnerLabels, setRunnerLabels] = useState("ubuntu-latest");
  const [runnerDescription, setRunnerDescription] = useState("");

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

  const isFormValid = [
    openProblems,
    method,
    experimentalSetup,
    primaryMetric,
    experimentalCode,
    expectedResult,
    expectedConclusion,
    githubOwner,
    repoName,
    branch,
    runnerLabels,
    runnerDescription,
    wandbEntity,
    wandbProject,
  ].every((v) => v.trim().length > 0);

  const handleRun = useCallback(async () => {
    if (!isFormValid) return;
    setError(null);
    setIsRunning(true);

    const toNumber = (value: string): number | undefined => {
      if (value.trim() === "") return undefined;
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : undefined;
    };

    const payload = {
      github_config: {
        github_owner: githubOwner,
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
      runner_config: {
        runner_label: runnerLabels
          .split(",")
          .map((l) => l.trim())
          .filter((l) => l.length > 0),
        description: runnerDescription,
      },
      wandb_config: {
        entity: wandbEntity,
        project: wandbProject,
      },
      is_github_repo_private: isPrivate,
      github_actions_agent: githubActionsAgent || undefined,
      num_experiment_models: toNumber(numExperimentModels),
      num_experiment_datasets: toNumber(numExperimentDatasets),
      num_comparison_methods: toNumber(numComparativeMethods),
      paper_content_refinement_iterations: toNumber(paperContentRefinementIterations),
      latex_template_name: latexTemplateName.trim() || undefined,
      llm_mapping: llmMapping,
    };

    try {
      const response =
        await HypothesisDrivenResearchService.executeHypothesisDrivenResearchAirasV1HypothesisDrivenResearchRunPost(
          payload,
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
    githubOwner,
    repoName,
    branch,
    isPrivate,
    runnerLabels,
    runnerDescription,
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
    <div className="flex h-full w-full flex-col items-start bg-default-background">
      <div className="flex w-full items-center justify-between border-b border-solid border-neutral-border bg-default-background px-6 py-4 sticky top-0 z-10">
        <div className="flex items-center gap-4">
          <LinkButton variant="neutral" icon={<FeatherArrowLeft />} onClick={onBack}>
            {t("autonomous.hypothesisDriven.backToList")}
          </LinkButton>
          <div className="flex h-4 w-px flex-none flex-col items-center gap-2 bg-neutral-border" />
          <span className="text-heading-2 font-heading-2 text-default-font">
            Hypothesis-Driven Research
          </span>
        </div>
      </div>
      <div className="flex w-full grow shrink-0 basis-0 flex-col items-center px-6 py-6 overflow-auto">
        <div className="flex w-full max-w-[1024px] flex-col items-start gap-6 rounded-xl border border-solid border-neutral-border bg-neutral-800 px-6 py-6 shadow-sm">
          <span className="text-heading-2 font-heading-2 text-default-font">
            {t("autonomous.hypothesisDriven.newSessionTitle")}
          </span>
          <div className="flex h-px w-full flex-none flex-col items-center gap-2 bg-neutral-border" />

          <div className="flex w-full flex-col items-start gap-2">
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

          <div className="flex w-full flex-col items-start gap-4 rounded-lg bg-neutral-900 px-4 py-4">
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
            <div className="flex min-w-[320px] grow shrink-0 basis-0 flex-col items-start gap-4 rounded-lg bg-neutral-900 px-4 py-4">
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
                      {t("autonomous.hypothesisDriven.owner")}
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
                      placeholder="username"
                      value={githubOwner}
                      onChange={(e) => setGithubOwner(e.target.value)}
                    />
                  </TextField>
                </div>
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
              <div className="flex w-full flex-col items-start gap-4 rounded-lg bg-neutral-900 px-4 py-4">
                <div className="flex w-full items-center gap-2">
                  <FeatherPlay className="text-body font-body text-default-font" />
                  <span className="text-body-bold font-body-bold text-default-font">
                    GitHub Actions Runner
                  </span>
                </div>
                <div className="flex w-full flex-wrap items-start gap-3">
                  <div className="flex min-w-[144px] grow shrink-0 basis-0 flex-col items-start gap-1">
                    <div className="flex items-center gap-1">
                      <span className="text-caption font-caption text-default-font">
                        {t("autonomous.hypothesisDriven.runnerLabel")}
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
                        placeholder="ubuntu-latest, gpu-runner"
                        value={runnerLabels}
                        onChange={(e) => setRunnerLabels(e.target.value)}
                      />
                    </TextField>
                  </div>
                  <div className="flex min-w-[144px] grow shrink-0 basis-0 flex-col items-start gap-1">
                    <div className="flex items-center gap-1">
                      <span className="text-caption font-caption text-default-font">
                        {t("autonomous.hypothesisDriven.runnerDescription")}
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
                        placeholder="A100 x1, 40GB VRAM"
                        value={runnerDescription}
                        onChange={(e) => setRunnerDescription(e.target.value)}
                      />
                    </TextField>
                  </div>
                </div>
              </div>

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
              <div className="flex w-full items-center gap-2 rounded-lg bg-neutral-900 px-4 py-3">
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

          <div className="flex h-px w-full flex-none flex-col items-center gap-2 bg-neutral-border" />
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
