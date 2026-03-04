// frontend/src/App.tsx

import { SiDiscord, SiGithub, SiX } from "@icons-pack/react-simple-icons";
import {
  FeatherBell,
  FeatherFileText,
  FeatherHelpCircle,
  FeatherHome,
  FeatherList,
  FeatherMessageSquare,
  FeatherPanelLeftClose,
  FeatherPanelLeftOpen,
  FeatherPlus,
  FeatherSearch,
  FeatherSettings,
  FeatherShield,
  FeatherUser,
} from "@subframe/core";
import axios from "axios";
import { useCallback, useEffect, useState } from "react";
import {
  AUTONOMOUS_SUB_NAVS,
  type AutonomousSubNav,
  MainContent,
  type NavKey,
} from "@/components/main-content";
import {
  type AutonomousActiveSectionMap,
  type AutonomousSectionsMap,
  useAutonomousResearchSessions,
} from "@/components/pages/autonomous-research/use-autonomous-research-sessions";
import { OnboardingOverlay } from "@/components/pages/onboarding";
import {
  mockVerifications,
  type ProposedMethod,
  type Verification,
} from "@/components/pages/verification";
import { SectionsSidebar } from "@/components/sections-sidebar";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { isEnterpriseEnabled } from "@/ee/config";
import { OpenAPI } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { FeatureType, WorkflowNode, WorkflowTree } from "@/types/research";
import { Avatar, IconButton, SidebarWithSections, TopbarWithRightNav } from "@/ui";

const initialWorkflowTree: WorkflowTree = {
  nodes: {},
  rootId: null,
  activeNodeId: null,
};

const initialAutonomousSectionsMap = AUTONOMOUS_SUB_NAVS.reduce<AutonomousSectionsMap>(
  (acc, nav) => {
    acc[nav] = [];
    return acc;
  },
  {} as AutonomousSectionsMap,
);

const initialAutonomousActiveSectionMap = AUTONOMOUS_SUB_NAVS.reduce<AutonomousActiveSectionMap>(
  (acc, nav) => {
    acc[nav] = null;
    return acc;
  },
  {} as AutonomousActiveSectionMap,
);

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
      // Set token resolver for the OpenAPI generated client
      OpenAPI.TOKEN = interceptor.openApiTokenResolver;
      // Also keep axios interceptor for any direct axios calls
      axios.interceptors.request.use(interceptor.authRequestInterceptor);
      setEeComponents({
        AuthGuard: authGuard.AuthGuard,
        UserMenu: userMenu.UserMenu,
        AuthCallback: authCallback.AuthCallback,
      });
    });
  }, []);

  return eeComponents;
}

export default function App() {
  const eeComponents = useEEComponents();

  // Autonomous Research
  const [autonomousSectionsMap, setAutonomousSectionsMap] = useState<AutonomousSectionsMap>(
    initialAutonomousSectionsMap,
  );
  const [autonomousActiveSectionMap, setAutonomousActiveSectionMap] =
    useState<AutonomousActiveSectionMap>(initialAutonomousActiveSectionMap);

  // Workflow
  const [workflowTree, setWorkflowTree] = useState<WorkflowTree>(initialWorkflowTree);
  const [activeNodeId, setActiveNodeId] = useState<string | null>(null);

  // Verification
  const [verifications, setVerifications] = useState<Verification[]>(mockVerifications);
  const [activeVerificationId, setActiveVerificationId] = useState<string | null>(null);
  const activeVerification = verifications.find((v) => v.id === activeVerificationId) ?? null;

  // Navigation — check URL params for post-checkout redirect
  const [activeNav, setActiveNav] = useState<NavKey>(() => {
    const params = new URLSearchParams(window.location.search);
    const nav = params.get("nav");
    if (nav === "user-plan" || nav === "integration") return nav;
    return "home";
  });
  const [autonomousSubNav, setAutonomousSubNav] = useState<AutonomousSubNav>("topic-driven");
  const [sessionsExpanded, setSessionsExpanded] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [showOnboarding, setShowOnboarding] = useState(() => {
    return !localStorage.getItem("airas-onboarding-done");
  });

  const { fetchSections } = useAutonomousResearchSessions({
    setAutonomousSectionsMap,
    setAutonomousActiveSectionMap,
  });

  const handleCreateSection = () => {
    if (activeNav === "autonomous-research") {
      setAutonomousActiveSectionMap((prev) => ({ ...prev, [autonomousSubNav]: null }));
    }
    setWorkflowTree(initialWorkflowTree);
    setActiveNodeId(null);
  };

  const handleCreateVerification = useCallback(() => {
    const newVerification: Verification = {
      id: `v-${Date.now()}`,
      title: "新規検証",
      query: "",
      createdAt: new Date(),
      phase: "initial",
    };
    setVerifications((prev) => [newVerification, ...prev]);
    setActiveVerificationId(newVerification.id);
    setActiveNav("verification");
  }, []);

  const handleSelectVerification = useCallback((id: string) => {
    setActiveVerificationId(id);
    setActiveNav("verification");
  }, []);

  const handleUpdateVerification = useCallback((id: string, updates: Partial<Verification>) => {
    setVerifications((prev) => prev.map((v) => (v.id === id ? { ...v, ...updates } : v)));
  }, []);

  const handleDeleteVerification = useCallback(
    (id: string) => {
      setVerifications((prev) => prev.filter((v) => v.id !== id));
      if (activeVerificationId === id) {
        setActiveVerificationId(null);
        setActiveNav("home");
      }
    },
    [activeVerificationId],
  );

  const handleDuplicateVerification = useCallback((id: string) => {
    setVerifications((prev) => {
      const source = prev.find((v) => v.id === id);
      if (!source) return prev;
      const copy: Verification = {
        ...source,
        id: `v-${Date.now()}`,
        title: `${source.title} (コピー)`,
        createdAt: new Date(),
      };
      return [copy, ...prev];
    });
  }, []);

  const handleCreateWithMethod = useCallback(
    (sourceVerification: Verification, method: ProposedMethod) => {
      const newId = `v-${Date.now()}`;
      const newVerification: Verification = {
        id: newId,
        title: method.title,
        query: sourceVerification.query,
        createdAt: new Date(),
        phase: "plan-generated",
        proposedMethods: [method],
        selectedMethodId: method.id,
        plan: {
          whatToVerify: method.whatToVerify,
          method: method.method,
        },
      };
      setVerifications((prev) => [newVerification, ...prev]);
      setActiveVerificationId(newId);
      setActiveNav("verification");
    },
    [],
  );

  const handleToggleSessions = useCallback(() => {
    setSessionsExpanded((prev) => !prev);
  }, []);

  const handleNavigate = useCallback(
    (nodeId: string) => {
      const node = workflowTree.nodes[nodeId];
      if (node) {
        setActiveNodeId(nodeId);
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
        setAutonomousSectionsMap((prev) => ({
          ...prev,
          [autonomousSubNav]: prev[autonomousSubNav].map((s) =>
            s.id === autonomousActiveSectionMap[autonomousSubNav]?.id ? { ...s, title } : s,
          ),
        }));
        setAutonomousActiveSectionMap((prev) => {
          const current = prev[autonomousSubNav];
          if (!current) return prev;
          return { ...prev, [autonomousSubNav]: { ...current, title } };
        });
      }
    },
    [activeNav, autonomousSubNav, autonomousActiveSectionMap],
  );

  const handleNavChange = useCallback((key: NavKey) => {
    setActiveNav(key);
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
    <div className="flex min-h-screen bg-default-background">
      <aside
        className={cn(
          "fixed left-0 top-0 h-screen z-30 transition-[width] duration-200 ease-in-out overflow-hidden",
          sidebarOpen ? "w-60" : "w-0",
        )}
      >
        <SidebarWithSections
          className="min-w-[15rem]"
          header={
            <div className="flex w-full items-center justify-between">
              <div className="flex items-center gap-3">
                <img src="/airas_logo.png" alt="AIRAS logo" className="h-7 w-auto" />
                <span className="text-heading-3 font-heading-3 text-default-font">AIRAS</span>
              </div>
              <IconButton
                size="small"
                variant="neutral-tertiary"
                icon={<FeatherPanelLeftClose />}
                onClick={() => setSidebarOpen(false)}
              />
            </div>
          }
          footer={
            <div className="flex w-full items-center gap-3">
              <Avatar variant="neutral" size="small">
                G
              </Avatar>
              <span className="text-body font-body text-default-font">Guest</span>
            </div>
          }
        >
          <SidebarWithSections.NavItem
            icon={<FeatherHome />}
            selected={activeNav === "dashboard"}
            onClick={() => handleNavChange("dashboard")}
          >
            ダッシュボード
          </SidebarWithSections.NavItem>
          <SidebarWithSections.NavItem
            icon={<FeatherPlus />}
            onClick={handleCreateVerification}
            className="bg-brand-50"
          >
            新規検証
          </SidebarWithSections.NavItem>
          <SidebarWithSections.NavItem
            icon={<FeatherList />}
            selected={activeNav === "home"}
            onClick={() => handleNavChange("home")}
          >
            検証一覧
          </SidebarWithSections.NavItem>
          <SidebarWithSections.NavItem
            icon={<FeatherSearch />}
            selected={activeNav === "search"}
            onClick={() => handleNavChange("search")}
          >
            検索
          </SidebarWithSections.NavItem>
          <SidebarWithSections.NavItem
            icon={<FeatherBell />}
            selected={activeNav === "notifications"}
            onClick={() => handleNavChange("notifications")}
          >
            通知
          </SidebarWithSections.NavItem>
          <SidebarWithSections.NavSection
            label={
              <>
                自動研究{" "}
                <span className="text-[10px] font-normal text-neutral-400">Experimental</span>
              </>
            }
          >
            <SidebarWithSections.NavItem
              icon={<span className="inline-block h-1.5 w-1.5 rounded-full bg-current" />}
              selected={activeNav === "autonomous-research" && autonomousSubNav === "topic-driven"}
              onClick={() => {
                setAutonomousSubNav("topic-driven");
                handleNavChange("autonomous-research");
              }}
            >
              Topic-Driven
            </SidebarWithSections.NavItem>
            <SidebarWithSections.NavItem
              icon={<span className="inline-block h-1.5 w-1.5 rounded-full bg-current" />}
              selected={
                activeNav === "autonomous-research" && autonomousSubNav === "hypothesis-driven"
              }
              onClick={() => {
                setAutonomousSubNav("hypothesis-driven");
                handleNavChange("autonomous-research");
              }}
            >
              Hypothesis-Driven
            </SidebarWithSections.NavItem>
          </SidebarWithSections.NavSection>
          <SidebarWithSections.NavSection label="Settings">
            <SidebarWithSections.NavItem
              icon={<FeatherSettings />}
              selected={activeNav === "integration"}
              onClick={() => handleNavChange("integration")}
            >
              Integration
            </SidebarWithSections.NavItem>
            <SidebarWithSections.NavItem
              icon={<FeatherUser />}
              selected={activeNav === "user-plan"}
              onClick={() => handleNavChange("user-plan")}
            >
              User Plan
            </SidebarWithSections.NavItem>
            <SidebarWithSections.NavItem
              icon={<FeatherUser />}
              selected={activeNav === "profile"}
              onClick={() => handleNavChange("profile")}
            >
              プロフィール
            </SidebarWithSections.NavItem>
          </SidebarWithSections.NavSection>
          <SidebarWithSections.NavSection label="Support">
            <SidebarWithSections.NavItem
              icon={<FeatherMessageSquare />}
              selected={activeNav === "feedback"}
              onClick={() => handleNavChange("feedback")}
            >
              お問い合わせ
            </SidebarWithSections.NavItem>
            <SidebarWithSections.NavItem
              icon={<FeatherHelpCircle />}
              onClick={() => window.open("https://airas-org.github.io/airas/", "_blank")}
            >
              ヘルプ・ドキュメント
            </SidebarWithSections.NavItem>
            <SidebarWithSections.NavItem
              icon={<FeatherShield />}
              selected={activeNav === "legal"}
              onClick={() => handleNavChange("legal")}
            >
              利用規約
            </SidebarWithSections.NavItem>
          </SidebarWithSections.NavSection>
        </SidebarWithSections>
      </aside>

      <div
        className={cn(
          "flex-1 flex flex-col min-w-0 transition-[margin-left] duration-200 ease-in-out",
          sidebarOpen ? "ml-60" : "ml-0",
        )}
      >
        <TopbarWithRightNav
          leftSlot={
            !sidebarOpen ? (
              <IconButton
                size="small"
                variant="neutral-tertiary"
                icon={<FeatherPanelLeftOpen />}
                onClick={() => setSidebarOpen(true)}
              />
            ) : undefined
          }
          rightSlot={
            <>
              <IconButton
                variant="neutral-tertiary"
                icon={<SiGithub className="h-4 w-4" />}
                onClick={() => window.open("https://github.com/airas-org/airas", "_blank")}
              />
              <IconButton
                variant="neutral-tertiary"
                icon={<FeatherFileText />}
                onClick={() => window.open("https://airas-org.github.io/airas/", "_blank")}
              />
              <IconButton
                variant="neutral-tertiary"
                icon={<SiDiscord className="h-4 w-4" />}
                onClick={() => window.open("https://discord.gg/KGm5FGY5", "_blank")}
              />
              <IconButton
                variant="neutral-tertiary"
                icon={<SiX className="h-4 w-4" />}
                onClick={() => window.open("https://x.com/fuyu_quant", "_blank")}
              />
              {eeComponents ? (
                <eeComponents.UserMenu />
              ) : (
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <span>
                        <IconButton disabled variant="neutral-secondary" icon={<FeatherUser />} />
                      </span>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Enterprise Edition is not enabled</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              )}
            </>
          }
        />
        <div className="flex-1 flex min-h-0">
          {activeNav === "autonomous-research" && (
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
                  sections={autonomousSectionsMap[autonomousSubNav]}
                  activeSection={autonomousActiveSectionMap[autonomousSubNav]}
                  onSelectSection={(section) =>
                    setAutonomousActiveSectionMap((prev) => ({
                      ...prev,
                      [autonomousSubNav]: section,
                    }))
                  }
                />
              </div>
            </div>
          )}
          <MainContent
            autonomousSection={autonomousActiveSectionMap[autonomousSubNav]}
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
            onRefreshSessions={(preferredId) => fetchSections(autonomousSubNav, preferredId)}
            verifications={verifications}
            activeVerification={activeVerification}
            onSelectVerification={handleSelectVerification}
            onDeleteVerification={handleDeleteVerification}
            onDuplicateVerification={handleDuplicateVerification}
            onUpdateVerification={handleUpdateVerification}
            onCreateWithMethod={handleCreateWithMethod}
            onNavChange={handleNavChange}
          />
        </div>
      </div>
    </div>
  );

  const handleOnboardingComplete = () => {
    localStorage.setItem("airas-onboarding-done", "true");
    setShowOnboarding(false);
  };

  const content = (
    <>
      {appContent}
      {showOnboarding && <OnboardingOverlay onComplete={handleOnboardingComplete} />}
    </>
  );

  if (eeComponents) {
    return <eeComponents.AuthGuard>{content}</eeComponents.AuthGuard>;
  }

  return content;
}
