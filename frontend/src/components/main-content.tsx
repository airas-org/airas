"use client";

import { useCallback, useState } from "react";
import { AssistedResearchPage } from "@/components/pages/assisted-research/index";
import { AutonomousResearchPage } from "@/components/pages/autonomous-research";
import { PapersPage } from "@/components/pages/papers";
import type {
  FeatureType,
  Paper,
  ResearchSection,
  WorkflowNode,
  WorkflowTree as WorkflowTreeType,
} from "@/types/research";

export type NavKey = "papers" | "assisted-research" | "autonomous-research";

interface AssistedResearchProps {
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
  resetDownstreamSessions: (fromType: FeatureType) => void;
  onNavigate: (nodeId: string) => void;
}

interface MainContentProps {
  assistedSection: ResearchSection | null;
  autonomousSection: ResearchSection | null;
  activeFeature: string | null;
  activeNav: NavKey;
  assistedResearchProps: AssistedResearchProps;
  sessionsExpanded: boolean;
  onToggleSessions: () => void;
  onCreateSection: () => void;
  onUpdateSectionTitle: (title: string) => void;
  onRefreshAutoSessions: (preferredId?: string) => Promise<void>;
}

const NoSectionSelected = () => (
  <div className="flex-1 flex items-center justify-center bg-background">
    <div className="text-center">
      <h2 className="text-xl font-semibold text-muted-foreground">No Section Selected</h2>
      <p className="text-sm text-muted-foreground mt-2">
        Create or select a research section to begin
      </p>
    </div>
  </div>
);

export function MainContent({
  assistedSection,
  autonomousSection,
  activeFeature,
  activeNav,
  assistedResearchProps,
  sessionsExpanded,
  onToggleSessions,
  onCreateSection,
  onUpdateSectionTitle,
  onRefreshAutoSessions,
}: MainContentProps) {
  const [selectedPapers, setSelectedPapers] = useState<Paper[]>([]);

  const handlePapersStepExecuted = useCallback(
    (papers: Paper[]) => {
      setSelectedPapers(papers);
      const snapshot: WorkflowNode["snapshot"] = {
        selectedPapers: papers,
        generatedMethod: null,
        experimentConfigs: [],
        githubUrl: null,
        experimentResults: [],
        analysisText: null,
        generatedPaper: null,
      };
      const nodeId = assistedResearchProps.addWorkflowNode(
        "papers",
        null,
        false,
        { selectedPapers: papers },
        snapshot,
      );
      assistedResearchProps.setActiveNodeId(nodeId);
    },
    [assistedResearchProps],
  );

  const handleSavePapersSnapshot = useCallback(() => {
    const { activeNodeId, workflowTree, updateNodeSnapshot } = assistedResearchProps;
    if (activeNodeId && workflowTree.nodes[activeNodeId]?.type === "papers") {
      const snapshot: WorkflowNode["snapshot"] = {
        selectedPapers,
        generatedMethod: null,
        experimentConfigs: [],
        githubUrl: null,
        experimentResults: [],
        analysisText: null,
        generatedPaper: null,
      };
      updateNodeSnapshot(activeNodeId, snapshot);
    }
  }, [assistedResearchProps, selectedPapers]);

  return (
    <div className="flex-1 flex">
      <div className={activeNav === "papers" ? "flex-1 flex" : "hidden"}>
        <PapersPage
          selectedPapers={selectedPapers}
          onPapersChange={setSelectedPapers}
          onStepExecuted={handlePapersStepExecuted}
          onSave={handleSavePapersSnapshot}
        />
      </div>

      <div className={activeNav === "autonomous-research" ? "flex-1 flex" : "hidden"}>
        <AutonomousResearchPage
          section={autonomousSection}
          sessionsExpanded={sessionsExpanded}
          onToggleSessions={onToggleSessions}
          onCreateSection={onCreateSection}
          onUpdateSectionTitle={onUpdateSectionTitle}
          onRefreshAutoSessions={onRefreshAutoSessions}
        />
      </div>

      <div className={activeNav === "assisted-research" ? "flex-1 flex" : "hidden"}>
        {assistedSection ? (
          <AssistedResearchPage
            section={assistedSection}
            activeFeature={activeFeature}
            selectedPapers={selectedPapers}
            onSelectedPapersChange={setSelectedPapers}
            sessionsExpanded={sessionsExpanded}
            onToggleSessions={onToggleSessions}
            onCreateSection={onCreateSection}
            onUpdateSectionTitle={onUpdateSectionTitle}
            workflowTree={assistedResearchProps.workflowTree}
            activeNodeId={assistedResearchProps.activeNodeId}
            setActiveNodeId={assistedResearchProps.setActiveNodeId}
            addWorkflowNode={assistedResearchProps.addWorkflowNode}
            updateNodeSnapshot={assistedResearchProps.updateNodeSnapshot}
            resetDownstreamSessions={assistedResearchProps.resetDownstreamSessions}
            onNavigate={assistedResearchProps.onNavigate}
          />
        ) : (
          <NoSectionSelected />
        )}
      </div>
    </div>
  );
}
