"use client";

import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, Plus } from "lucide-react";
import { useEffect, useState } from "react";
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
  type TopicOpenEndedResearchRequestBody,
  TopicOpenEndedResearchService,
  type TopicOpenEndedResearchStatusResponseBody,
} from "@/lib/api";
import type { ResearchSection } from "@/types/research";

const DEFAULT_RESEARCH_TITLE = "Untitled Research";

type AutoResearchSave = {
  id: string;
  savedAt: Date;
  payload: TopicOpenEndedResearchRequestBody;
  queryList: string[];
  response: TopicOpenEndedResearchStatusResponseBody | null;
};

interface AutonomousResearchPageProps {
  section: ResearchSection | null;
  sessionsExpanded: boolean;
  onToggleSessions: () => void;
  onCreateSection: () => void;
  onUpdateSectionTitle: (title: string) => void;
}

export function AutonomousResearchPage({
  section,
  sessionsExpanded,
  onToggleSessions,
  onCreateSection,
  onUpdateSectionTitle,
}: AutonomousResearchPageProps) {
  const [autoResearchSaves, setAutoResearchSaves] = useState<AutoResearchSave[]>([]);
  const [autoQueries, setAutoQueries] = useState("");
  const [autoGithubOwner, setAutoGithubOwner] = useState("");
  const [autoRepoName, setAutoRepoName] = useState("");
  const [autoBranch, setAutoBranch] = useState("main");
  const [autoRunnerLabels, setAutoRunnerLabels] = useState("ubuntu-latest");
  const [autoRunnerDescription, setAutoRunnerDescription] = useState("");
  const [autoWandbEntity, setAutoWandbEntity] = useState("");
  const [autoWandbProject, setAutoWandbProject] = useState("");
  const [autoIsPrivate, setAutoIsPrivate] = useState(false);
  const [showAdvancedSettings, setShowAdvancedSettings] = useState(false);
  const [autoMaxResultsPerQuery, setAutoMaxResultsPerQuery] = useState("5");
  const [autoRefinementRounds, setAutoRefinementRounds] = useState("1");
  const [autoNumModelsToUse, setAutoNumModelsToUse] = useState("1");
  const [autoNumDatasetsToUse, setAutoNumDatasetsToUse] = useState("1");
  const [autoNumComparativeMethods, setAutoNumComparativeMethods] = useState("1");
  const [autoMaxCodeValidations, setAutoMaxCodeValidations] = useState("10");
  const [autoWritingRefinementRounds, setAutoWritingRefinementRounds] = useState("2");
  const [autoLatexTemplateName, setAutoLatexTemplateName] = useState("iclr2024");
  const [autoStatus, setAutoStatus] = useState<TopicOpenEndedResearchStatusResponseBody | null>(
    null,
  );
  const [autoTaskId, setAutoTaskId] = useState<string | null>(null);
  const [isAutoRunning, setIsAutoRunning] = useState(false);
  const [autoError, setAutoError] = useState<string | null>(null);
  const [isEditingAutoTitle, setIsEditingAutoTitle] = useState(false);
  const [autoTitleDraft, setAutoTitleDraft] = useState(section?.title ?? DEFAULT_RESEARCH_TITLE);

  useEffect(() => {
    const nextTitle = section?.title ?? DEFAULT_RESEARCH_TITLE;
    setAutoTitleDraft(nextTitle);
  }, [section?.title]);

  const buildAutoResearchPayload = (): {
    payload: TopicOpenEndedResearchRequestBody;
    queryList: string[];
  } => {
    const queryList = autoQueries
      .split("\n")
      .map((q) => q.trim())
      .filter((q) => q.length > 0);

    const researchTopic = queryList[0] ?? "";

    const toNumber = (value: string): number | undefined => {
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : undefined;
    };

    const payload: TopicOpenEndedResearchRequestBody = {
      github_config: {
        github_owner: autoGithubOwner,
        repository_name: autoRepoName,
        branch_name: autoBranch,
      },
      research_topic: researchTopic,
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
      num_paper_search_queries: queryList.length || undefined,
      papers_per_query: toNumber(autoMaxResultsPerQuery),
      hypothesis_refinement_iterations: toNumber(autoRefinementRounds),
      num_experiment_models: toNumber(autoNumModelsToUse),
      num_experiment_datasets: toNumber(autoNumDatasetsToUse),
      num_comparison_methods: toNumber(autoNumComparativeMethods),
      experiment_code_validation_iterations: toNumber(autoMaxCodeValidations),
      paper_content_refinement_iterations: toNumber(autoWritingRefinementRounds),
      latex_template_name: autoLatexTemplateName.trim() || undefined,
    };

    return { payload, queryList };
  };

  const handleSaveAutoResearch = () => {
    const { payload, queryList } = buildAutoResearchPayload();
    const id = `auto-research-save-${Date.now()}`;
    setAutoResearchSaves((prev) => [
      { id, savedAt: new Date(), payload, queryList, response: autoStatus },
      ...prev,
    ]);
  };

  const handleRunAutoResearch = async () => {
    setIsAutoRunning(true);
    setAutoError(null);
    try {
      const { payload, queryList } = buildAutoResearchPayload();
      if (queryList.length === 0) {
        throw new Error("研究トピック/クエリを1つ以上入力してください");
      }
      if (!payload.github_config.github_owner || !payload.github_config.repository_name) {
        throw new Error("GitHubのオーナーとリポジトリ名を入力してください");
      }
      if (!payload.runner_config.description) {
        throw new Error("Runnerの説明を入力してください");
      }
      if (!payload.wandb_config.entity || !payload.wandb_config.project) {
        throw new Error("WandBのEntity/Projectを入力してください");
      }

      const response =
        await TopicOpenEndedResearchService.executeTopicOpenEndedResearchAirasV1TopicOpenEndedResearchRunPost(
          payload,
        );
      setAutoTaskId(response.task_id);
      await handleRefreshAutoStatus(response.task_id);
    } catch (error) {
      const message = error instanceof Error ? error.message : "自動研究の実行に失敗しました";
      setAutoError(message);
    } finally {
      setIsAutoRunning(false);
    }
  };

  const handleRefreshAutoStatus = async (taskId?: string) => {
    const id = taskId ?? autoTaskId;
    if (!id) return;
    setIsAutoRunning(true);
    setAutoError(null);
    try {
      const response =
        await TopicOpenEndedResearchService.getTopicOpenEndedResearchStatusAirasV1TopicOpenEndedResearchStatusTaskIdGet(
          id,
        );
      setAutoStatus(response);
    } catch (error) {
      const message = error instanceof Error ? error.message : "ステータスの取得に失敗しました";
      setAutoError(message);
    } finally {
      setIsAutoRunning(false);
    }
  };

  const handleSaveAutoTitle = () => {
    onUpdateSectionTitle(autoTitleDraft);
    setIsEditingAutoTitle(false);
  };

  const renderAutoHistory = () => {
    if (autoResearchSaves.length === 0) {
      return <p className="text-sm text-muted-foreground">まだ保存がありません</p>;
    }
    return (
      <div className="space-y-2 max-h-48 overflow-auto">
        {autoResearchSaves.map((save) => (
          <div key={save.id} className="rounded-md border border-border bg-card/50 px-3 py-2">
            <p className="text-sm font-medium">保存 {save.savedAt.toLocaleString()}</p>
            <p className="text-xs text-muted-foreground">
              クエリ {save.queryList.length} 件 / リポジトリ{" "}
              {save.payload.github_config.github_owner}/{save.payload.github_config.repository_name}
            </p>
            {save.response?.task_id && (
              <p className="text-xs text-muted-foreground">タスクID: {save.response.task_id}</p>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="flex-1 bg-background overflow-y-auto">
      <div className="sticky top-0 z-10 border-b border-border bg-card px-6 py-4 flex items-center justify-between relative">
        <button
          type="button"
          className="absolute left-2 top-1/2 -translate-y-1/2 h-7 w-7 rounded-full border border-border bg-card text-muted-foreground hover:text-foreground shadow-sm"
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
        <Button onClick={onCreateSection} className="bg-black text-white hover:bg-black/90">
          <Plus className="h-4 w-4 mr-2" />
          New Section
        </Button>
      </div>
      <div className="p-6 space-y-6">
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
                  {section?.title ?? DEFAULT_RESEARCH_TITLE}
                </p>
              )}
              <Button
                variant="outline"
                size="sm"
                onClick={
                  isEditingAutoTitle ? handleSaveAutoTitle : () => setIsEditingAutoTitle(true)
                }
              >
                {isEditingAutoTitle ? "save" : "edit"}
              </Button>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="auto-queries">クエリ (改行区切り)</Label>
              <Textarea
                id="auto-queries"
                value={autoQueries}
                onChange={(e) => setAutoQueries(e.target.value)}
                placeholder="ex) vision-language models for video QA"
              />
            </div>
            <div className="grid gap-4 md:grid-cols-3">
              <div className="space-y-2">
                <Label htmlFor="auto-github-owner">GitHub Owner</Label>
                <Input
                  id="auto-github-owner"
                  value={autoGithubOwner}
                  onChange={(e) => setAutoGithubOwner(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="auto-repo-name">Repository</Label>
                <Input
                  id="auto-repo-name"
                  value={autoRepoName}
                  onChange={(e) => setAutoRepoName(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="auto-branch">Branch</Label>
                <Input
                  id="auto-branch"
                  value={autoBranch}
                  onChange={(e) => setAutoBranch(e.target.value)}
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="auto-runner-labels">Runner Labels (カンマ区切り)</Label>
                <Input
                  id="auto-runner-labels"
                  value={autoRunnerLabels}
                  onChange={(e) => setAutoRunnerLabels(e.target.value)}
                  placeholder="ubuntu-latest,gpu-runner"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="auto-runner-desc">Runner 説明</Label>
                <Textarea
                  id="auto-runner-desc"
                  value={autoRunnerDescription}
                  onChange={(e) => setAutoRunnerDescription(e.target.value)}
                  placeholder="A100 x1, 40GB / 8 vCPU / 32GB RAM"
                />
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="auto-wandb-entity">WandB Entity</Label>
                <Input
                  id="auto-wandb-entity"
                  value={autoWandbEntity}
                  onChange={(e) => setAutoWandbEntity(e.target.value)}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="auto-wandb-project">WandB Project</Label>
                <Input
                  id="auto-wandb-project"
                  value={autoWandbProject}
                  onChange={(e) => setAutoWandbProject(e.target.value)}
                />
              </div>
            </div>

            <div className="rounded-md border border-border">
              <button
                type="button"
                className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-foreground"
                onClick={() => setShowAdvancedSettings((prev) => !prev)}
              >
                <span>詳細設定</span>
                {showAdvancedSettings ? (
                  <ChevronUp className="h-4 w-4" />
                ) : (
                  <ChevronDown className="h-4 w-4" />
                )}
              </button>
              {showAdvancedSettings && (
                <div className="p-4 space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <Label htmlFor="auto-max-results">max_results_per_query</Label>
                      <Input
                        id="auto-max-results"
                        type="number"
                        inputMode="numeric"
                        value={autoMaxResultsPerQuery}
                        onChange={(e) => setAutoMaxResultsPerQuery(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="auto-refinement-rounds">refinement_rounds</Label>
                      <Input
                        id="auto-refinement-rounds"
                        type="number"
                        inputMode="numeric"
                        value={autoRefinementRounds}
                        onChange={(e) => setAutoRefinementRounds(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="auto-num-models">num_models_to_use</Label>
                      <Input
                        id="auto-num-models"
                        type="number"
                        inputMode="numeric"
                        value={autoNumModelsToUse}
                        onChange={(e) => setAutoNumModelsToUse(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="auto-num-datasets">num_datasets_to_use</Label>
                      <Input
                        id="auto-num-datasets"
                        type="number"
                        inputMode="numeric"
                        value={autoNumDatasetsToUse}
                        onChange={(e) => setAutoNumDatasetsToUse(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="auto-num-comparative-methods">num_comparative_methods</Label>
                      <Input
                        id="auto-num-comparative-methods"
                        type="number"
                        inputMode="numeric"
                        value={autoNumComparativeMethods}
                        onChange={(e) => setAutoNumComparativeMethods(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="auto-max-code-validations">max_code_validations</Label>
                      <Input
                        id="auto-max-code-validations"
                        type="number"
                        inputMode="numeric"
                        value={autoMaxCodeValidations}
                        onChange={(e) => setAutoMaxCodeValidations(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="auto-writing-refinement-rounds">
                        writing_refinement_rounds
                      </Label>
                      <Input
                        id="auto-writing-refinement-rounds"
                        type="number"
                        inputMode="numeric"
                        value={autoWritingRefinementRounds}
                        onChange={(e) => setAutoWritingRefinementRounds(e.target.value)}
                      />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="auto-latex-template-name">latex_template_name</Label>
                      <Select
                        value={autoLatexTemplateName}
                        onValueChange={setAutoLatexTemplateName}
                      >
                        <SelectTrigger className="w-full">
                          <SelectValue placeholder="iclr2024" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="iclr2024">iclr2024</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="flex items-center gap-3">
              <Checkbox
                id="auto-private"
                checked={autoIsPrivate}
                onCheckedChange={(val) => setAutoIsPrivate(Boolean(val))}
              />
              <Label htmlFor="auto-private" className="text-sm text-muted-foreground">
                リポジトリをプライベート扱いにする
              </Label>
            </div>

            <div className="flex flex-wrap gap-3">
              <Button onClick={handleRunAutoResearch} disabled={isAutoRunning}>
                {isAutoRunning ? "実行中..." : "自動研究を実行"}
              </Button>
              <Button variant="secondary" onClick={handleSaveAutoResearch}>
                この設定で保存
              </Button>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>ステータス確認</CardTitle>
            <CardDescription>
              タスクIDをもとに最新のステータスと研究履歴を取得します。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-wrap gap-3 items-center">
              <Button
                variant="outline"
                onClick={() => handleRefreshAutoStatus()}
                disabled={isAutoRunning || !autoTaskId}
              >
                ステータス確認
              </Button>
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
                    <p className="text-sm font-medium break-all">{autoStatus.task_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">ステータス</p>
                    <p className="text-sm font-medium">{autoStatus.status}</p>
                  </div>
                </div>
                {autoStatus.error && <p className="text-sm text-destructive">{autoStatus.error}</p>}
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
              </>
            ) : (
              <p className="text-sm text-muted-foreground">まだ実行結果がありません</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>自動研究の保存履歴</CardTitle>
            <CardDescription>設定・結果を手動で保存できます。</CardDescription>
          </CardHeader>
          <CardContent>{renderAutoHistory()}</CardContent>
        </Card>
      </div>
    </div>
  );
}
