import { useCallback, useState } from "react";
import { Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { AutonomousResearchPage } from "@/components/pages/autonomous-research";
import { HypothesisDrivenResearchPage } from "@/components/pages/hypothesis-driven-research";
import { NotificationsPage } from "@/components/pages/notifications";
import { PapersPage } from "@/components/pages/papers";
import { SettingsPage } from "@/components/pages/settings";
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
  autonomousSectionMap: Record<AutonomousSubNav, ResearchSection | null>;
  autonomousSessions: Record<AutonomousSubNav, ResearchSection[]>;
  onSelectAutonomousSession: (subNav: AutonomousSubNav, section: ResearchSection) => void;
  assistedResearchProps: AssistedResearchProps;
  onCreateSection: (subNav: AutonomousSubNav) => void;
  onUpdateSectionTitle: (subNav: AutonomousSubNav, title: string) => void;
  onRefreshSessions: (subNav: AutonomousSubNav, preferredId?: string) => Promise<void>;
  verifications: Verification[];
  onDeleteVerification: (id: string) => void;
  onDuplicateVerification: (id: string) => void;
  onUpdateVerification: (id: string, updates: Partial<Verification>) => void;
  onCreateWithMethod: (sourceVerification: Verification, method: ProposedMethod) => void;
  autonomousListViewKey: number;
}

function VerificationDetailRoute({
  verifications,
  onUpdateVerification,
  onCreateWithMethod,
}: {
  verifications: Verification[];
  onUpdateVerification: (id: string, updates: Partial<Verification>) => void;
  onCreateWithMethod: (sourceVerification: Verification, method: ProposedMethod) => void;
}) {
  const { id } = useParams<{ id: string }>();
  const verification = verifications.find((v) => v.id === id) ?? null;
  return (
    <VerificationDetailPage
      verification={verification}
      onUpdateVerification={onUpdateVerification}
      onCreateWithMethod={onCreateWithMethod}
    />
  );
}

function AutonomousResearchRoute({
  subNav,
  autonomousSectionMap,
  autonomousSessions,
  onSelectAutonomousSession,
  onCreateSection,
  onUpdateSectionTitle,
  onRefreshSessions,
  listViewKey,
}: {
  subNav: AutonomousSubNav;
  autonomousSectionMap: Record<AutonomousSubNav, ResearchSection | null>;
  autonomousSessions: Record<AutonomousSubNav, ResearchSection[]>;
  onSelectAutonomousSession: (subNav: AutonomousSubNav, section: ResearchSection) => void;
  onCreateSection: (subNav: AutonomousSubNav) => void;
  onUpdateSectionTitle: (subNav: AutonomousSubNav, title: string) => void;
  onRefreshSessions: (subNav: AutonomousSubNav, preferredId?: string) => Promise<void>;
  listViewKey: number;
}) {
  const PageComponent =
    subNav === "topic-driven" ? AutonomousResearchPage : HypothesisDrivenResearchPage;
  return (
    <PageComponent
      section={autonomousSectionMap[subNav]}
      sessions={autonomousSessions[subNav]}
      onSelectSession={(section) => onSelectAutonomousSession(subNav, section)}
      onCreateSection={() => onCreateSection(subNav)}
      onUpdateSectionTitle={(title) => onUpdateSectionTitle(subNav, title)}
      onRefreshSessions={(preferredId) => onRefreshSessions(subNav, preferredId)}
      listViewKey={listViewKey}
    />
  );
}

export function MainContent({
  autonomousSectionMap,
  autonomousSessions,
  onSelectAutonomousSession,
  assistedResearchProps,
  onCreateSection,
  onUpdateSectionTitle,
  onRefreshSessions,
  verifications,
  onDeleteVerification,
  onDuplicateVerification,
  onUpdateVerification,
  onCreateWithMethod,
  autonomousListViewKey,
}: MainContentProps) {
  const navigate = useNavigate();
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
    <div className="flex-1 flex min-w-0">
      <Routes>
        <Route path="/" element={null} />
        <Route
          path="/home"
          element={
            <VerificationHomePage
              verifications={verifications}
              onSelectVerification={(id) => navigate(`/verification/${id}`)}
              onDeleteVerification={onDeleteVerification}
              onDuplicateVerification={onDuplicateVerification}
            />
          }
        />
        <Route
          path="/verification/:id"
          element={
            <VerificationDetailRoute
              verifications={verifications}
              onUpdateVerification={onUpdateVerification}
              onCreateWithMethod={onCreateWithMethod}
            />
          }
        />
        <Route
          path="/papers"
          element={
            <PapersPage
              selectedPapers={selectedPapers}
              onPapersChange={setSelectedPapers}
              onStepExecuted={handlePapersStepExecuted}
              onSave={handleSavePapersSnapshot}
            />
          }
        />
        <Route
          path="/autonomous-research/topic-driven"
          element={
            <AutonomousResearchRoute
              subNav="topic-driven"
              autonomousSectionMap={autonomousSectionMap}
              autonomousSessions={autonomousSessions}
              onSelectAutonomousSession={onSelectAutonomousSession}
              onCreateSection={onCreateSection}
              onUpdateSectionTitle={onUpdateSectionTitle}
              onRefreshSessions={onRefreshSessions}
              listViewKey={autonomousListViewKey}
            />
          }
        />
        <Route
          path="/autonomous-research/hypothesis-driven"
          element={
            <AutonomousResearchRoute
              subNav="hypothesis-driven"
              autonomousSectionMap={autonomousSectionMap}
              autonomousSessions={autonomousSessions}
              onSelectAutonomousSession={onSelectAutonomousSession}
              onCreateSection={onCreateSection}
              onUpdateSectionTitle={onUpdateSectionTitle}
              onRefreshSessions={onRefreshSessions}
              listViewKey={autonomousListViewKey}
            />
          }
        />
        <Route
          path="/autonomous-research"
          element={<Navigate to="/autonomous-research/topic-driven" replace />}
        />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/settings/:tab" element={<SettingsRoute />} />
        <Route path="/settings" element={<Navigate to="/settings/profile" replace />} />
        <Route path="*" element={<Navigate to="/home" replace />} />
      </Routes>
    </div>
  );
}

function SettingsRoute() {
  const { tab } = useParams<{ tab: string }>();
  const VALID_TABS = [
    "profile",
    "feedback",
    "integration",
    "api-token",
    "user-plan",
    "receipts",
    "usage",
  ];
  const activeTab = VALID_TABS.includes(tab ?? "")
    ? (tab as Parameters<typeof SettingsPage>[0]["activeTab"])
    : "profile";
  return <SettingsPage activeTab={activeTab} />;
}
