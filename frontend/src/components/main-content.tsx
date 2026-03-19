import { FeatherLayoutList } from "@subframe/core";
import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { Navigate, Route, Routes, useNavigate, useParams } from "react-router-dom";
import { AutonomousResearchPage } from "@/components/pages/autonomous-research";
import { HypothesisDrivenResearchPage } from "@/components/pages/hypothesis-driven-research";
import { NotificationsPage } from "@/components/pages/notifications";
import { PapersPage } from "@/components/pages/papers";
import { ReproductionPage } from "@/components/pages/reproduction";
import { EE_ONLY_TABS, SETTINGS_TABS, SettingsPage } from "@/components/pages/settings";
import { VerificationDetailPage, VerificationHomePage } from "@/components/pages/verification";
import { ChatInput } from "@/components/pages/verification/detail/chat-input";
import { useAutonomousResearchContext } from "@/contexts/autonomous-research-context";
import { useVerificationContext } from "@/contexts/verification-context";
import { useEE } from "@/hooks/use-ee-components";
import type {
  FeatureType,
  Paper,
  WorkflowNode,
  WorkflowTree as WorkflowTreeType,
} from "@/types/research";

export const AUTONOMOUS_SUB_NAVS = ["topic-driven", "hypothesis-driven"] as const;
export type AutonomousSubNav = (typeof AUTONOMOUS_SUB_NAVS)[number];

export function getAutonomousSubNav(pathname: string): AutonomousSubNav {
  if (pathname.includes("hypothesis-driven")) return "hypothesis-driven";
  return "topic-driven";
}

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
  assistedResearchProps: AssistedResearchProps;
}

function VerificationDetailRoute() {
  const { id } = useParams<{ id: string }>();
  const { verifications, onUpdateVerification, onCreateWithMethod } = useVerificationContext();
  const verification = verifications.find((v) => v.id === id) ?? null;
  return (
    <VerificationDetailPage
      verification={verification}
      onUpdateVerification={onUpdateVerification}
      onCreateWithMethod={onCreateWithMethod}
    />
  );
}

function AutonomousResearchRoute({ subNav }: { subNav: AutonomousSubNav }) {
  const {
    activeSectionMap,
    sectionsMap,
    onSelectSession,
    onCreateSection,
    onUpdateSectionTitle,
    onRefreshSessions,
    listViewKey,
  } = useAutonomousResearchContext();
  const PageComponent =
    subNav === "topic-driven" ? AutonomousResearchPage : HypothesisDrivenResearchPage;
  return (
    <PageComponent
      section={activeSectionMap[subNav]}
      sessions={sectionsMap[subNav]}
      onSelectSession={(section) => onSelectSession(subNav, section)}
      onCreateSection={() => onCreateSection(subNav)}
      onUpdateSectionTitle={(title) => onUpdateSectionTitle(subNav, title)}
      onRefreshSessions={(preferredId) => onRefreshSessions(subNav, preferredId)}
      listViewKey={listViewKey}
    />
  );
}

export function MainContent({ assistedResearchProps }: MainContentProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [selectedPapers, setSelectedPapers] = useState<Paper[]>([]);

  const { verifications, onDeleteVerification, onDuplicateVerification, onCreateWithQuery } =
    useVerificationContext();

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
        <Route path="/" element={<Navigate to="/home" replace />} />
        <Route
          path="/home"
          element={
            <div className="flex-1 flex flex-col">
              <div className="flex-shrink-0 px-6 py-6">
                <button
                  type="button"
                  onClick={() => navigate("/verification")}
                  className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium text-neutral-500 hover:bg-neutral-50 active:bg-neutral-100 transition-colors cursor-pointer"
                >
                  <FeatherLayoutList className="h-4 w-4" />
                  {t("nav.verificationList")}
                </button>
              </div>
              <div className="flex-1 flex items-center justify-center pb-[20vh] p-6">
                <ChatInput onSubmit={onCreateWithQuery} />
              </div>
            </div>
          }
        />
        <Route
          path="/verification"
          element={
            <VerificationHomePage
              verifications={verifications}
              onSelectVerification={(id) => navigate(`/verification/${id}`)}
              onDeleteVerification={onDeleteVerification}
              onDuplicateVerification={onDuplicateVerification}
              onCreateNew={() => navigate("/home")}
            />
          }
        />
        <Route path="/verification/:id" element={<VerificationDetailRoute />} />
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
          element={<AutonomousResearchRoute subNav="topic-driven" />}
        />
        <Route
          path="/autonomous-research/hypothesis-driven"
          element={<AutonomousResearchRoute subNav="hypothesis-driven" />}
        />
        <Route
          path="/autonomous-research"
          element={<Navigate to="/autonomous-research/topic-driven" replace />}
        />
        <Route path="/notifications" element={<NotificationsPage />} />
        <Route path="/reproduction" element={<ReproductionPage />} />
        <Route path="/settings/:tab" element={<SettingsRoute />} />
        <Route path="/settings" element={<Navigate to="/settings/profile" replace />} />
        <Route path="*" element={<Navigate to="/home" replace />} />
      </Routes>
    </div>
  );
}

function SettingsRoute() {
  const { tab } = useParams<{ tab: string }>();
  const { isAuthenticated, loading } = useEE();

  const isValidTab = SETTINGS_TABS.includes(tab as never);
  const isEETab = EE_ONLY_TABS.includes(tab as never);

  if (!isValidTab) {
    return <Navigate to="/settings/profile" replace />;
  }

  if (isEETab && loading) {
    return null;
  }

  if (isEETab && !isAuthenticated) {
    return <Navigate to="/settings/profile" replace />;
  }

  return <SettingsPage activeTab={tab as Parameters<typeof SettingsPage>[0]["activeTab"]} />;
}
