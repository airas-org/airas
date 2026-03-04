import { useCallback, useState } from "react";
import { AutonomousResearchPage } from "@/components/pages/autonomous-research";
import { HypothesisDrivenResearchPage } from "@/components/pages/hypothesis-driven-research";
import { IntegrationPage } from "@/components/pages/integration";
import { PapersPage } from "@/components/pages/papers";
import { UserPlanPage } from "@/components/pages/user-plan";
import {
  type ProposedMethod,
  type Verification,
  VerificationDetailPage,
  VerificationHomePage,
} from "@/components/pages/verification";
import type {
  FeatureType,
  Paper,
  ResearchSection,
  WorkflowNode,
  WorkflowTree as WorkflowTreeType,
} from "@/types/research";

export type NavKey =
  | "home"
  | "papers"
  | "autonomous-research"
  | "integration"
  | "user-plan"
  | "verification";
export const AUTONOMOUS_SUB_NAVS = ["topic-driven", "hypothesis-driven"] as const;
export type AutonomousSubNav = (typeof AUTONOMOUS_SUB_NAVS)[number];

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
  autonomousSection: ResearchSection | null;
  activeNav: NavKey;
  autonomousSubNav: AutonomousSubNav;
  assistedResearchProps: AssistedResearchProps;
  sessionsExpanded: boolean;
  onToggleSessions: () => void;
  onCreateSection: () => void;
  onUpdateSectionTitle: (title: string) => void;
  onRefreshSessions: (preferredId?: string) => Promise<void>;
  verifications: Verification[];
  activeVerification: Verification | null;
  onSelectVerification: (id: string) => void;
  onDeleteVerification: (id: string) => void;
  onDuplicateVerification: (id: string) => void;
  onUpdateVerification: (id: string, updates: Partial<Verification>) => void;
  onCreateWithMethod: (sourceVerification: Verification, method: ProposedMethod) => void;
}

export function MainContent({
  autonomousSection,
  activeNav,
  autonomousSubNav,
  assistedResearchProps,
  sessionsExpanded,
  onToggleSessions,
  onCreateSection,
  onUpdateSectionTitle,
  onRefreshSessions,
  verifications,
  activeVerification,
  onSelectVerification,
  onDeleteVerification,
  onDuplicateVerification,
  onUpdateVerification,
  onCreateWithMethod,
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
      <div className={activeNav === "home" ? "flex-1 flex" : "hidden"}>
        <VerificationHomePage
          verifications={verifications}
          onSelectVerification={onSelectVerification}
          onDeleteVerification={onDeleteVerification}
          onDuplicateVerification={onDuplicateVerification}
        />
      </div>

      <div className={activeNav === "verification" ? "flex-1 flex" : "hidden"}>
        <VerificationDetailPage
          verification={activeVerification}
          onUpdateVerification={onUpdateVerification}
          onCreateWithMethod={onCreateWithMethod}
        />
      </div>

      <div className={activeNav === "papers" ? "flex-1 flex" : "hidden"}>
        <PapersPage
          selectedPapers={selectedPapers}
          onPapersChange={setSelectedPapers}
          onStepExecuted={handlePapersStepExecuted}
          onSave={handleSavePapersSnapshot}
        />
      </div>

      <div className={activeNav === "autonomous-research" ? "flex-1 flex" : "hidden"}>
        {autonomousSubNav === "topic-driven" ? (
          <AutonomousResearchPage
            section={autonomousSection}
            sessionsExpanded={sessionsExpanded}
            onToggleSessions={onToggleSessions}
            onCreateSection={onCreateSection}
            onUpdateSectionTitle={onUpdateSectionTitle}
            onRefreshSessions={onRefreshSessions}
          />
        ) : (
          <HypothesisDrivenResearchPage
            section={autonomousSection}
            sessionsExpanded={sessionsExpanded}
            onToggleSessions={onToggleSessions}
            onCreateSection={onCreateSection}
            onUpdateSectionTitle={onUpdateSectionTitle}
            onRefreshSessions={onRefreshSessions}
          />
        )}
      </div>

      <div className={activeNav === "integration" ? "flex-1 flex" : "hidden"}>
        <IntegrationPage />
      </div>
      <div className={activeNav === "user-plan" ? "flex-1 flex" : "hidden"}>
        <UserPlanPage />
      </div>
    </div>
  );
}
