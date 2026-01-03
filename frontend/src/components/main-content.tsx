"use client";

import { ChevronDown, ChevronLeft, ChevronRight, ChevronUp, Plus } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { AnalysisSection } from "@/components/features/analysis";
import { CodeGenerationSection } from "@/components/features/code-generation";
import { ExperimentConfigSection } from "@/components/features/experiment-config";
import { ExperimentRunSection } from "@/components/features/experiment-run";
import { MethodGenerationSection } from "@/components/features/method-generation";
import { PaperSearchSection } from "@/components/features/paper-search";
import { PaperWritingSection } from "@/components/features/paper-writing";
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
import { WorkflowTree } from "@/components/workflow-tree";
import type {
  TopicOpenEndedResearchRequestBody,
  TopicOpenEndedResearchResponseBody,
} from "@/lib/api";
import { TopicOpenEndedResearchService } from "@/lib/api";
import { cn } from "@/lib/utils";
import type {
  ExperimentConfig,
  ExperimentResult,
  FeatureType,
  GeneratedPaper,
  Method,
  Paper,
  ResearchSection,
  WorkflowNode,
  WorkflowTree as WorkflowTreeType,
} from "@/types/research";

const DEFAULT_RESEARCH_TITLE = "Untitled Research";

const featureOrder: FeatureType[] = [
  "papers",
  "method",
  "experiment-config",
  "code-generation",
  "experiment-run",
  "analysis",
  "paper-writing",
];

export type SnapshotData = Partial<WorkflowNode["snapshot"]>;
export type NavKey = "papers" | "research" | "auto-research";

type AutoResearchSave = {
  id: string;
  savedAt: Date;
  payload: TopicOpenEndedResearchRequestBody;
  response: TopicOpenEndedResearchResponseBody | null;
};

interface MainContentProps {
  section: ResearchSection | null;
  activeFeature: string | null;
  activeNav: NavKey;
  workflowTree: WorkflowTreeType;
  activeNodeId: string | null;
  setActiveNodeId: (nodeId: string | null) => void;
  addWorkflowNode: (
    type: FeatureType,
    parentNodeId: string | null,
    isBranch?: boolean,
    data?: WorkflowNode["data"],
    snapshot?: WorkflowNode["snapshot"],
  ) => string;
  createBranchFromNode: (sourceNodeId: string, newType: FeatureType) => string;
  updateNodeData: (nodeId: string, data: Partial<WorkflowNode["data"]>) => void;
  updateNodeSnapshot: (nodeId: string, snapshot: WorkflowNode["snapshot"]) => void;
  resetDownstreamSections: (fromType: FeatureType) => void;
  onNavigate: (nodeId: string) => void;
  onCreateSection: () => void;
  onUpdateSectionTitle: (title: string) => void;
  sectionsExpanded: boolean;
  onToggleSections: () => void;
}

export function MainContent({
  section,
  activeFeature,
  activeNav,
  workflowTree,
  activeNodeId,
  setActiveNodeId,
  addWorkflowNode,
  createBranchFromNode: _createBranchFromNode,
  updateNodeData: _updateNodeData,
  updateNodeSnapshot,
  resetDownstreamSections,
  onNavigate,
  onCreateSection,
  onUpdateSectionTitle,
  sectionsExpanded,
  onToggleSections,
}: MainContentProps) {
  const [selectedPapers, setSelectedPapers] = useState<Paper[]>([]);
  const [generatedMethod, setGeneratedMethod] = useState<Method | null>(null);
  const [experimentConfigs, setExperimentConfigs] = useState<ExperimentConfig[]>([]);
  const [githubUrl, setGithubUrl] = useState<string | null>(null);
  const [experimentResults, setExperimentResults] = useState<ExperimentResult[]>([]);
  const [analysisText, setAnalysisText] = useState<string | null>(null);
  const [generatedPaper, setGeneratedPaper] = useState<GeneratedPaper | null>(null);
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
  const [isAutoRunning, setIsAutoRunning] = useState(false);
  const [autoError, setAutoError] = useState<string | null>(null);
  const [autoResponse, setAutoResponse] = useState<ExecuteE2EResponseBody | null>(null);
  const [isEditingAutoTitle, setIsEditingAutoTitle] = useState(false);
  const [autoTitleDraft, setAutoTitleDraft] = useState(section?.title ?? DEFAULT_RESEARCH_TITLE);
  const [isEditingResearchTitle, setIsEditingResearchTitle] = useState(false);
  const [researchTitleDraft, setResearchTitleDraft] = useState(
    section?.title ?? DEFAULT_RESEARCH_TITLE,
  );

  const skipNextRestoreRef = useRef(false);
  const lastActiveNodeIdRef = useRef<string | null>(null);

  const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    if (lastActiveNodeIdRef.current === activeNodeId) {
      return;
    }
    lastActiveNodeIdRef.current = activeNodeId;

    if (skipNextRestoreRef.current) {
      skipNextRestoreRef.current = false;
      return;
    }

    if (activeNodeId) {
      const node = workflowTree.nodes[activeNodeId];
      if (node?.snapshot) {
        setSelectedPapers(node.snapshot.selectedPapers || []);
        setGeneratedMethod(node.snapshot.generatedMethod || null);
        setExperimentConfigs(node.snapshot.experimentConfigs || []);
        setGithubUrl(node.snapshot.githubUrl || null);
        setExperimentResults(node.snapshot.experimentResults || []);
        setAnalysisText(node.snapshot.analysisText || null);
        setGeneratedPaper(node.snapshot.generatedPaper || null);
      }
    }
  }, [activeNodeId, workflowTree.nodes]);

  useEffect(() => {
    if (activeFeature && sectionRefs.current[activeFeature]) {
      sectionRefs.current[activeFeature]?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [activeFeature]);

  useEffect(() => {
    const nextTitle = section?.title ?? DEFAULT_RESEARCH_TITLE;
    setAutoTitleDraft(nextTitle);
    setResearchTitleDraft(nextTitle);
  }, [section?.title]);

  if (!section && activeNav !== "papers") {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-muted-foreground">No Section Selected</h2>
          <p className="text-sm text-muted-foreground mt-2">
            Create or select a research section to begin
          </p>
        </div>
      </div>
    );
  }

  const createSnapshot = (newData?: SnapshotData): WorkflowNode["snapshot"] => {
    return {
      selectedPapers: newData?.selectedPapers ?? [...selectedPapers],
      generatedMethod:
        newData?.generatedMethod !== undefined
          ? newData.generatedMethod
          : generatedMethod
            ? { ...generatedMethod }
            : null,
      experimentConfigs: newData?.experimentConfigs ?? [...experimentConfigs],
      githubUrl: newData?.githubUrl !== undefined ? newData.githubUrl : githubUrl,
      experimentResults: newData?.experimentResults ?? [...experimentResults],
      analysisText: newData?.analysisText !== undefined ? newData.analysisText : analysisText,
      generatedPaper:
        newData?.generatedPaper !== undefined
          ? newData.generatedPaper
          : generatedPaper
            ? { ...generatedPaper }
            : null,
    };
  };

  const getCurrentDataForType = (
    type: FeatureType,
    newData?: SnapshotData,
  ): WorkflowNode["data"] => {
    switch (type) {
      case "papers":
        return { selectedPapers: newData?.selectedPapers ?? [...selectedPapers] };
      case "method":
        return {
          generatedMethod:
            newData?.generatedMethod !== undefined
              ? newData.generatedMethod
              : generatedMethod
                ? { ...generatedMethod }
                : null,
        };
      case "experiment-config":
        return { experimentConfigs: newData?.experimentConfigs ?? [...experimentConfigs] };
      case "code-generation":
        return { githubUrl: newData?.githubUrl !== undefined ? newData.githubUrl : githubUrl };
      case "experiment-run":
        return { experimentResults: newData?.experimentResults ?? [...experimentResults] };
      case "analysis":
        return {
          analysisText: newData?.analysisText !== undefined ? newData.analysisText : analysisText,
        };
      case "paper-writing":
        return {
          generatedPaper:
            newData?.generatedPaper !== undefined
              ? newData.generatedPaper
              : generatedPaper
                ? { ...generatedPaper }
                : null,
        };
      default:
        return {};
    }
  };

  const handleStepExecuted = (type: FeatureType, newData?: SnapshotData) => {
    skipNextRestoreRef.current = true;

    const typeIndex = featureOrder.indexOf(type);
    let parentNodeId: string | null = null;

    if (typeIndex > 0) {
      const prevType = featureOrder[typeIndex - 1];

      if (activeNodeId && workflowTree.nodes[activeNodeId]?.type === prevType) {
        parentNodeId = activeNodeId;
      } else {
        let latestNodeOfPrevType: string | null = null;
        let latestCreatedAt: Date | null = null;

        for (const nodeId in workflowTree.nodes) {
          const node = workflowTree.nodes[nodeId];
          if (node.type === prevType) {
            if (activeNodeId) {
              const activeNode = workflowTree.nodes[activeNodeId];
              if (activeNode && node.branchIndex === activeNode.branchIndex) {
                if (!latestCreatedAt || node.createdAt > latestCreatedAt) {
                  latestNodeOfPrevType = nodeId;
                  latestCreatedAt = node.createdAt;
                }
              }
            } else {
              if (!latestCreatedAt || node.createdAt > latestCreatedAt) {
                latestNodeOfPrevType = nodeId;
                latestCreatedAt = node.createdAt;
              }
            }
          }
        }

        if (!latestNodeOfPrevType) {
          for (const nodeId in workflowTree.nodes) {
            const node = workflowTree.nodes[nodeId];
            if (node.type === prevType) {
              if (!latestCreatedAt || node.createdAt > workflowTree.nodes[nodeId].createdAt) {
                latestNodeOfPrevType = nodeId;
                latestCreatedAt = node.createdAt;
              }
            }
          }
        }

        parentNodeId = latestNodeOfPrevType;
      }
    }

    const currentData = getCurrentDataForType(type, newData);
    const snapshot = createSnapshot(newData);
    const newNodeId = addWorkflowNode(type, parentNodeId, false, currentData, snapshot);

    lastActiveNodeIdRef.current = newNodeId;
    setActiveNodeId(newNodeId);
    return newNodeId;
  };

  const handleBranchCreated = (sourceType: FeatureType, newData?: SnapshotData) => {
    skipNextRestoreRef.current = true;

    resetDownstreamState(sourceType);
    resetDownstreamSections(sourceType);

    let sourceNodeId: string | null = null;

    if (activeNodeId && workflowTree.nodes[activeNodeId]?.type === sourceType) {
      sourceNodeId = activeNodeId;
    } else {
      for (const nodeId in workflowTree.nodes) {
        const node = workflowTree.nodes[nodeId];
        if (node.type === sourceType) {
          if (!sourceNodeId || node.createdAt > workflowTree.nodes[nodeId].createdAt) {
            sourceNodeId = nodeId;
          }
        }
      }
    }

    const currentData = getCurrentDataForType(sourceType, newData);
    const snapshot = createSnapshot(newData);

    if (sourceNodeId) {
      const sourceNode = workflowTree.nodes[sourceNodeId];
      const newNodeId = addWorkflowNode(
        sourceType,
        sourceNode.parentId,
        true,
        currentData,
        snapshot,
      );
      lastActiveNodeIdRef.current = newNodeId;
      setActiveNodeId(newNodeId);
      return newNodeId;
    }
    const newNodeId = addWorkflowNode(sourceType, null, true, currentData, snapshot);
    lastActiveNodeIdRef.current = newNodeId;
    setActiveNodeId(newNodeId);
    return newNodeId;
  };

  const resetDownstreamState = (fromType: FeatureType) => {
    const fromIndex = featureOrder.indexOf(fromType);

    for (let i = fromIndex + 1; i < featureOrder.length; i++) {
      const type = featureOrder[i];
      switch (type) {
        case "experiment-config":
          setExperimentConfigs([]);
          break;
        case "code-generation":
          setGithubUrl(null);
          break;
        case "experiment-run":
          setExperimentResults([]);
          break;
        case "analysis":
          setAnalysisText(null);
          break;
        case "paper-writing":
          setGeneratedPaper(null);
          break;
      }
    }
  };

  const isSectionCompleted = (type: FeatureType): boolean => {
    if (!activeNodeId) {
      switch (type) {
        case "papers":
          return selectedPapers.length > 0;
        case "method":
          return generatedMethod !== null;
        case "experiment-config":
          return experimentConfigs.length > 0;
        case "code-generation":
          return githubUrl !== null;
        case "experiment-run":
          return experimentResults.length > 0;
        case "analysis":
          return analysisText !== null;
        case "paper-writing":
          return generatedPaper !== null;
        default:
          return false;
      }
    }

    const activeNode = workflowTree.nodes[activeNodeId];
    if (!activeNode) return false;

    const activeTypeIndex = featureOrder.indexOf(activeNode.type);
    const currentTypeIndex = featureOrder.indexOf(type);

    return currentTypeIndex < activeTypeIndex;
  };

  const handleUpdateSnapshot = (type: FeatureType) => {
    if (activeNodeId && workflowTree.nodes[activeNodeId]?.type === type) {
      const snapshot = createSnapshot();
      updateNodeSnapshot(activeNodeId, snapshot);
    }
  };

  const buildAutoResearchPayload = (): TopicOpenEndedResearchRequestBody => {
    const queryList = autoQueries
      .split("\n")
      .map((q) => q.trim())
      .filter((q) => q.length > 0);

    const toNumber = (value: string): number | undefined => {
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : undefined;
    };

    return {
      github_config: {
        github_owner: autoGithubOwner,
        repository_name: autoRepoName,
        branch_name: autoBranch,
      },
      query_list: queryList,
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
      is_private: autoIsPrivate,
      max_results_per_query: toNumber(autoMaxResultsPerQuery),
      refinement_rounds: toNumber(autoRefinementRounds),
      num_models_to_use: toNumber(autoNumModelsToUse),
      num_datasets_to_use: toNumber(autoNumDatasetsToUse),
      num_comparative_methods: toNumber(autoNumComparativeMethods),
      max_code_validations: toNumber(autoMaxCodeValidations),
      writing_refinement_rounds: toNumber(autoWritingRefinementRounds),
      latex_template_name: autoLatexTemplateName.trim() || undefined,
    };
  };

  const handleSaveAutoResearch = () => {
    const payload = buildAutoResearchPayload();
    const id = `auto-research-save-${Date.now()}`;
    setAutoResearchSaves((prev) => [
      { id, savedAt: new Date(), payload, response: autoResponse },
      ...prev,
    ]);
  };

  const handleRunAutoResearch = async () => {
    setIsAutoRunning(true);
    setAutoError(null);
    try {
      const payload = buildAutoResearchPayload();
      if (payload.query_list.length === 0) {
        throw new Error("クエリを1つ以上入力してください");
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

      const response = await TopicOpenEndedResearchService.executeE2EAirasV1E2ERunPost(payload);
      setAutoResponse(response);
    } catch (error) {
      const message = error instanceof Error ? error.message : "自動研究の実行に失敗しました";
      setAutoError(message);
    } finally {
      setIsAutoRunning(false);
    }
  };

  const handleRefreshAutoStatus = async () => {
    if (!autoResponse?.task_id) return;
    setIsAutoRunning(true);
    setAutoError(null);
    try {
      const response = await TopicOpenEndedResearchService.getE2EStatusAirasV1E2EStatusTaskIdGet(
        autoResponse.task_id,
      );
      setAutoResponse(response);
    } catch (error) {
      const message = error instanceof Error ? error.message : "ステータスの取得に失敗しました";
      setAutoError(message);
    } finally {
      setIsAutoRunning(false);
    }
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
              クエリ {save.payload.query_list.length} 件 / リポジトリ{" "}
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

  const handleSaveResearchTitle = () => {
    onUpdateSectionTitle(researchTitleDraft);
    setIsEditingResearchTitle(false);
  };

  const handleSaveAutoTitle = () => {
    onUpdateSectionTitle(autoTitleDraft);
    setIsEditingAutoTitle(false);
  };

  const renderAutoResearchContent = () => (
    <div className="flex-1 bg-background overflow-y-auto">
      <div className="sticky top-0 z-10 border-b border-border bg-card px-6 py-4 flex items-center justify-between relative">
        <button
          type="button"
          className="absolute left-2 top-1/2 -translate-y-1/2 h-7 w-7 rounded-full border border-border bg-card text-muted-foreground hover:text-foreground shadow-sm"
          onClick={onToggleSections}
          aria-label="Toggle sections"
        >
          {sectionsExpanded ? (
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
                onClick={handleRefreshAutoStatus}
                disabled={isAutoRunning || !autoResponse?.task_id}
              >
                ステータス確認
              </Button>
              {!autoResponse?.task_id && (
                <p className="text-sm text-muted-foreground">
                  先に自動研究を実行してタスクIDを取得してください。
                </p>
              )}
            </div>
            {autoError && <p className="text-sm text-destructive">{autoError}</p>}
            {autoResponse ? (
              <>
                <div className="grid gap-2 md:grid-cols-2">
                  <div>
                    <p className="text-sm text-muted-foreground">タスクID</p>
                    <p className="text-sm font-medium break-all">{autoResponse.task_id}</p>
                  </div>
                  <div>
                    <p className="text-sm text-muted-foreground">ステータス</p>
                    <p className="text-sm font-medium">{autoResponse.status}</p>
                  </div>
                </div>
                {autoResponse.error && (
                  <p className="text-sm text-destructive">{autoResponse.error}</p>
                )}
                {autoResponse.research_history && (
                  <div className="rounded-md border border-border bg-card/60 p-3">
                    <p className="text-sm font-semibold">研究履歴</p>
                    <p className="text-sm text-muted-foreground">
                      目的: {autoResponse.research_history.research_objective ?? "N/A"}
                    </p>
                    {autoResponse.research_history.paper_url && (
                      <p className="text-sm text-muted-foreground">
                        論文URL: {autoResponse.research_history.paper_url}
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

  if (activeNav === "auto-research") {
    return renderAutoResearchContent();
  }

  if (activeNav === "papers") {
    return (
      <div className="flex-1 bg-background overflow-y-auto">
        <div className="sticky top-0 z-10 border-b border-border bg-card px-6 py-4">
          <h2 className="text-lg font-semibold text-foreground">論文取得</h2>
          <p className="text-sm text-muted-foreground">論文検索を実行します</p>
        </div>
        <div className="p-6">
          <div
            ref={(el) => {
              sectionRefs.current.papers = el;
            }}
            id="papers"
            className={cn(
              "scroll-mt-20 transition-opacity",
              isSectionCompleted("papers") && "opacity-60",
            )}
          >
            <PaperSearchSection
              selectedPapers={selectedPapers}
              onPapersChange={setSelectedPapers}
              onStepExecuted={(papers) => handleStepExecuted("papers", { selectedPapers: papers })}
              onSave={() => handleUpdateSnapshot("papers")}
            />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 bg-background overflow-y-auto">
      <div className="sticky top-0 z-10">
        <div className="h-20 border-b border-border bg-card px-6 flex items-center justify-between relative">
          <button
            type="button"
            className="absolute left-2 top-1/2 -translate-y-1/2 h-7 w-7 rounded-full border border-border bg-card text-muted-foreground hover:text-foreground shadow-sm"
            onClick={onToggleSections}
            aria-label="Toggle sections"
          >
            {sectionsExpanded ? (
              <ChevronLeft className="h-4 w-4" />
            ) : (
              <ChevronRight className="h-4 w-4" />
            )}
          </button>
          <div className="space-y-2 pl-9">
            <h2 className="text-lg font-semibold text-foreground">Assisted Research</h2>
          </div>
          <Button onClick={onCreateSection} className="bg-black text-white hover:bg-black/90">
            <Plus className="h-4 w-4 mr-2" />
            New Section
          </Button>
        </div>
        <WorkflowTree
          workflowTree={workflowTree}
          activeNodeId={activeNodeId}
          onNavigate={onNavigate}
        />
      </div>

      <div className="p-6 space-y-8">
        <Card>
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            {isEditingResearchTitle ? (
              <Input
                id="research-section-title"
                value={researchTitleDraft}
                onChange={(e) => setResearchTitleDraft(e.target.value)}
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
                isEditingResearchTitle
                  ? handleSaveResearchTitle
                  : () => setIsEditingResearchTitle(true)
              }
            >
              {isEditingResearchTitle ? "save" : "edit"}
            </Button>
          </CardHeader>
        </Card>

        <div
          ref={(el) => {
            sectionRefs.current.method = el;
          }}
          id="method"
          className={cn(
            "scroll-mt-20 transition-opacity",
            isSectionCompleted("method") && "opacity-60",
          )}
        >
          <MethodGenerationSection
            selectedPapers={selectedPapers}
            generatedMethod={generatedMethod}
            onMethodGenerated={setGeneratedMethod}
            onStepExecuted={(method) => handleStepExecuted("method", { generatedMethod: method })}
            onBranchCreated={(method) => handleBranchCreated("method", { generatedMethod: method })}
            onSave={() => handleUpdateSnapshot("method")}
          />
        </div>

        <div
          ref={(el) => {
            sectionRefs.current["experiment-config"] = el;
          }}
          id="experiment-config"
          className={cn(
            "scroll-mt-20 transition-opacity",
            isSectionCompleted("experiment-config") && "opacity-60",
          )}
        >
          <ExperimentConfigSection
            method={generatedMethod}
            configs={experimentConfigs}
            onConfigsGenerated={setExperimentConfigs}
            onStepExecuted={(configs) =>
              handleStepExecuted("experiment-config", { experimentConfigs: configs })
            }
            onBranchCreated={(configs) =>
              handleBranchCreated("experiment-config", { experimentConfigs: configs })
            }
            onSave={() => handleUpdateSnapshot("experiment-config")}
          />
        </div>

        <div
          ref={(el) => {
            sectionRefs.current["code-generation"] = el;
          }}
          id="code-generation"
          className={cn(
            "scroll-mt-20 transition-opacity",
            isSectionCompleted("code-generation") && "opacity-60",
          )}
        >
          <CodeGenerationSection
            configs={experimentConfigs}
            githubUrl={githubUrl}
            onGithubUrlChange={setGithubUrl}
            onStepExecuted={(url) => handleStepExecuted("code-generation", { githubUrl: url })}
            onSave={() => handleUpdateSnapshot("code-generation")}
          />
        </div>

        <div
          ref={(el) => {
            sectionRefs.current["experiment-run"] = el;
          }}
          id="experiment-run"
          className={cn(
            "scroll-mt-20 transition-opacity",
            isSectionCompleted("experiment-run") && "opacity-60",
          )}
        >
          <ExperimentRunSection
            configs={experimentConfigs}
            results={experimentResults}
            onResultsChange={setExperimentResults}
            onStepExecuted={(results) =>
              handleStepExecuted("experiment-run", { experimentResults: results })
            }
            onSave={() => handleUpdateSnapshot("experiment-run")}
          />
        </div>

        <div
          ref={(el) => {
            sectionRefs.current.analysis = el;
          }}
          id="analysis"
          className={cn(
            "scroll-mt-20 transition-opacity",
            isSectionCompleted("analysis") && "opacity-60",
          )}
        >
          <AnalysisSection
            results={experimentResults}
            analysisText={analysisText}
            onAnalysisGenerated={setAnalysisText}
            onStepExecuted={(text) => handleStepExecuted("analysis", { analysisText: text })}
            onSave={() => handleUpdateSnapshot("analysis")}
          />
        </div>

        <div
          ref={(el) => {
            sectionRefs.current["paper-writing"] = el;
          }}
          id="paper-writing"
          className={cn(
            "scroll-mt-20 transition-opacity",
            isSectionCompleted("paper-writing") && "opacity-60",
          )}
        >
          <PaperWritingSection
            method={generatedMethod}
            configs={experimentConfigs}
            results={experimentResults}
            analysisText={analysisText}
            generatedPaper={generatedPaper}
            onPaperGenerated={setGeneratedPaper}
            onStepExecuted={(paper) =>
              handleStepExecuted("paper-writing", { generatedPaper: paper })
            }
            onBranchCreated={(paper) =>
              handleBranchCreated("paper-writing", { generatedPaper: paper })
            }
            onSave={() => handleUpdateSnapshot("paper-writing")}
          />
        </div>
      </div>
    </div>
  );
}
