"use client";

import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, Plus } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { HypothesisAllLLMConfig } from "@/components/features/llm-config";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import {
  type HypothesisDrivenResearchLLMMapping,
  HypothesisDrivenResearchRequestBody,
  HypothesisDrivenResearchService,
  type HypothesisDrivenResearchStatusResponseBody,
  Status,
} from "@/lib/api";
import type { ResearchSection } from "@/types/research";
import {
  AutoResearchResultDisplay,
  type AutoResearchResultSnapshot,
  mergeAutoResearchResultSnapshot,
} from "../autonomous-research/autonomous-research-result";

const DEFAULT_RESEARCH_TITLE = "Untitled Research";
const AUTO_STATUS_POLL_INTERVAL_MS = 5000;

const RequiredMark = () => <span className="text-rose-400 ml-0.5">*</span>;

interface HypothesisDrivenResearchPageProps {
  section: ResearchSection | null;
  sessionsExpanded: boolean;
  onToggleSessions: () => void;
  onCreateSection: () => void;
  onUpdateSectionTitle: (title: string) => void;
  onRefreshSessions: (preferredId?: string) => Promise<void>;
}

export function HypothesisDrivenResearchPage({
  section,
  sessionsExpanded,
  onToggleSessions,
  onCreateSection,
  onUpdateSectionTitle,
  onRefreshSessions,
}: HypothesisDrivenResearchPageProps) {
  // ResearchHypothesis fields (all required)
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

  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);

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

  // Status and polling
  const [status, setStatus] = useState<HypothesisDrivenResearchStatusResponseBody | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Title editing
  const [isEditingTitle, setIsEditingTitle] = useState(false);
  const [isUpdatingTitle, setIsUpdatingTitle] = useState(false);
  const [titleDraft, setTitleDraft] = useState(section?.title ?? DEFAULT_RESEARCH_TITLE);

  const [resultSnapshot, setResultSnapshot] = useState<AutoResearchResultSnapshot>({});

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

  useEffect(() => {
    const nextTitle = section?.title ?? DEFAULT_RESEARCH_TITLE;
    setTitleDraft(nextTitle);
  }, [section?.title]);

  useEffect(() => {
    if (!sessionsExpanded) return;
    void onRefreshSessions(section?.id);
  }, [onRefreshSessions, section?.id, sessionsExpanded]);

  useEffect(
    () => () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    },
    [],
  );

  useEffect(() => {
    if (!status) return;
    setResultSnapshot((prev) =>
      mergeAutoResearchResultSnapshot(prev, status.result, status.github_url),
    );
  }, [status]);

  const clearPollingTimer = useCallback(() => {
    if (!pollingRef.current) return;
    clearInterval(pollingRef.current);
    pollingRef.current = null;
  }, []);

  const stopPolling = useCallback(() => {
    clearPollingTimer();
    setIsPolling(false);
    setIsRunning(false);
  }, [clearPollingTimer]);

  useEffect(() => {
    if (!section?.id) {
      stopPolling();
      setTaskId(null);
      setStatus(null);
      setResultSnapshot({});
      setError(null);
      return;
    }

    stopPolling();
    setTaskId(section.id);
    setStatus(null);
    setResultSnapshot({});
    setError(null);
  }, [section?.id, stopPolling]);

  const fetchStatus = async (id: string, { resetError = false } = {}) => {
    if (resetError) setError(null);
    try {
      const response =
        await HypothesisDrivenResearchService.getHypothesisDrivenResearchStatusAirasV1HypothesisDrivenResearchStatusTaskIdGet(
          id,
        );
      setStatus(response);
      if (response.error) setError(response.error);
      const finished =
        response.status === Status.COMPLETED ||
        response.status === Status.FAILED ||
        Boolean(response.error);
      if (finished) stopPolling();
    } catch (err) {
      const message = err instanceof Error ? err.message : "ステータスの取得に失敗しました";
      setError(message);
      stopPolling();
    }
  };

  const startPolling = (id: string) => {
    clearPollingTimer();
    setIsPolling(true);
    setIsRunning(true);
    void fetchStatus(id, { resetError: true });
    pollingRef.current = setInterval(() => {
      void fetchStatus(id);
    }, AUTO_STATUS_POLL_INTERVAL_MS);
  };

  const buildPayload = () => {
    const toNumber = (value: string): number | undefined => {
      if (value.trim() === "") return undefined;
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : undefined;
    };

    return {
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
  };

  const handleRun = async () => {
    if (!isFormValid) return;
    const payload = buildPayload();
    setError(null);
    setStatus(null);
    setResultSnapshot({});
    setIsRunning(true);
    try {
      const response =
        await HypothesisDrivenResearchService.executeHypothesisDrivenResearchAirasV1HypothesisDrivenResearchRunPost(
          payload,
        );
      setTaskId(response.task_id);
      startPolling(response.task_id);
    } catch (err) {
      const message = err instanceof Error ? err.message : "研究の実行に失敗しました";
      setError(message);
      stopPolling();
    }
  };

  const handleGetStatus = async (id?: string) => {
    const targetId = id ?? taskId;
    if (!targetId) return;
    clearPollingTimer();
    setIsPolling(false);
    await fetchStatus(targetId, { resetError: true });
  };

  const handleSaveTitle = async () => {
    const targetId = section?.id ?? taskId;
    if (!targetId) {
      setError("セッションを選択してください");
      return;
    }

    setIsUpdatingTitle(true);
    setError(null);
    try {
      const updated =
        await HypothesisDrivenResearchService.updateHypothesisDrivenResearchAirasV1HypothesisDrivenResearchTaskIdPatch(
          targetId,
          { title: titleDraft },
        );
      setTitleDraft(updated.title);
      onUpdateSectionTitle(updated.title);
      setIsEditingTitle(false);
      await onRefreshSessions(updated.id);
    } catch (err) {
      const message = err instanceof Error ? err.message : "タイトルの更新に失敗しました";
      setError(message);
    } finally {
      setIsUpdatingTitle(false);
    }
  };

  return (
    <div className="flex-1 bg-background overflow-y-auto">
      <div className="sticky top-0 z-10 border-b border-border bg-card px-6 py-4 flex items-center justify-between relative">
        <button
          type="button"
          className="absolute left-2 top-1/2 -translate-y-1/2 inline-flex h-7 w-7 items-center justify-center rounded-full border border-border bg-card text-muted-foreground hover:text-foreground shadow-sm"
          onClick={onToggleSessions}
          aria-label="Toggle sessions"
        >
          {sessionsExpanded ? (
            <ChevronLeft className="h-4 w-4" />
          ) : (
            <ChevronRight className="h-4 w-4" />
          )}
        </button>
        <div className="space-y-2 pl-9">
          <h2 className="text-lg font-semibold text-foreground">Hypothesis-Driven Research</h2>
        </div>
        <Button onClick={onCreateSection}>
          <Plus className="h-4 w-4 mr-2" />
          New Session
        </Button>
      </div>

      <div className="p-6">
        <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-[1fr_2fr] items-start">
          <Card>
            <CardHeader className="space-y-4">
              <div className="flex items-center justify-between gap-3">
                {isEditingTitle ? (
                  <Input
                    id="hypothesis-section-title"
                    value={titleDraft}
                    onChange={(e) => setTitleDraft(e.target.value)}
                    className="bg-muted/40 border-border/70 text-lg"
                    placeholder="Enter research title"
                  />
                ) : (
                  <p className="text-xl font-semibold leading-tight text-foreground">
                    {section?.title ?? titleDraft ?? DEFAULT_RESEARCH_TITLE}
                  </p>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  disabled={isUpdatingTitle}
                  onClick={isEditingTitle ? handleSaveTitle : () => setIsEditingTitle(true)}
                >
                  {isEditingTitle ? (isUpdatingTitle ? "saving..." : "save") : "edit"}
                </Button>
              </div>
            </CardHeader>

            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="hypothesis-research-topic">研究テーマ（任意）</Label>
                <Input
                  id="hypothesis-research-topic"
                  value={researchTopic}
                  onChange={(e) => setResearchTopic(e.target.value)}
                  placeholder="ex) vision-language models for video QA"
                />
              </div>

              <div className="space-y-6 rounded-md bg-muted/40 p-4">
                <p className="text-sm font-semibold text-foreground">研究仮説</p>

                <div className="space-y-2">
                  <Label htmlFor="hypothesis-open-problems">
                    解決すべき問題
                    <RequiredMark />
                  </Label>
                  <Textarea
                    id="hypothesis-open-problems"
                    className="min-h-28"
                    value={openProblems}
                    onChange={(e) => setOpenProblems(e.target.value)}
                    placeholder="ex) Existing models struggle with temporal reasoning in long videos"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="hypothesis-method">
                    提案手法
                    <RequiredMark />
                  </Label>
                  <Textarea
                    id="hypothesis-method"
                    className="min-h-28"
                    value={method}
                    onChange={(e) => setMethod(e.target.value)}
                    placeholder="ex) A hierarchical attention mechanism that models temporal dependencies"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="hypothesis-experimental-setup">
                    実験設定
                    <RequiredMark />
                  </Label>
                  <Textarea
                    id="hypothesis-experimental-setup"
                    className="min-h-24"
                    value={experimentalSetup}
                    onChange={(e) => setExperimentalSetup(e.target.value)}
                    placeholder="ex) Evaluate on ActivityNet-QA and EgoSchema benchmarks"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="hypothesis-primary-metric">
                    主要評価指標
                    <RequiredMark />
                  </Label>
                  <Input
                    id="hypothesis-primary-metric"
                    value={primaryMetric}
                    onChange={(e) => setPrimaryMetric(e.target.value)}
                    placeholder="ex) Accuracy on ActivityNet-QA"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="hypothesis-experimental-code">
                    実験コード
                    <RequiredMark />
                  </Label>
                  <Textarea
                    id="hypothesis-experimental-code"
                    className="min-h-28"
                    value={experimentalCode}
                    onChange={(e) => setExperimentalCode(e.target.value)}
                    placeholder="ex) PyTorch implementation using transformers library"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="hypothesis-expected-result">
                    期待される結果
                    <RequiredMark />
                  </Label>
                  <Textarea
                    id="hypothesis-expected-result"
                    className="min-h-24"
                    value={expectedResult}
                    onChange={(e) => setExpectedResult(e.target.value)}
                    placeholder="ex) 5% accuracy improvement over baseline on ActivityNet-QA"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="hypothesis-expected-conclusion">
                    期待される結論
                    <RequiredMark />
                  </Label>
                  <Textarea
                    id="hypothesis-expected-conclusion"
                    className="min-h-24"
                    value={expectedConclusion}
                    onChange={(e) => setExpectedConclusion(e.target.value)}
                    placeholder="ex) Hierarchical temporal attention significantly improves video QA"
                  />
                </div>
              </div>

              <hr className="border-border" />

              <div className="space-y-3 rounded-md bg-muted/40 p-4">
                <p className="text-sm font-semibold text-foreground">GitHub</p>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="hypothesis-github-owner">
                      owner
                      <RequiredMark />
                    </Label>
                    <Input
                      id="hypothesis-github-owner"
                      value={githubOwner}
                      onChange={(e) => setGithubOwner(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="hypothesis-repo-name">
                      repository
                      <RequiredMark />
                    </Label>
                    <Input
                      id="hypothesis-repo-name"
                      value={repoName}
                      onChange={(e) => setRepoName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="hypothesis-branch">
                      branch
                      <RequiredMark />
                    </Label>
                    <Input
                      id="hypothesis-branch"
                      value={branch}
                      onChange={(e) => setBranch(e.target.value)}
                    />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Checkbox
                    id="hypothesis-private"
                    checked={isPrivate}
                    onCheckedChange={(val) => setIsPrivate(Boolean(val))}
                  />
                  <Label htmlFor="hypothesis-private" className="text-sm text-muted-foreground">
                    リポジトリをprivateにする
                  </Label>
                </div>
              </div>

              <hr className="border-border" />

              <div className="space-y-3 rounded-md bg-muted/40 p-4">
                <p className="text-sm font-semibold text-foreground">GitHub Actions Runners</p>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="hypothesis-runner-labels">
                      ラベル
                      <RequiredMark />
                    </Label>
                    <Input
                      id="hypothesis-runner-labels"
                      value={runnerLabels}
                      onChange={(e) => setRunnerLabels(e.target.value)}
                      placeholder="ubuntu-latest,gpu-runner"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="hypothesis-runner-desc">
                      説明
                      <RequiredMark />
                    </Label>
                    <Textarea
                      id="hypothesis-runner-desc"
                      value={runnerDescription}
                      onChange={(e) => setRunnerDescription(e.target.value)}
                      placeholder="A100 x1, 40GB / 8 vCPU / 32GB RAM"
                    />
                  </div>
                </div>
              </div>

              <hr className="border-border" />

              <div className="space-y-3 rounded-md bg-muted/40 p-4">
                <p className="text-sm font-semibold text-foreground">Weights &amp; Biases</p>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="hypothesis-wandb-entity">
                      entity
                      <RequiredMark />
                    </Label>
                    <Input
                      id="hypothesis-wandb-entity"
                      value={wandbEntity}
                      onChange={(e) => setWandbEntity(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="hypothesis-wandb-project">
                      project
                      <RequiredMark />
                    </Label>
                    <Input
                      id="hypothesis-wandb-project"
                      value={wandbProject}
                      onChange={(e) => setWandbProject(e.target.value)}
                    />
                  </div>
                </div>
              </div>

              <hr className="border-border" />

              <div className="rounded-md bg-muted/40">
                <button
                  type="button"
                  className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-foreground cursor-pointer"
                  onClick={() => setShowAdvancedSettings((prev) => !prev)}
                  aria-expanded={showAdvancedSettings}
                >
                  <span>詳細設定</span>
                  {showAdvancedSettings ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <ChevronDown className="h-4 w-4" />
                  )}
                </button>
                {showAdvancedSettings && (
                  <div className="p-6 space-y-6">
                    <div className="grid gap-6 md:grid-cols-2">
                      <div className="space-y-2">
                        <Label htmlFor="hypothesis-github-actions-agent">
                          GitHub Actionsエージェント
                        </Label>
                        <Select
                          value={githubActionsAgent}
                          onValueChange={(val) =>
                            setGithubActionsAgent(
                              val as HypothesisDrivenResearchRequestBody.github_actions_agent | "",
                            )
                          }
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="デフォルト" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem
                              value={
                                HypothesisDrivenResearchRequestBody.github_actions_agent.CLAUDE_CODE
                              }
                            >
                              Claude Code
                            </SelectItem>
                            <SelectItem
                              value={
                                HypothesisDrivenResearchRequestBody.github_actions_agent.OPEN_CODE
                              }
                            >
                              Open Code
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="hypothesis-num-models">実験に用いるモデルの数</Label>
                        <Input
                          id="hypothesis-num-models"
                          type="number"
                          inputMode="numeric"
                          value={numExperimentModels}
                          onChange={(e) => setNumExperimentModels(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="hypothesis-num-datasets">
                          実験に用いるデータセットの数
                        </Label>
                        <Input
                          id="hypothesis-num-datasets"
                          type="number"
                          inputMode="numeric"
                          value={numExperimentDatasets}
                          onChange={(e) => setNumExperimentDatasets(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="hypothesis-num-comparative-methods">
                          比較手法の数(ベースラインの数)
                        </Label>
                        <Input
                          id="hypothesis-num-comparative-methods"
                          type="number"
                          inputMode="numeric"
                          value={numComparativeMethods}
                          onChange={(e) => setNumComparativeMethods(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="hypothesis-writing-refinement-rounds">
                          執筆した論文のリファインメント回数
                        </Label>
                        <Input
                          id="hypothesis-writing-refinement-rounds"
                          type="number"
                          inputMode="numeric"
                          value={paperContentRefinementIterations}
                          onChange={(e) => setPaperContentRefinementIterations(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="hypothesis-latex-template-name">
                          利用するLatexのテンプレート
                        </Label>
                        <Select value={latexTemplateName} onValueChange={setLatexTemplateName}>
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="mdpi" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem value="mdpi">mdpi</SelectItem>
                            <SelectItem value="iclr2024">iclr2024</SelectItem>
                            <SelectItem value="agents4science_2025">agents4science_2025</SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                    </div>
                  </div>
                )}
              </div>

              <hr className="border-border" />

              <HypothesisAllLLMConfig llmMapping={llmMapping} onChange={setLlmMapping} />

              <hr className="border-border" />

              <div className="flex flex-wrap gap-3">
                <Button onClick={handleRun} disabled={isRunning || !isFormValid}>
                  {isRunning ? "実行中..." : "仮説駆動研究を実行"}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>仮説駆動研究の結果</CardTitle>
              <CardDescription>最新のステータスを表示します。</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-3 items-center">
                <Button
                  variant="outline"
                  onClick={() => handleGetStatus()}
                  disabled={isPolling || !taskId}
                >
                  最新を取得
                </Button>
                {isPolling && <p className="text-sm text-muted-foreground">自動更新中...</p>}
                {!taskId && (
                  <p className="text-sm text-muted-foreground">
                    先に研究を実行してタスクIDを取得してください。
                  </p>
                )}
              </div>
              {error && <p className="text-sm text-destructive">{error}</p>}
              {status ? (
                <>
                  <div className="grid gap-2 md:grid-cols-2">
                    <div>
                      <p className="text-sm text-muted-foreground">タスクID</p>
                      <p className="text-sm font-medium break-all">{status.id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">ステータス</p>
                      <p className="text-sm font-medium">{status.status}</p>
                    </div>
                  </div>
                  {status.error && <p className="text-sm text-destructive">{status.error}</p>}
                  {status.research_history && (
                    <div className="rounded-md border border-border bg-card/60 p-3">
                      <p className="text-sm font-semibold">研究履歴</p>
                      <p className="text-sm text-muted-foreground">
                        目的: {status.research_history.research_topic ?? "N/A"}
                      </p>
                      {status.research_history.paper_url && (
                        <p className="text-sm text-muted-foreground">
                          論文URL: {status.research_history.paper_url}
                        </p>
                      )}
                    </div>
                  )}
                  <AutoResearchResultDisplay snapshot={resultSnapshot} />
                </>
              ) : (
                <p className="text-sm text-muted-foreground">まだ実行結果がありません</p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}
