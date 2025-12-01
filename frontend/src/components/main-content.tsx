"use client"

import { useState, useRef, useEffect } from "react"
import type {
  ResearchSection,
  Paper,
  Method,
  ExperimentConfig,
  ExperimentResult,
  GeneratedPaper,
  WorkflowTree as WorkflowTreeType,
  WorkflowNode,
  FeatureType,
} from "@/types/research"
import { PaperSearchSection } from "@/components/features/paper-search"
import { MethodGenerationSection } from "@/components/features/method-generation"
import { ExperimentConfigSection } from "@/components/features/experiment-config"
import { CodeGenerationSection } from "@/components/features/code-generation"
import { ExperimentRunSection } from "@/components/features/experiment-run"
import { AnalysisSection } from "@/components/features/analysis"
import { PaperWritingSection } from "@/components/features/paper-writing"
import { WorkflowTree } from "@/components/workflow-tree"
import { cn } from "@/lib/utils"

const featureLabels: Record<string, string> = {
  papers: "論文取得",
  method: "新規手法の生成",
  "experiment-config": "実験設定の作成",
  "code-generation": "実験コードの生成",
  "experiment-run": "実験の実行",
  analysis: "実験結果の分析",
  "paper-writing": "論文の作成",
}

const featureOrder: FeatureType[] = [
  "papers",
  "method",
  "experiment-config",
  "code-generation",
  "experiment-run",
  "analysis",
  "paper-writing",
]

export type SnapshotData = Partial<WorkflowNode["snapshot"]>

interface MainContentProps {
  section: ResearchSection | null
  activeFeature: string | null
  setActiveFeature: (feature: string | null) => void
  workflowTree: WorkflowTreeType
  activeNodeId: string | null
  setActiveNodeId: (nodeId: string | null) => void
  addWorkflowNode: (
    type: FeatureType,
    parentNodeId: string | null,
    isBranch?: boolean,
    data?: WorkflowNode["data"],
    snapshot?: WorkflowNode["snapshot"],
  ) => string
  createBranchFromNode: (sourceNodeId: string, newType: FeatureType) => string
  updateNodeData: (nodeId: string, data: Partial<WorkflowNode["data"]>) => void
  updateNodeSnapshot: (nodeId: string, snapshot: WorkflowNode["snapshot"]) => void
  resetDownstreamSections: (fromType: FeatureType) => void
  getNodePathData: (nodeId: string) => Record<FeatureType, WorkflowNode["data"]>
  onNavigate: (nodeId: string) => void
}

export function MainContent({
  section,
  activeFeature,
  setActiveFeature,
  workflowTree,
  activeNodeId,
  setActiveNodeId,
  addWorkflowNode,
  createBranchFromNode,
  updateNodeData,
  updateNodeSnapshot,
  resetDownstreamSections,
  getNodePathData,
  onNavigate,
}: MainContentProps) {
  const [selectedPapers, setSelectedPapers] = useState<Paper[]>([])
  const [generatedMethod, setGeneratedMethod] = useState<Method | null>(null)
  const [experimentConfigs, setExperimentConfigs] = useState<ExperimentConfig[]>([])
  const [githubUrl, setGithubUrl] = useState<string | null>(null)
  const [experimentResults, setExperimentResults] = useState<ExperimentResult[]>([])
  const [analysisText, setAnalysisText] = useState<string | null>(null)
  const [generatedPaper, setGeneratedPaper] = useState<GeneratedPaper | null>(null)

  const skipNextRestoreRef = useRef(false)
  const lastActiveNodeIdRef = useRef<string | null>(null)

  const sectionRefs = useRef<Record<string, HTMLDivElement | null>>({})

  useEffect(() => {
    if (lastActiveNodeIdRef.current === activeNodeId) {
      return
    }
    lastActiveNodeIdRef.current = activeNodeId

    if (skipNextRestoreRef.current) {
      skipNextRestoreRef.current = false
      return
    }

    if (activeNodeId) {
      const node = workflowTree.nodes[activeNodeId]
      if (node?.snapshot) {
        setSelectedPapers(node.snapshot.selectedPapers || [])
        setGeneratedMethod(node.snapshot.generatedMethod || null)
        setExperimentConfigs(node.snapshot.experimentConfigs || [])
        setGithubUrl(node.snapshot.githubUrl || null)
        setExperimentResults(node.snapshot.experimentResults || [])
        setAnalysisText(node.snapshot.analysisText || null)
        setGeneratedPaper(node.snapshot.generatedPaper || null)
      }
    }
  }, [activeNodeId, workflowTree.nodes])

  useEffect(() => {
    if (activeFeature && sectionRefs.current[activeFeature]) {
      sectionRefs.current[activeFeature]?.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }, [activeFeature])

  if (!section) {
    return (
      <div className="flex-1 flex items-center justify-center bg-background">
        <div className="text-center">
          <h2 className="text-xl font-semibold text-muted-foreground">No Section Selected</h2>
          <p className="text-sm text-muted-foreground mt-2">Create or select a research section to begin</p>
        </div>
      </div>
    )
  }

  const handleClose = () => setActiveFeature(null)

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
        newData?.generatedPaper !== undefined ? newData.generatedPaper : generatedPaper ? { ...generatedPaper } : null,
    }
  }

  const getCurrentDataForType = (type: FeatureType, newData?: SnapshotData): WorkflowNode["data"] => {
    switch (type) {
      case "papers":
        return { selectedPapers: newData?.selectedPapers ?? [...selectedPapers] }
      case "method":
        return {
          generatedMethod:
            newData?.generatedMethod !== undefined
              ? newData.generatedMethod
              : generatedMethod
                ? { ...generatedMethod }
                : null,
        }
      case "experiment-config":
        return { experimentConfigs: newData?.experimentConfigs ?? [...experimentConfigs] }
      case "code-generation":
        return { githubUrl: newData?.githubUrl !== undefined ? newData.githubUrl : githubUrl }
      case "experiment-run":
        return { experimentResults: newData?.experimentResults ?? [...experimentResults] }
      case "analysis":
        return { analysisText: newData?.analysisText !== undefined ? newData.analysisText : analysisText }
      case "paper-writing":
        return {
          generatedPaper:
            newData?.generatedPaper !== undefined
              ? newData.generatedPaper
              : generatedPaper
                ? { ...generatedPaper }
                : null,
        }
      default:
        return {}
    }
  }

  const handleStepExecuted = (type: FeatureType, newData?: SnapshotData) => {
    skipNextRestoreRef.current = true

    const typeIndex = featureOrder.indexOf(type)
    let parentNodeId: string | null = null

    if (typeIndex > 0) {
      const prevType = featureOrder[typeIndex - 1]

      if (activeNodeId && workflowTree.nodes[activeNodeId]?.type === prevType) {
        parentNodeId = activeNodeId
      } else {
        let latestNodeOfPrevType: string | null = null
        let latestCreatedAt: Date | null = null

        for (const nodeId in workflowTree.nodes) {
          const node = workflowTree.nodes[nodeId]
          if (node.type === prevType) {
            if (activeNodeId) {
              const activeNode = workflowTree.nodes[activeNodeId]
              if (activeNode && node.branchIndex === activeNode.branchIndex) {
                if (!latestCreatedAt || node.createdAt > latestCreatedAt) {
                  latestNodeOfPrevType = nodeId
                  latestCreatedAt = node.createdAt
                }
              }
            } else {
              if (!latestCreatedAt || node.createdAt > latestCreatedAt) {
                latestNodeOfPrevType = nodeId
                latestCreatedAt = node.createdAt
              }
            }
          }
        }

        if (!latestNodeOfPrevType) {
          for (const nodeId in workflowTree.nodes) {
            const node = workflowTree.nodes[nodeId]
            if (node.type === prevType) {
              if (!latestCreatedAt || node.createdAt > workflowTree.nodes[nodeId].createdAt) {
                latestNodeOfPrevType = nodeId
                latestCreatedAt = node.createdAt
              }
            }
          }
        }

        parentNodeId = latestNodeOfPrevType
      }
    }

    const currentData = getCurrentDataForType(type, newData)
    const snapshot = createSnapshot(newData)
    const newNodeId = addWorkflowNode(type, parentNodeId, false, currentData, snapshot)

    lastActiveNodeIdRef.current = newNodeId
    setActiveNodeId(newNodeId)
    return newNodeId
  }

  const handleBranchCreated = (sourceType: FeatureType, newData?: SnapshotData) => {
    skipNextRestoreRef.current = true

    resetDownstreamState(sourceType)
    resetDownstreamSections(sourceType)

    let sourceNodeId: string | null = null

    if (activeNodeId && workflowTree.nodes[activeNodeId]?.type === sourceType) {
      sourceNodeId = activeNodeId
    } else {
      for (const nodeId in workflowTree.nodes) {
        const node = workflowTree.nodes[nodeId]
        if (node.type === sourceType) {
          if (!sourceNodeId || node.createdAt > workflowTree.nodes[nodeId].createdAt) {
            sourceNodeId = nodeId
          }
        }
      }
    }

    const currentData = getCurrentDataForType(sourceType, newData)
    const snapshot = createSnapshot(newData)

    if (sourceNodeId) {
      const sourceNode = workflowTree.nodes[sourceNodeId]
      const newNodeId = addWorkflowNode(sourceType, sourceNode.parentId, true, currentData, snapshot)
      lastActiveNodeIdRef.current = newNodeId
      setActiveNodeId(newNodeId)
      return newNodeId
    }
    const newNodeId = addWorkflowNode(sourceType, null, true, currentData, snapshot)
    lastActiveNodeIdRef.current = newNodeId
    setActiveNodeId(newNodeId)
    return newNodeId
  }

  const resetDownstreamState = (fromType: FeatureType) => {
    const fromIndex = featureOrder.indexOf(fromType)

    for (let i = fromIndex + 1; i < featureOrder.length; i++) {
      const type = featureOrder[i]
      switch (type) {
        case "experiment-config":
          setExperimentConfigs([])
          break
        case "code-generation":
          setGithubUrl(null)
          break
        case "experiment-run":
          setExperimentResults([])
          break
        case "analysis":
          setAnalysisText(null)
          break
        case "paper-writing":
          setGeneratedPaper(null)
          break
      }
    }
  }

  const isSectionCompleted = (type: FeatureType): boolean => {
    if (!activeNodeId) {
      switch (type) {
        case "papers":
          return selectedPapers.length > 0
        case "method":
          return generatedMethod !== null
        case "experiment-config":
          return experimentConfigs.length > 0
        case "code-generation":
          return githubUrl !== null
        case "experiment-run":
          return experimentResults.length > 0
        case "analysis":
          return analysisText !== null
        case "paper-writing":
          return generatedPaper !== null
        default:
          return false
      }
    }

    const activeNode = workflowTree.nodes[activeNodeId]
    if (!activeNode) return false

    const activeTypeIndex = featureOrder.indexOf(activeNode.type)
    const currentTypeIndex = featureOrder.indexOf(type)

    return currentTypeIndex < activeTypeIndex
  }

  const handleUpdateSnapshot = (type: FeatureType) => {
    if (activeNodeId && workflowTree.nodes[activeNodeId]?.type === type) {
      const snapshot = createSnapshot()
      updateNodeSnapshot(activeNodeId, snapshot)
    }
  }

  return (
    <div className="flex-1 bg-background overflow-y-auto">
      <div className="sticky top-0 z-10">
        <div className="h-16 border-b border-border bg-card px-6 flex items-center">
          <h2 className="text-lg font-semibold text-foreground">{section.title}</h2>
        </div>
        <WorkflowTree workflowTree={workflowTree} activeNodeId={activeNodeId} onNavigate={onNavigate} />
      </div>

      <div className="p-6 space-y-8">
        <div
          ref={(el) => {
            sectionRefs.current["papers"] = el
          }}
          id="papers"
          className={cn("scroll-mt-20 transition-opacity", isSectionCompleted("papers") && "opacity-60")}
        >
          <PaperSearchSection
            selectedPapers={selectedPapers}
            onPapersChange={setSelectedPapers}
            onStepExecuted={(papers) => handleStepExecuted("papers", { selectedPapers: papers })}
            onSave={() => handleUpdateSnapshot("papers")}
          />
        </div>

        <div
          ref={(el) => {
            sectionRefs.current["method"] = el
          }}
          id="method"
          className={cn("scroll-mt-20 transition-opacity", isSectionCompleted("method") && "opacity-60")}
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
            sectionRefs.current["experiment-config"] = el
          }}
          id="experiment-config"
          className={cn("scroll-mt-20 transition-opacity", isSectionCompleted("experiment-config") && "opacity-60")}
        >
          <ExperimentConfigSection
            method={generatedMethod}
            configs={experimentConfigs}
            onConfigsGenerated={setExperimentConfigs}
            onStepExecuted={(configs) => handleStepExecuted("experiment-config", { experimentConfigs: configs })}
            onBranchCreated={(configs) => handleBranchCreated("experiment-config", { experimentConfigs: configs })}
            onSave={() => handleUpdateSnapshot("experiment-config")}
          />
        </div>

        <div
          ref={(el) => {
            sectionRefs.current["code-generation"] = el
          }}
          id="code-generation"
          className={cn("scroll-mt-20 transition-opacity", isSectionCompleted("code-generation") && "opacity-60")}
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
            sectionRefs.current["experiment-run"] = el
          }}
          id="experiment-run"
          className={cn("scroll-mt-20 transition-opacity", isSectionCompleted("experiment-run") && "opacity-60")}
        >
          <ExperimentRunSection
            configs={experimentConfigs}
            results={experimentResults}
            onResultsChange={setExperimentResults}
            onStepExecuted={(results) => handleStepExecuted("experiment-run", { experimentResults: results })}
            onSave={() => handleUpdateSnapshot("experiment-run")}
          />
        </div>

        <div
          ref={(el) => {
            sectionRefs.current["analysis"] = el
          }}
          id="analysis"
          className={cn("scroll-mt-20 transition-opacity", isSectionCompleted("analysis") && "opacity-60")}
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
            sectionRefs.current["paper-writing"] = el
          }}
          id="paper-writing"
          className={cn("scroll-mt-20 transition-opacity", isSectionCompleted("paper-writing") && "opacity-60")}
        >
          <PaperWritingSection
            method={generatedMethod}
            configs={experimentConfigs}
            results={experimentResults}
            analysisText={analysisText}
            generatedPaper={generatedPaper}
            onPaperGenerated={setGeneratedPaper}
            onStepExecuted={(paper) => handleStepExecuted("paper-writing", { generatedPaper: paper })}
            onBranchCreated={(paper) => handleBranchCreated("paper-writing", { generatedPaper: paper })}
            onSave={() => handleUpdateSnapshot("paper-writing")}
          />
        </div>
      </div>
    </div>
  )
}
