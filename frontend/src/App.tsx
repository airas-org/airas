// frontend/src/App.tsx

import { SiDiscord, SiGithub, SiX } from "@icons-pack/react-simple-icons";
import {
  FeatherArrowLeft,
  FeatherBarChart2,
  FeatherBell,
  FeatherBookOpen,
  FeatherCreditCard,
  FeatherExternalLink,
  FeatherKey,
  FeatherLink,
  FeatherList,
  FeatherMessageSquare,
  FeatherPanelLeftClose,
  FeatherPanelLeftOpen,
  FeatherPlus,
  FeatherReceipt,
  FeatherSettings,
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
import type { SettingsTab } from "@/components/pages/settings";
import {
  mockVerifications,
  type ProposedMethod,
  type Verification,
} from "@/components/pages/verification";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { isEnterpriseEnabled } from "@/ee/config";
import { useIsMobile } from "@/hooks/use-mobile";
import { OpenAPI } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { FeatureType, ResearchSection, WorkflowNode, WorkflowTree } from "@/types/research";
import { IconButton, SidebarWithSections, TopbarWithRightNav } from "@/ui";

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
    if (nav === "user-plan" || nav === "integration") return "settings" as NavKey;
    return "verification";
  });
  const [autonomousSubNav, setAutonomousSubNav] = useState<AutonomousSubNav>("topic-driven");
  const [settingsTab, setSettingsTab] = useState<SettingsTab>("profile");
  const isMobile = useIsMobile();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [showOnboarding, setShowOnboarding] = useState(() => {
    return !localStorage.getItem("airas-onboarding-done");
  });

  useEffect(() => {
    setSidebarOpen(!isMobile);
  }, [isMobile]);

  const { fetchSections } = useAutonomousResearchSessions({
    setAutonomousSectionsMap,
    setAutonomousActiveSectionMap,
  });

  // 初回起動時に新規検証を自動作成
  // biome-ignore lint/correctness/useExhaustiveDependencies: 初回マウント時のみ実行
  useEffect(() => {
    if (activeNav === "verification" && !activeVerificationId) {
      handleCreateVerification();
    }
  }, []);

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

  const handleSelectAutonomousSession = useCallback(
    (section: ResearchSection) => {
      setAutonomousActiveSectionMap((prev) => ({
        ...prev,
        [autonomousSubNav]: section,
      }));
    },
    [autonomousSubNav],
  );

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

  const handleMobileNavClose = useCallback(() => {
    if (isMobile) setSidebarOpen(false);
  }, [isMobile]);

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
          "fixed left-0 top-0 h-screen bg-default-background transition-[width] duration-200 ease-in-out overflow-hidden",
          sidebarOpen ? "w-52" : "w-0",
          isMobile ? "z-40" : "z-30",
        )}
      >
        <SidebarWithSections
          className="min-w-[13rem]"
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
            <button
              type="button"
              className={cn(
                "flex w-full items-center gap-2.5 rounded-md px-1 py-1 -mx-1 transition-colors cursor-pointer",
                activeNav === "settings"
                  ? "text-brand-700"
                  : "text-neutral-600 hover:bg-neutral-100",
              )}
              onClick={() => handleNavChange("settings")}
            >
              <FeatherSettings className="h-4 w-4" />
              <span className="text-sm font-medium">設定</span>
            </button>
          }
        >
          {activeNav === "settings" ? (
            <>
              <button
                type="button"
                className="flex w-full items-center gap-2 rounded-md px-1 py-1 -mx-1 text-neutral-600 hover:bg-neutral-100 transition-colors cursor-pointer mb-1"
                onClick={() => handleNavChange("home")}
              >
                <FeatherArrowLeft className="h-4 w-4" />
                <span className="text-sm font-medium">設定</span>
              </button>
              <SidebarWithSections.NavSection label="アカウント">
                <SidebarWithSections.NavItem
                  icon={<FeatherUser />}
                  selected={settingsTab === "profile"}
                  onClick={() => setSettingsTab("profile")}
                >
                  プロフィール
                </SidebarWithSections.NavItem>
              </SidebarWithSections.NavSection>
              <SidebarWithSections.NavSection label="サポート">
                <SidebarWithSections.NavItem
                  icon={<FeatherBookOpen />}
                  selected={false}
                  rightSlot={<FeatherExternalLink className="h-3 w-3 text-neutral-400" />}
                  onClick={() => window.open("https://airas-org.github.io/airas/", "_blank")}
                >
                  ドキュメント
                </SidebarWithSections.NavItem>
                <SidebarWithSections.NavItem
                  icon={<SiDiscord className="h-4 w-4" />}
                  selected={false}
                  rightSlot={<FeatherExternalLink className="h-3 w-3 text-neutral-400" />}
                  onClick={() => window.open("https://discord.gg/KGm5FGY5", "_blank")}
                >
                  Discord
                </SidebarWithSections.NavItem>
                <SidebarWithSections.NavItem
                  icon={<FeatherMessageSquare />}
                  selected={settingsTab === "feedback"}
                  onClick={() => setSettingsTab("feedback")}
                >
                  お問い合わせ
                </SidebarWithSections.NavItem>
              </SidebarWithSections.NavSection>
              <SidebarWithSections.NavSection label="AIRASのリソース">
                <SidebarWithSections.NavItem
                  icon={<FeatherLink />}
                  selected={settingsTab === "integration"}
                  onClick={() => setSettingsTab("integration")}
                >
                  接続
                </SidebarWithSections.NavItem>
                <SidebarWithSections.NavItem
                  icon={<FeatherKey />}
                  selected={settingsTab === "api-token"}
                  onClick={() => setSettingsTab("api-token")}
                >
                  シークレット
                </SidebarWithSections.NavItem>
              </SidebarWithSections.NavSection>
              <SidebarWithSections.NavSection label="支払い">
                <SidebarWithSections.NavItem
                  icon={<FeatherCreditCard />}
                  selected={settingsTab === "user-plan"}
                  onClick={() => setSettingsTab("user-plan")}
                >
                  プラン
                </SidebarWithSections.NavItem>
                <SidebarWithSections.NavItem
                  icon={<FeatherReceipt />}
                  selected={settingsTab === "receipts"}
                  onClick={() => setSettingsTab("receipts")}
                >
                  領収書 / 請求書
                </SidebarWithSections.NavItem>
                <SidebarWithSections.NavItem
                  icon={<FeatherBarChart2 />}
                  selected={settingsTab === "usage"}
                  onClick={() => setSettingsTab("usage")}
                >
                  利用量
                </SidebarWithSections.NavItem>
              </SidebarWithSections.NavSection>
            </>
          ) : (
            <>
              <SidebarWithSections.NavItem
                icon={<FeatherPlus />}
                selected={activeNav === "verification"}
                onClick={() => {
                  handleCreateVerification();
                  handleMobileNavClose();
                }}
              >
                新規検証
              </SidebarWithSections.NavItem>
              <SidebarWithSections.NavItem
                icon={<FeatherList />}
                selected={activeNav === "home"}
                onClick={() => {
                  handleNavChange("home");
                  handleMobileNavClose();
                }}
              >
                検証一覧
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
                  selected={
                    activeNav === "autonomous-research" && autonomousSubNav === "topic-driven"
                  }
                  onClick={() => {
                    setAutonomousSubNav("topic-driven");
                    setAutonomousActiveSectionMap((prev) => ({ ...prev, "topic-driven": null }));
                    handleNavChange("autonomous-research");
                    handleMobileNavClose();
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
                    setAutonomousActiveSectionMap((prev) => ({
                      ...prev,
                      "hypothesis-driven": null,
                    }));
                    handleNavChange("autonomous-research");
                    handleMobileNavClose();
                  }}
                >
                  Hypothesis-Driven
                </SidebarWithSections.NavItem>
              </SidebarWithSections.NavSection>
            </>
          )}
        </SidebarWithSections>
      </aside>

      {isMobile && sidebarOpen && (
        <button
          type="button"
          aria-label="Close sidebar"
          className="fixed inset-0 z-20 bg-black/50 transition-opacity cursor-default"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div
        className={cn(
          "flex-1 flex flex-col min-w-0 overflow-x-clip transition-[margin-left] duration-200 ease-in-out",
          !isMobile && sidebarOpen ? "ml-52" : "ml-0",
        )}
      >
        <TopbarWithRightNav
          leftSlot={
            !sidebarOpen || isMobile ? (
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
              <div className="hidden md:flex items-center gap-4">
                <IconButton
                  variant="neutral-tertiary"
                  icon={<SiGithub className="h-4 w-4" />}
                  onClick={() => window.open("https://github.com/airas-org/airas", "_blank")}
                />
                <IconButton
                  variant="neutral-tertiary"
                  icon={<SiX className="h-4 w-4" />}
                  onClick={() => window.open("https://x.com/fuyu_quant", "_blank")}
                />
              </div>
              <IconButton
                variant={activeNav === "notifications" ? "neutral-secondary" : "neutral-tertiary"}
                icon={<FeatherBell className="h-4 w-4" />}
                onClick={() => handleNavChange("notifications")}
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
          <MainContent
            autonomousSection={autonomousActiveSectionMap[autonomousSubNav]}
            autonomousSessions={autonomousSectionsMap[autonomousSubNav]}
            onSelectAutonomousSession={handleSelectAutonomousSession}
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
            settingsTab={settingsTab}
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
