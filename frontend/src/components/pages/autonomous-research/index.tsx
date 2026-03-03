"use client";

import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, Plus } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";
import { AllLLMConfig } from "@/components/features/llm-config";
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
  Status,
  type TopicOpenEndedResearchLLMMapping,
  TopicOpenEndedResearchRequestBody,
  TopicOpenEndedResearchService,
  type TopicOpenEndedResearchStatusResponseBody,
} from "@/lib/api";
import type { ResearchSection } from "@/types/research";
import {
  AutoResearchResultDisplay,
  type AutoResearchResultSnapshot,
  mergeAutoResearchResultSnapshot,
} from "./autonomous-research-result";

const DEFAULT_RESEARCH_TITLE = "Untitled Research";
const AUTO_STATUS_POLL_INTERVAL_MS = 5000;

const RequiredMark = () => <span className="text-rose-400 ml-0.5">*</span>;

interface AutonomousResearchPageProps {
  section: ResearchSection | null;
  sessionsExpanded: boolean;
  onToggleSessions: () => void;
  onCreateSection: () => void;
  onUpdateSectionTitle: (title: string) => void;
  onRefreshSessions: (preferredId?: string) => Promise<void>;
}

export function AutonomousResearchPage({
  section,
  sessionsExpanded,
  onToggleSessions,
  onCreateSection,
  onUpdateSectionTitle,
  onRefreshSessions,
}: AutonomousResearchPageProps) {
  // topic_open_ended_research/run request params
  const [autoResearchTopic, setAutoResearchTopic] = useState(
    "Proposing an improved Chain-of-Thought based on human thinking methods, evaluated purely through prompt tuning without fine-tuning or time-intensive experiments",
  );
  const [autoGithubOwner, setAutoGithubOwner] = useState("auto-res2");
  const [autoRepoName, setAutoRepoName] = useState("");
  const [autoBranch, setAutoBranch] = useState("main");
  const [autoRunnerLabels, setAutoRunnerLabels] = useState("ubuntu-latest");
  const [autoRunnerDescription, setAutoRunnerDescription] = useState("CPU: 4 vCPU, RAM: 16 GB");
  const [autoWandbEntity, setAutoWandbEntity] = useState("airas");
  const [autoWandbProject, setAutoWandbProject] = useState("");
  const [autoIsPrivate, setAutoIsPrivate] = useState(false);

  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);

  const [autoNumPaperSearchQueries, setAutoNumPaperSearchQueries] = useState("2");
  const [autoPapersPerQuery, setAutoPapersPerQuery] = useState("2");
  const [autoHypothesisRefinementIterations, setAutoHypothesisRefinementIterations] = useState("1");
  const [autoNumExperimentModels, setAutoNumExperimentModels] = useState("1");
  const [autoNumExperimentDatasets, setAutoNumExperimentDatasets] = useState("1");
  const [autoNumComparativeMethods, setAutoNumComparativeMethods] = useState("1");
  const [autoExperimentCodeValidationIterations, setAutoExperimentCodeValidationIterations] =
    useState("4");
  const [autoPaperContentRefinementIterations, setAutoPaperContentRefinementIteration] =
    useState("2");
  const [autoGithubActionsAgent, setAutoGithubActionsAgent] = useState<
    TopicOpenEndedResearchRequestBody.github_actions_agent | ""
  >("");
  const [autoLatexTemplateName, setAutoLatexTemplateName] = useState("mdpi");
  // LLM設定
  const [llmMapping, setLlmMapping] = useState<TopicOpenEndedResearchLLMMapping | null>(null);
  const [autoStatus, setAutoStatus] = useState<TopicOpenEndedResearchStatusResponseBody | null>(
    null,
  );
  const [autoTaskId, setAutoTaskId] = useState<string | null>(null);
  const autoStatusPollingRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [isAutoPolling, setIsAutoPolling] = useState(false);
  const [isAutoRunning, setIsAutoRunning] = useState(false);
  const [autoError, setAutoError] = useState<string | null>(null);
  const [isEditingAutoTitle, setIsEditingAutoTitle] = useState(false);
  const [isUpdatingAutoTitle, setIsUpdatingAutoTitle] = useState(false);
  const [autoTitleDraft, setAutoTitleDraft] = useState(section?.title ?? DEFAULT_RESEARCH_TITLE);
  const [autoResultSnapshot, setAutoResultSnapshot] = useState<AutoResearchResultSnapshot>({});

  const isAutoFormValid = [
    autoResearchTopic,
    autoGithubOwner,
    autoRepoName,
    autoBranch,
    autoRunnerLabels,
    autoRunnerDescription,
    autoWandbEntity,
    autoWandbProject,
  ].every((value) => value.trim().length > 0);

  useEffect(() => {
    const nextTitle = section?.title ?? DEFAULT_RESEARCH_TITLE;
    setAutoTitleDraft(nextTitle);
  }, [section?.title]);

  useEffect(() => {
    if (!sessionsExpanded) return;
    void onRefreshSessions(section?.id);
  }, [onRefreshSessions, section?.id, sessionsExpanded]);

  useEffect(
    () => () => {
      if (autoStatusPollingRef.current) clearInterval(autoStatusPollingRef.current);
    },
    [],
  );

  const buildAutoResearchPayload = (): TopicOpenEndedResearchRequestBody => {
    const toNumber = (value: string): number | undefined => {
      if (value.trim() === "") return undefined;
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : undefined;
    };

    const payload: TopicOpenEndedResearchRequestBody = {
      github_config: {
        github_owner: autoGithubOwner,
        repository_name: autoRepoName,
        branch_name: autoBranch,
      },
      research_topic: autoResearchTopic,
      runner_config: {
        runner_label: autoRunnerLabels
          .split(",")
          .map((label) => label.trim())
          .filter((label) => label.length > 0),
        description: autoRunnerDescription,
      },
      wandb_config: {
        entity: autoWandbEntity,
        project: autoWandbProject,
      },
      is_github_repo_private: autoIsPrivate,
      num_paper_search_queries: toNumber(autoNumPaperSearchQueries),
      papers_per_query: toNumber(autoPapersPerQuery),
      hypothesis_refinement_iterations: toNumber(autoHypothesisRefinementIterations),
      num_experiment_models: toNumber(autoNumExperimentModels),
      num_experiment_datasets: toNumber(autoNumExperimentDatasets),
      num_comparison_methods: toNumber(autoNumComparativeMethods),
      paper_content_refinement_iterations: toNumber(autoPaperContentRefinementIterations),
      github_actions_agent: autoGithubActionsAgent || undefined,
      latex_template_name: autoLatexTemplateName.trim() || undefined,
      llm_mapping: llmMapping,
    };

    return payload;
  };

  useEffect(() => {
    if (!autoStatus) return;
    setAutoResultSnapshot((prev) =>
      mergeAutoResearchResultSnapshot(prev, autoStatus.result, autoStatus.github_url),
    );
  }, [autoStatus]);

  const clearAutoPollingTimer = useCallback(() => {
    if (!autoStatusPollingRef.current) return;
    clearInterval(autoStatusPollingRef.current);
    autoStatusPollingRef.current = null;
  }, []);

  const stopAutoPolling = useCallback(() => {
    clearAutoPollingTimer();
    setIsAutoPolling(false);
    setIsAutoRunning(false);
  }, [clearAutoPollingTimer]);

  useEffect(() => {
    if (!section?.id) {
      stopAutoPolling();
      setAutoTaskId(null);
      setAutoStatus(null);
      setAutoResultSnapshot({});
      setAutoError(null);
      return;
    }

    stopAutoPolling();
    setAutoTaskId(section.id);
    setAutoStatus(null);
    setAutoResultSnapshot({});
    setAutoError(null);
  }, [section?.id, stopAutoPolling]);

  const fetchAutoStatus = async (taskId: string, { resetError = false } = {}) => {
    if (resetError) setAutoError(null);
    try {
      const response =
        await TopicOpenEndedResearchService.getTopicOpenEndedResearchStatusAirasV1TopicOpenEndedResearchStatusTaskIdGet(
          taskId,
        );
      setAutoStatus(response);
      if (response.error) setAutoError(response.error);
      const finished = response.status === Status.COMPLETED || Boolean(response.error);
      if (finished) stopAutoPolling();
    } catch (error) {
      const message = error instanceof Error ? error.message : "ステータスの取得に失敗しました";
      setAutoError(message);
      stopAutoPolling();
    }
  };

  const startAutoPolling = (taskId: string) => {
    clearAutoPollingTimer();
    setIsAutoPolling(true);
    setIsAutoRunning(true);
    void fetchAutoStatus(taskId, { resetError: true });
    autoStatusPollingRef.current = setInterval(() => {
      void fetchAutoStatus(taskId);
    }, AUTO_STATUS_POLL_INTERVAL_MS);
  };

  const handleRunAutoResearch = async () => {
    if (!isAutoFormValid) return;
    const payload = buildAutoResearchPayload();
    setAutoError(null);

    setAutoStatus(null);
    setAutoResultSnapshot({});
    setIsAutoRunning(true);
    try {
      const response =
        await TopicOpenEndedResearchService.executeTopicOpenEndedResearchAirasV1TopicOpenEndedResearchRunPost(
          payload,
        );
      setAutoTaskId(response.task_id);
      startAutoPolling(response.task_id);
    } catch (error) {
      const message = error instanceof Error ? error.message : "自動研究の実行に失敗しました";
      setAutoError(message);
      stopAutoPolling();
    }
  };

  // 実行状態を確認するエンドポイントをたたく
  // 実行進捗の表示
  // 実行時間の表示
  // 実行結果の表示
  const handleGetAutoResearchStatus = async (taskId?: string) => {
    const id = taskId ?? autoTaskId;
    if (!id) return;
    clearAutoPollingTimer();
    setIsAutoPolling(false);
    await fetchAutoStatus(id, { resetError: true });
  };

  const handleSaveAutoTitle = async () => {
    const targetId = section?.id ?? autoTaskId;
    if (!targetId) {
      setAutoError("セッションを選択してください");
      return;
    }

    setIsUpdatingAutoTitle(true);
    setAutoError(null);
    try {
      const updated =
        await TopicOpenEndedResearchService.updateTopicOpenEndedResearchAirasV1TopicOpenEndedResearchTaskIdPatch(
          targetId,
          {
            title: autoTitleDraft,
          },
        );
      setAutoTitleDraft(updated.title);
      onUpdateSectionTitle(updated.title);
      setIsEditingAutoTitle(false);
      await onRefreshSessions(updated.id);
    } catch (error) {
      const message = error instanceof Error ? error.message : "タイトルの更新に失敗しました";
      setAutoError(message);
    } finally {
      setIsUpdatingAutoTitle(false);
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
          <h2 className="text-lg font-semibold text-foreground">Autonomous Research</h2>
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
                {isEditingAutoTitle ? (
                  <Input
                    id="auto-section-title"
                    value={autoTitleDraft}
                    onChange={(e) => setAutoTitleDraft(e.target.value)}
                    className="bg-muted/40 border-border/70 text-lg"
                    placeholder=""
                  />
                ) : (
                  <p className="text-xl font-semibold leading-tight text-foreground">
                    {section?.title ?? autoTitleDraft ?? DEFAULT_RESEARCH_TITLE}
                  </p>
                )}
                <Button
                  variant="outline"
                  size="sm"
                  disabled={isUpdatingAutoTitle}
                  onClick={
                    isEditingAutoTitle ? handleSaveAutoTitle : () => setIsEditingAutoTitle(true)
                  }
                >
                  {isEditingAutoTitle ? (isUpdatingAutoTitle ? "saving..." : "save") : "edit"}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="auto-queries">
                  研究テーマ
                  <RequiredMark />
                </Label>
                <Textarea
                  id="auto-queries"
                  value={autoResearchTopic}
                  onChange={(e) => setAutoResearchTopic(e.target.value)}
                  placeholder="ex) vision-language models for video QA"
                />
              </div>

              <hr className="border-border" />

              <div className="space-y-3 rounded-md bg-muted/40 p-4">
                <p className="text-sm font-semibold text-foreground">GitHub</p>
                <div className="grid gap-4 md:grid-cols-3">
                  <div className="space-y-2">
                    <Label htmlFor="auto-github-owner">
                      owner
                      <RequiredMark />
                    </Label>
                    <Input
                      id="auto-github-owner"
                      value={autoGithubOwner}
                      onChange={(e) => setAutoGithubOwner(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="auto-repo-name">
                      repository
                      <RequiredMark />
                    </Label>
                    <Input
                      id="auto-repo-name"
                      value={autoRepoName}
                      onChange={(e) => setAutoRepoName(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="auto-branch">
                      branch
                      <RequiredMark />
                    </Label>
                    <Input
                      id="auto-branch"
                      value={autoBranch}
                      onChange={(e) => setAutoBranch(e.target.value)}
                    />
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Checkbox
                    id="auto-private"
                    checked={autoIsPrivate}
                    onCheckedChange={(val) => setAutoIsPrivate(Boolean(val))}
                  />
                  <Label htmlFor="auto-private" className="text-sm text-muted-foreground">
                    リポジトリをprivateにする
                  </Label>
                </div>
              </div>

              <hr className="border-border" />

              <div className="space-y-3 rounded-md bg-muted/40 p-4">
                <p className="text-sm font-semibold text-foreground">GitHub Actions Runners</p>
                <div className="grid gap-4 md:grid-cols-2">
                  <div className="space-y-2">
                    <Label htmlFor="auto-runner-labels">
                      ラベル
                      <RequiredMark />
                    </Label>
                    <Input
                      id="auto-runner-labels"
                      value={autoRunnerLabels}
                      onChange={(e) => setAutoRunnerLabels(e.target.value)}
                      placeholder="ubuntu-latest,gpu-runner"
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="auto-runner-desc">
                      説明
                      <RequiredMark />
                    </Label>
                    <Textarea
                      id="auto-runner-desc"
                      value={autoRunnerDescription}
                      onChange={(e) => setAutoRunnerDescription(e.target.value)}
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
                    <Label htmlFor="auto-wandb-entity">
                      entity
                      <RequiredMark />
                    </Label>
                    <Input
                      id="auto-wandb-entity"
                      value={autoWandbEntity}
                      onChange={(e) => setAutoWandbEntity(e.target.value)}
                    />
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="auto-wandb-project">
                      project
                      <RequiredMark />
                    </Label>
                    <Input
                      id="auto-wandb-project"
                      value={autoWandbProject}
                      onChange={(e) => setAutoWandbProject(e.target.value)}
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
                        <Label htmlFor="auto-num-paper-search-queries">
                          論文取得にための検索クエリの数
                        </Label>
                        <Input
                          id="auto-num-paper-search-queries"
                          type="number"
                          inputMode="numeric"
                          value={autoNumPaperSearchQueries}
                          onChange={(e) => setAutoNumPaperSearchQueries(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="auto-max-results">1クエリあたりの取得論文数</Label>
                        <Input
                          id="auto-max-results"
                          type="number"
                          inputMode="numeric"
                          value={autoPapersPerQuery}
                          onChange={(e) => setAutoPapersPerQuery(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="auto-refinement-rounds">
                          生成する仮説のリファインメント回数
                        </Label>
                        <Input
                          id="auto-refinement-rounds"
                          type="number"
                          inputMode="numeric"
                          value={autoHypothesisRefinementIterations}
                          onChange={(e) => setAutoHypothesisRefinementIterations(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="auto-num-models">実験に用いるモデルの数</Label>
                        <Input
                          id="auto-num-models"
                          type="number"
                          inputMode="numeric"
                          value={autoNumExperimentModels}
                          onChange={(e) => setAutoNumExperimentModels(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="auto-num-datasets">実験に用いるデータセットの数</Label>
                        <Input
                          id="auto-num-datasets"
                          type="number"
                          inputMode="numeric"
                          value={autoNumExperimentDatasets}
                          onChange={(e) => setAutoNumExperimentDatasets(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="auto-num-comparative-methods">
                          比較手法の数(ベースラインの数)
                        </Label>
                        <Input
                          id="auto-num-comparative-methods"
                          type="number"
                          inputMode="numeric"
                          value={autoNumComparativeMethods}
                          onChange={(e) => setAutoNumComparativeMethods(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="auto-max-code-validations">
                          実装したコードのバリデーション回数
                        </Label>
                        <Input
                          id="auto-max-code-validations"
                          type="number"
                          inputMode="numeric"
                          value={autoExperimentCodeValidationIterations}
                          onChange={(e) =>
                            setAutoExperimentCodeValidationIterations(e.target.value)
                          }
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="auto-writing-refinement-rounds">
                          執筆した論文のリファインメント回数
                        </Label>
                        <Input
                          id="auto-writing-refinement-rounds"
                          type="number"
                          inputMode="numeric"
                          value={autoPaperContentRefinementIterations}
                          onChange={(e) => setAutoPaperContentRefinementIteration(e.target.value)}
                        />
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="auto-github-actions-agent">
                          GitHub Actionsエージェント
                        </Label>
                        <Select
                          value={autoGithubActionsAgent}
                          onValueChange={(val) =>
                            setAutoGithubActionsAgent(
                              val as TopicOpenEndedResearchRequestBody.github_actions_agent | "",
                            )
                          }
                        >
                          <SelectTrigger className="w-full">
                            <SelectValue placeholder="デフォルト" />
                          </SelectTrigger>
                          <SelectContent>
                            <SelectItem
                              value={
                                TopicOpenEndedResearchRequestBody.github_actions_agent.CLAUDE_CODE
                              }
                            >
                              Claude Code
                            </SelectItem>
                            <SelectItem
                              value={
                                TopicOpenEndedResearchRequestBody.github_actions_agent.OPEN_CODE
                              }
                            >
                              Open Code
                            </SelectItem>
                          </SelectContent>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <Label htmlFor="auto-latex-template-name">
                          利用するLatexのテンプレート
                        </Label>
                        <Select
                          value={autoLatexTemplateName}
                          onValueChange={setAutoLatexTemplateName}
                        >
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

              <AllLLMConfig llmMapping={llmMapping} onChange={setLlmMapping} />

              <hr className="border-border" />

              <div className="flex flex-wrap gap-3">
                <Button
                  onClick={handleRunAutoResearch}
                  disabled={isAutoRunning || !isAutoFormValid}
                >
                  {isAutoRunning ? "実行中..." : "自動研究を実行"}
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>自動研究の結果</CardTitle>
              <CardDescription>最新のステータスを表示します。</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap gap-3 items-center">
                <Button
                  variant="outline"
                  onClick={() => handleGetAutoResearchStatus()}
                  disabled={isAutoPolling || !autoTaskId}
                >
                  最新を取得
                </Button>
                {isAutoPolling && <p className="text-sm text-muted-foreground">自動更新中...</p>}

                {!autoTaskId && (
                  <p className="text-sm text-muted-foreground">
                    先に自動研究を実行してタスクIDを取得してください。
                  </p>
                )}
              </div>
              {autoError && <p className="text-sm text-destructive">{autoError}</p>}
              {autoStatus ? (
                <>
                  <div className="grid gap-2 md:grid-cols-2">
                    <div>
                      <p className="text-sm text-muted-foreground">タスクID</p>
                      <p className="text-sm font-medium break-all">{autoStatus.id}</p>
                    </div>
                    <div>
                      <p className="text-sm text-muted-foreground">ステータス</p>
                      <p className="text-sm font-medium">{autoStatus.status}</p>
                    </div>
                  </div>
                  {autoStatus.error && (
                    <p className="text-sm text-destructive">{autoStatus.error}</p>
                  )}
                  {autoStatus.research_history && (
                    <div className="rounded-md border border-border bg-card/60 p-3">
                      <p className="text-sm font-semibold">研究履歴</p>
                      <p className="text-sm text-muted-foreground">
                        目的: {autoStatus.research_history.research_topic ?? "N/A"}
                      </p>
                      {autoStatus.research_history.paper_url && (
                        <p className="text-sm text-muted-foreground">
                          論文URL: {autoStatus.research_history.paper_url}
                        </p>
                      )}
                    </div>
                  )}
                  <AutoResearchResultDisplay snapshot={autoResultSnapshot} />
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
