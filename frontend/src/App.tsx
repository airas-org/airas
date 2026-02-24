// frontend/src/App.tsx

import { SiDiscord, SiGithub, SiX } from "@icons-pack/react-simple-icons";
import axios from "axios";
import { ChevronDown, ChevronRight, FileText, UserCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { type AutonomousSubNav, MainContent, type NavKey } from "@/components/main-content";
import { useAutonomousResearchSessions } from "@/components/pages/autonomous-research/use-autonomous-research-sessions";
import { useHypothesisDrivenSessions } from "@/components/pages/hypothesis-driven-research/use-hypothesis-driven-sessions";
import { SectionsSidebar } from "@/components/sections-sidebar";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { isEnterpriseEnabled } from "@/ee/config";
import { cn } from "@/lib/utils";
import type { FeatureType, ResearchSection, WorkflowNode, WorkflowTree } from "@/types/research";

const mockResearchSections: ResearchSection[] = [
  {
    id: "1",
    title: "Untitled Research",
    createdAt: new Date("2024-01-15"),
    status: "in-progress",
  },
  {
    id: "2",
    title: "GAN-based Image Generation",
    createdAt: new Date("2024-01-10"),
    status: "completed",
  },
  {
    id: "3",
    title: "Reinforcement Learning Study",
    createdAt: new Date("2024-01-05"),
    status: "completed",
  },
];

const initialWorkflowTree: WorkflowTree = {
  nodes: {},
  rootId: null,
  activeNodeId: null,
};

// Lazy-loaded EE components (only imported when EE is enabled)
type AuthGuardType = typeof import("@/ee/auth/components/AuthGuard").AuthGuard;
type UserMenuType = typeof import("@/ee/auth/components/UserMenu").UserMenu;
type AuthCallbackType = typeof import("@/ee/auth/components/AuthCallback").AuthCallback;

interface EEComponents {
  AuthGuard: AuthGuardType;
  UserMenu: UserMenuType;
  AuthCallback: AuthCallbackType;
}

function useEEComponents() {
  const [eeComponents, setEeComponents] = useState<EEComponents | null>(null);

  useEffect(() => {
    if (!isEnterpriseEnabled()) return;

    Promise.all([
      import("@/ee/auth/components/AuthGuard"),
      import("@/ee/auth/components/UserMenu"),
      import("@/ee/auth/components/AuthCallback"),
      import("@/ee/auth/lib/axios-interceptor"),
    ]).then(([authGuard, userMenu, authCallback, interceptor]) => {
      setEeComponents({
        AuthGuard: authGuard.AuthGuard,
        UserMenu: userMenu.UserMenu,
        AuthCallback: authCallback.AuthCallback,
      });
      axios.interceptors.request.use(interceptor.authRequestInterceptor);
    });
  }, []);

  return eeComponents;
}

export default function App() {
  const eeComponents = useEEComponents();

  const [assistedSections, setAssistedSections] = useState<ResearchSection[]>(mockResearchSections);
  const [autonomousSections, setAutonomousSections] = useState<ResearchSection[]>([]);
  const [hypothesisSections, setHypothesisSections] = useState<ResearchSection[]>([]);
  const [activeAssistedSection, setActiveAssistedSection] = useState<ResearchSection | null>(
    mockResearchSections[0],
  );
  const [activeAutonomousSection, setActiveAutonomousSection] = useState<ResearchSection | null>(
    null,
  );
  const [activeHypothesisSection, setActiveHypothesisSection] = useState<ResearchSection | null>(
    null,
  );
  const [activeFeature, setActiveFeature] = useState<string | null>(null);
  const [workflowTree, setWorkflowTree] = useState<WorkflowTree>(initialWorkflowTree);
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);
  // Currently selected (default)
  const [activeNav, setActiveNav] = useState<NavKey>("autonomous-research");
  const [isAutonomousExpanded, setIsAutonomousExpanded] = useState(true);
  const [autonomousSubNav, setAutonomousSubNav] = useState<AutonomousSubNav>("topic-driven");
  const [sessionsExpanded, setSessionsExpanded] = useState(false);

  const { fetchAutoSections } = useAutonomousResearchSessions({
    setAutonomousSections,
    setActiveAutonomousSection,
  });

  const { fetchHypothesisSections } = useHypothesisDrivenSessions({
    setHypothesisSections,
    setActiveHypothesisSection,
  });

  const handleCreateSection = () => {
    const newSection: ResearchSection = {
      id: Date.now().toString(),
      title: "Untitled Research",
      createdAt: new Date(),
      status: "in-progress",
    };
    if (activeNav === "autonomous-research") {
      if (autonomousSubNav === "hypothesis-driven") {
        setActiveHypothesisSection(null);
      } else {
        setActiveAutonomousSection(null);
      }
    } else {
      setAssistedSections([newSection, ...assistedSections]);
      setActiveAssistedSection(newSection);
    }
    setWorkflowTree(initialWorkflowTree);
    setActiveNodeId(null);
    setActiveFeature(null);
  };

  const handleToggleSessions = useCallback(() => {
    setSessionsExpanded((prev) => !prev);
  }, []);

  const handleNavigate = useCallback(
    (nodeId: string) => {
      const node = workflowTree.nodes[nodeId];
      if (node) {
        setActiveNodeId(nodeId);
        setActiveFeature(node.type);
      }
    },
    [workflowTree],
  );

  const addWorkflowNode = useCallback(
    (
      type: FeatureType,
      parentNodeId: string | null,
      isBranch = false,
      data?: WorkflowNode["data"],
      snapshot?: WorkflowNode["snapshot"],
    ): string => {
      const newNodeId = `node-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

      setWorkflowTree((prev) => {
        const newNodes = { ...prev.nodes };

        let branchIndex = 0;
        if (parentNodeId) {
          const parentNode = prev.nodes[parentNodeId];
          if (parentNode) {
            if (isBranch) {
              const siblingBranches = parentNode.children.map(
                (id) => prev.nodes[id]?.branchIndex || 0,
              );
              const maxSiblingBranch =
                siblingBranches.length > 0 ? Math.max(...siblingBranches) : parentNode.branchIndex;
              branchIndex = maxSiblingBranch + 1;
            } else {
              branchIndex = parentNode.branchIndex;
            }
          }
        } else if (isBranch) {
          let maxBranch = 0;
          for (const nodeId in prev.nodes) {
            maxBranch = Math.max(maxBranch, prev.nodes[nodeId].branchIndex);
          }
          branchIndex = maxBranch + 1;
        }

        const newNode: WorkflowNode = {
          id: newNodeId,
          type,
          branchIndex,
          parentId: parentNodeId,
          children: [],
          data: data || {},
          snapshot,
          createdAt: new Date(),
        };

        newNodes[newNodeId] = newNode;

        if (parentNodeId && newNodes[parentNodeId]) {
          newNodes[parentNodeId] = {
            ...newNodes[parentNodeId],
            children: [...newNodes[parentNodeId].children, newNodeId],
          };
        }

        return {
          nodes: newNodes,
          rootId: prev.rootId || newNodeId,
          activeNodeId: newNodeId,
        };
      });

      setActiveNodeId(newNodeId);
      return newNodeId;
    },
    [],
  );

  const updateNodeSnapshot = useCallback((nodeId: string, snapshot: WorkflowNode["snapshot"]) => {
    setWorkflowTree((prev) => ({
      ...prev,
      nodes: {
        ...prev.nodes,
        [nodeId]: {
          ...prev.nodes[nodeId],
          snapshot,
        },
      },
    }));
  }, []);

  const resetDownstreamSessions = useCallback((_fromType: FeatureType) => {
    // ここはそのまま
  }, []);

  const handleUpdateSectionTitle = useCallback(
    (title: string) => {
      if (activeNav === "autonomous-research") {
        if (autonomousSubNav === "hypothesis-driven") {
          if (!activeHypothesisSection) return;
          setHypothesisSections((prev) =>
            prev.map((s) => (s.id === activeHypothesisSection.id ? { ...s, title } : s)),
          );
          setActiveHypothesisSection((prev) => (prev ? { ...prev, title } : prev));
        } else {
          if (!activeAutonomousSection) return;
          setAutonomousSections((prev) =>
            prev.map((s) => (s.id === activeAutonomousSection.id ? { ...s, title } : s)),
          );
          setActiveAutonomousSection((prev) => (prev ? { ...prev, title } : prev));
        }
      } else {
        if (!activeAssistedSection) return;
        setAssistedSections((prev) =>
          prev.map((s) => (s.id === activeAssistedSection.id ? { ...s, title } : s)),
        );
        setActiveAssistedSection((prev) => (prev ? { ...prev, title } : prev));
      }
    },
    [
      activeAutonomousSection,
      activeHypothesisSection,
      autonomousSubNav,
      activeNav,
      activeAssistedSection,
    ],
  );

  const handleNavChange = useCallback((key: NavKey) => {
    setActiveNav(key);
    if (key === "assisted-research") {
      setWorkflowTree(initialWorkflowTree);
      setActiveNodeId(null);
    }
  }, []);

  // Handle OAuth callback route
  if (isEnterpriseEnabled() && window.location.pathname === "/auth/callback") {
    if (!eeComponents) {
      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-muted-foreground">Loading...</div>
        </div>
      );
    }
    return <eeComponents.AuthCallback />;
  }

  const appContent = (
    <div className="flex min-h-screen flex-col bg-background">
      <header className="h-12 border-b border-border bg-card px-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src="/airas_logo.png" alt="AIRAS logo" className="h-8 w-auto" />
          <p className="text-base font-semibold text-foreground leading-none">AIRAS</p>
        </div>
        <div className="flex items-center gap-4">
          <a
            href="https://github.com/airas-org/airas"
            target="_blank"
            rel="noreferrer"
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="GitHub"
          >
            <SiGithub className="h-6 w-6" />
          </a>
          <a
            href="https://airas-org.github.io/airas/"
            target="_blank"
            rel="noreferrer"
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Documentation"
            title="Documentation"
          >
            <FileText className="h-6 w-6" />
          </a>
          <a
            href="https://discord.gg/KGm5FGY5"
            target="_blank"
            rel="noreferrer"
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="Discord"
          >
            <SiDiscord className="h-6 w-6" />
          </a>
          <a
            href="https://x.com/fuyu_quant"
            target="_blank"
            rel="noreferrer"
            className="text-muted-foreground hover:text-foreground transition-colors"
            aria-label="X"
          >
            <SiX className="h-6 w-6" />
          </a>
          {eeComponents ? (
            <eeComponents.UserMenu />
          ) : (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span aria-disabled="true" className="inline-flex">
                    <button
                      type="button"
                      disabled
                      className="flex items-center gap-2 rounded-md border border-border px-3 py-1.5 text-sm text-muted-foreground opacity-50 cursor-not-allowed"
                    >
                      <UserCircle className="h-5 w-5" />
                      <span>Login</span>
                    </button>
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Enterprise Edition is not enabled</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
      </header>

      <div className="flex flex-1">
        <aside className="w-52 border-r border-border bg-card/60 flex-shrink-0 flex flex-col">
          <div className="flex flex-col gap-1 p-3">
            <button
              type="button"
              disabled
              className="w-full px-3 py-1.5 text-left text-sm border-l-2 text-muted-foreground cursor-not-allowed border-transparent"
            >
              Paper
            </button>
            <button
              type="button"
              disabled
              className="w-full px-3 py-1.5 text-left text-sm border-l-2 text-muted-foreground cursor-not-allowed border-transparent"
            >
              Assisted Research
            </button>
            <button
              type="button"
              onClick={() => setIsAutonomousExpanded((prev) => !prev)}
              aria-expanded={isAutonomousExpanded}
              className={cn(
                "w-full px-3 py-1.5 text-left text-sm transition-colors border-l-2 border-transparent flex items-center justify-between cursor-pointer",
                activeNav === "autonomous-research"
                  ? "text-foreground"
                  : "text-muted-foreground hover:text-foreground hover:bg-muted/40",
              )}
            >
              <span>Autonomous Research</span>
              {isAutonomousExpanded ? (
                <ChevronDown className="h-4 w-4 shrink-0" />
              ) : (
                <ChevronRight className="h-4 w-4 shrink-0" />
              )}
            </button>
            <div
              className={cn(
                "grid transition-all duration-200 ease-in-out",
                isAutonomousExpanded ? "grid-rows-[1fr]" : "grid-rows-[0fr]",
              )}
            >
              <div className="overflow-hidden flex flex-col gap-1">
                <button
                  type="button"
                  onClick={() => {
                    setAutonomousSubNav("topic-driven");
                    handleNavChange("autonomous-research");
                  }}
                  className={cn(
                    "w-full pl-6 pr-3 py-1.5 text-left text-sm transition-colors border-l-2 hover:text-foreground hover:bg-muted/40 cursor-pointer",
                    activeNav === "autonomous-research" && autonomousSubNav === "topic-driven"
                      ? "text-foreground font-semibold border-blue-700"
                      : "text-muted-foreground border-transparent",
                  )}
                >
                  Topic-Driven
                </button>
                <button
                  type="button"
                  onClick={() => {
                    setAutonomousSubNav("hypothesis-driven");
                    handleNavChange("autonomous-research");
                  }}
                  className={cn(
                    "w-full pl-6 pr-3 py-1.5 text-left text-sm transition-colors border-l-2 hover:text-foreground hover:bg-muted/40 cursor-pointer",
                    activeNav === "autonomous-research" && autonomousSubNav === "hypothesis-driven"
                      ? "text-foreground font-semibold border-blue-700"
                      : "text-muted-foreground border-transparent",
                  )}
                >
                  Hypothesis-Driven
                </button>
              </div>
            </div>
          </div>
        </aside>

        {(activeNav === "assisted-research" || activeNav === "autonomous-research") && (
          <div
            className={cn(
              "relative flex-shrink-0 h-full transition-[width] duration-200 ease-in-out",
              sessionsExpanded ? "w-56" : "w-0",
            )}
          >
            <div
              className={cn(
                "overflow-hidden transition-[width,opacity] duration-200 ease-in-out h-full",
                sessionsExpanded ? "w-56 opacity-100" : "w-0 opacity-0",
              )}
            >
              <SectionsSidebar
                sections={
                  activeNav === "autonomous-research"
                    ? autonomousSubNav === "hypothesis-driven"
                      ? hypothesisSections
                      : autonomousSections
                    : assistedSections
                }
                activeSection={
                  activeNav === "autonomous-research"
                    ? autonomousSubNav === "hypothesis-driven"
                      ? activeHypothesisSection
                      : activeAutonomousSection
                    : activeAssistedSection
                }
                onSelectSection={
                  activeNav === "autonomous-research"
                    ? autonomousSubNav === "hypothesis-driven"
                      ? setActiveHypothesisSection
                      : setActiveAutonomousSection
                    : setActiveAssistedSection
                }
              />
            </div>
          </div>
        )}
        <MainContent
          assistedSection={activeAssistedSection}
          autonomousSection={activeAutonomousSection}
          hypothesisSection={activeHypothesisSection}
          activeFeature={activeFeature}
          activeNav={activeNav}
          autonomousSubNav={autonomousSubNav}
          assistedResearchProps={{
            workflowTree,
            activeNodeId,
            setActiveNodeId,
            addWorkflowNode,
            updateNodeSnapshot,
            resetDownstreamSessions,
            onNavigate: handleNavigate,
          }}
          sessionsExpanded={sessionsExpanded}
          onToggleSessions={handleToggleSessions}
          onCreateSection={handleCreateSection}
          onUpdateSectionTitle={handleUpdateSectionTitle}
          onRefreshAutoSessions={fetchAutoSections}
          onRefreshHypothesisSessions={fetchHypothesisSections}
        />
      </div>
    </div>
  );

  if (eeComponents) {
    return <eeComponents.AuthGuard>{appContent}</eeComponents.AuthGuard>;
  }

  return appContent;
}
