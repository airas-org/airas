"use client";

import { ChevronLeft, ChevronRight, Plus } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { AnalysisSection } from "@/components/features/analysis";
import { CodeGenerationSection } from "@/components/features/code-generation";
import { ExperimentConfigSection } from "@/components/features/experiment-config";
import { ExperimentRunSection } from "@/components/features/experiment-run";
import { MethodGenerationSection } from "@/components/features/method-generation";
import { PaperWritingSection } from "@/components/features/paper-writing";
import { Button } from "@/components/ui/button";
import { Card, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { WorkflowTree } from "@/components/workflow-tree";
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

type SnapshotData = Partial<WorkflowNode["snapshot"]>;

interface AssistedResearchPageProps {
  section: ResearchSection | null;
  activeFeature: string | null;
  selectedPapers: Paper[];
  onSelectedPapersChange: (papers: Paper[]) => void;
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
  updateNodeSnapshot: (nodeId: string, snapshot: WorkflowNode["snapshot"]) => void;
  resetDownstreamSections: (fromType: FeatureType) => void;
  onNavigate: (nodeId: string) => void;
  onCreateSection: () => void;
  onUpdateSectionTitle: (title: string) => void;
  sectionsExpanded: boolean;
  onToggleSections: () => void;
}

export function AssistedResearchPage({
  section,
  activeFeature,
  selectedPapers,
  onSelectedPapersChange,
  workflowTree,
  activeNodeId,
  setActiveNodeId,
  addWorkflowNode,
  updateNodeSnapshot,
  resetDownstreamSections,
  onNavigate,
  onCreateSection,
  onUpdateSectionTitle,
  sectionsExpanded,
  onToggleSections,
}: AssistedResearchPageProps) {
  const [generatedMethod, setGeneratedMethod] = useState<Method | null>(null);
  const [experimentConfigs, setExperimentConfigs] = useState<ExperimentConfig[]>([]);
  const [githubUrl, setGithubUrl] = useState<string | null>(null);
  const [experimentResults, setExperimentResults] = useState<ExperimentResult[]>([]);
  const [analysisText, setAnalysisText] = useState<string | null>(null);
  const [generatedPaper, setGeneratedPaper] = useState<GeneratedPaper | null>(null);
  const [isEditingResearchTitle, setIsEditingResearchTitle] = useState(false);
  const [researchTitleDraft, setResearchTitleDraft] = useState(
    section?.title ?? DEFAULT_RESEARCH_TITLE,
  );

  const skipNextRestoreRef = useRef(false);
  const lastActiveNodeIdRef = useRef<string | null>(null);
  const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({});

  useEffect(() => {
    if (lastActiveNodeIdRef.current === activeNodeId) return;
    lastActiveNodeIdRef.current = activeNodeId;

    if (skipNextRestoreRef.current) {
      skipNextRestoreRef.current = false;
      return;
    }

    if (activeNodeId) {
      const node = workflowTree.nodes[activeNodeId];
      if (node?.snapshot) {
        onSelectedPapersChange(node.snapshot.selectedPapers || []);
        setGeneratedMethod(node.snapshot.generatedMethod || null);
        setExperimentConfigs(node.snapshot.experimentConfigs || []);
        setGithubUrl(node.snapshot.githubUrl || null);
        setExperimentResults(node.snapshot.experimentResults || []);
        setAnalysisText(node.snapshot.analysisText || null);
        setGeneratedPaper(node.snapshot.generatedPaper || null);
      }
    }
  }, [activeNodeId, onSelectedPapersChange, workflowTree.nodes]);

  useEffect(() => {
    if (activeFeature && sectionRefs.current[activeFeature]) {
      sectionRefs.current[activeFeature]?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [activeFeature]);

  useEffect(() => {
    const nextTitle = section?.title ?? DEFAULT_RESEARCH_TITLE;
    setResearchTitleDraft(nextTitle);
  }, [section?.title]);

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
            } else if (!latestCreatedAt || node.createdAt > latestCreatedAt) {
              latestNodeOfPrevType = nodeId;
              latestCreatedAt = node.createdAt;
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

  const handleSaveResearchTitle = () => {
    onUpdateSectionTitle(researchTitleDraft);
    setIsEditingResearchTitle(false);
  };

  return (
    <div className="flex-1 bg-background overflow-y-auto">
      <div className="sticky top-0">
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
