// frontend/src/App.tsx

import { SiDiscord, SiGithub, SiX } from "@icons-pack/react-simple-icons";
import * as SubframeCore from "@subframe/core";
import {
  FeatherArrowLeft,
  FeatherBarChart2,
  FeatherBeaker,
  FeatherBell,
  FeatherBookOpen,
  FeatherCheck,
  FeatherCreditCard,
  FeatherExternalLink,
  FeatherGlobe,
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
import { useTranslation } from "react-i18next";
import { Navigate, Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { AUTONOMOUS_SUB_NAVS, type AutonomousSubNav, MainContent } from "@/components/main-content";
import {
  type AutonomousActiveSectionMap,
  type AutonomousSectionsMap,
  useAutonomousResearchSessions,
} from "@/components/pages/autonomous-research/use-autonomous-research-sessions";
import { GitHubOAuthCallback } from "@/components/pages/integration";
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
import { DropdownMenu, IconButton, SidebarWithSections, TopbarWithRightNav } from "@/ui";

// Attach GitHub session header only to GitHub-related generated API calls
OpenAPI.HEADERS = async (options) => {
  const sessionToken = localStorage.getItem("github_session_token");
  const headers: Record<string, string> = {};
  if (
    sessionToken &&
    typeof options?.url === "string" &&
    options.url.toLowerCase().includes("github")
  ) {
    headers["X-GitHub-Session"] = sessionToken;
  }
  return headers;
};

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

const SETTINGS_TABS: SettingsTab[] = [
  "profile",
  "feedback",
  "integration",
  "api-token",
  "user-plan",
  "receipts",
  "usage",
];

function getActiveSection(pathname: string): string {
  if (pathname.startsWith("/autonomous-research")) return "autonomous-research";
  if (pathname.startsWith("/settings")) return "settings";
  if (pathname.startsWith("/verification")) return "verification";
  if (pathname.startsWith("/notifications")) return "notifications";
  if (pathname.startsWith("/papers")) return "papers";
  return "home";
}

function getAutonomousSubNav(pathname: string): AutonomousSubNav {
  if (pathname.includes("hypothesis-driven")) return "hypothesis-driven";
  return "topic-driven";
}

function getSettingsTab(pathname: string): SettingsTab {
  const tab = pathname.split("/settings/")[1] as SettingsTab | undefined;
  if (tab && SETTINGS_TABS.includes(tab)) return tab;
  return "profile";
}

function GitHubOAuthCallbackRoute() {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  const code = params.get("code");
  const state = params.get("state");
  const savedState = sessionStorage.getItem("github_oauth_state");

  if (code && state && state === savedState) {
    return <GitHubOAuthCallback code={code} />;
  }
  return <Navigate to="/" replace />;
}

export default function App() {
  const eeComponents = useEEComponents();
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  const activeSection = getActiveSection(location.pathname);
  const autonomousSubNav = getAutonomousSubNav(location.pathname);

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

  // autonomousListViewKey forces list remount when clicking the same sub-nav
  const [autonomousListViewKey, setAutonomousListViewKey] = useState(0);

  // UI state
  const isMobile = useIsMobile();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    setSidebarOpen(!isMobile);
  }, [isMobile]);

  const { fetchSections } = useAutonomousResearchSessions({
    setAutonomousSectionsMap,
    setAutonomousActiveSectionMap,
  });

  const handleCreateVerification = useCallback(() => {
    const newVerification: Verification = {
      id: `v-${Date.now()}`,
      title: t("verification.detail.newTitle"),
      query: "",
      createdAt: new Date(),
      phase: "initial",
    };
    setVerifications((prev) => [newVerification, ...prev]);
    navigate(`/verification/${newVerification.id}`);
  }, [navigate, t]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: 初回マウント時のみ実行
  useEffect(() => {
    if (location.pathname === "/") {
      handleCreateVerification();
    }
  }, []);

  const handleUpdateVerification = useCallback((id: string, updates: Partial<Verification>) => {
    setVerifications((prev) => prev.map((v) => (v.id === id ? { ...v, ...updates } : v)));
  }, []);

  const handleDeleteVerification = useCallback(
    (id: string) => {
      setVerifications((prev) => prev.filter((v) => v.id !== id));
      if (location.pathname === `/verification/${id}`) {
        navigate("/home");
      }
    },
    [location.pathname, navigate],
  );

  const handleDuplicateVerification = useCallback(
    (id: string) => {
      setVerifications((prev) => {
        const source = prev.find((v) => v.id === id);
        if (!source) return prev;
        const copy: Verification = {
          ...source,
          id: `v-${Date.now()}`,
          title: `${source.title} ${t("verification.detail.copyTitle")}`,
          createdAt: new Date(),
        };
        return [copy, ...prev];
      });
    },
    [t],
  );

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
      navigate(`/verification/${newId}`);
    },
    [navigate],
  );

  const handleSelectAutonomousSession = useCallback(
    (subNav: AutonomousSubNav, section: ResearchSection) => {
      setAutonomousActiveSectionMap((prev) => ({
        ...prev,
        [subNav]: section,
      }));
    },
    [],
  );

  const handleCreateSection = useCallback((subNav: AutonomousSubNav) => {
    setAutonomousActiveSectionMap((prev) => ({ ...prev, [subNav]: null }));
    setWorkflowTree(initialWorkflowTree);
    setActiveNodeId(null);
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
    (subNav: AutonomousSubNav, title: string) => {
      setAutonomousSectionsMap((prev) => ({
        ...prev,
        [subNav]: prev[subNav].map((s) =>
          s.id === autonomousActiveSectionMap[subNav]?.id ? { ...s, title } : s,
        ),
      }));
      setAutonomousActiveSectionMap((prev) => {
        const current = prev[subNav];
        if (!current) return prev;
        return { ...prev, [subNav]: { ...current, title } };
      });
    },
    [autonomousActiveSectionMap],
  );

  const handleMobileNavClose = useCallback(() => {
    if (isMobile) setSidebarOpen(false);
  }, [isMobile]);

  const currentLanguage = (i18n.resolvedLanguage ?? i18n.language)?.toLowerCase().startsWith("ja")
    ? "ja"
    : "en";

  const isSettingsView = activeSection === "settings";

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
                isSettingsView ? "text-brand-700" : "text-neutral-600 hover:bg-neutral-100",
              )}
              onClick={() => navigate("/settings/profile")}
            >
              <FeatherSettings className="h-4 w-4" />
              <span className="text-sm font-medium">{t("nav.settings")}</span>
            </button>
          }
        >
          {isSettingsView ? (
            <>
              <button
                type="button"
                className="flex w-full items-center gap-2 rounded-md px-1 py-1 -mx-1 text-neutral-600 hover:bg-neutral-100 transition-colors cursor-pointer mb-1"
                onClick={() => navigate("/home")}
              >
                <FeatherArrowLeft className="h-4 w-4" />
                <span className="text-sm font-medium">{t("nav.settings")}</span>
              </button>
              <SidebarWithSections.NavSection
                label={<span className="text-sm font-medium">{t("settings.accountSection")}</span>}
              >
                <SidebarWithSections.NavItem
                  icon={<FeatherUser />}
                  selected={getSettingsTab(location.pathname) === "profile"}
                  onClick={() => navigate("/settings/profile")}
                >
                  {t("nav.profile")}
                </SidebarWithSections.NavItem>
              </SidebarWithSections.NavSection>
              <SidebarWithSections.NavSection
                label={<span className="text-sm font-medium">{t("nav.support")}</span>}
              >
                <SidebarWithSections.NavItem
                  icon={<FeatherBookOpen />}
                  selected={false}
                  rightSlot={<FeatherExternalLink className="h-3 w-3 text-neutral-400" />}
                  onClick={() => window.open("https://airas-org.github.io/airas/", "_blank")}
                >
                  {t("nav.docs")}
                </SidebarWithSections.NavItem>
                <SidebarWithSections.NavItem
                  icon={<SiDiscord className="h-4 w-4" />}
                  selected={false}
                  rightSlot={<FeatherExternalLink className="h-3 w-3 text-neutral-400" />}
                  onClick={() => window.open("https://discord.gg/uDmkgKfkes", "_blank")}
                >
                  Discord
                </SidebarWithSections.NavItem>
                <SidebarWithSections.NavItem
                  icon={<FeatherMessageSquare />}
                  selected={getSettingsTab(location.pathname) === "feedback"}
                  onClick={() => navigate("/settings/feedback")}
                >
                  {t("nav.feedback")}
                </SidebarWithSections.NavItem>
              </SidebarWithSections.NavSection>
              <SidebarWithSections.NavSection
                label={
                  <span className="text-sm font-medium">
                    {t("settings.externalServicesSection")}
                  </span>
                }
              >
                <SidebarWithSections.NavItem
                  icon={<FeatherLink />}
                  selected={getSettingsTab(location.pathname) === "integration"}
                  onClick={() => navigate("/settings/integration")}
                >
                  {t("nav.integration")}
                </SidebarWithSections.NavItem>
                <SidebarWithSections.NavItem
                  icon={<FeatherKey />}
                  selected={getSettingsTab(location.pathname) === "api-token"}
                  onClick={() => navigate("/settings/api-token")}
                >
                  {t("userMenu.apiToken")}
                </SidebarWithSections.NavItem>
              </SidebarWithSections.NavSection>
              <SidebarWithSections.NavSection
                label={<span className="text-sm font-medium">{t("nav.userPlan")}</span>}
              >
                <SidebarWithSections.NavItem
                  icon={<FeatherCreditCard />}
                  selected={getSettingsTab(location.pathname) === "user-plan"}
                  onClick={() => navigate("/settings/user-plan")}
                >
                  {t("nav.userPlan")}
                </SidebarWithSections.NavItem>
                <SidebarWithSections.NavItem
                  icon={<FeatherReceipt />}
                  selected={getSettingsTab(location.pathname) === "receipts"}
                  onClick={() => navigate("/settings/receipts")}
                >
                  領収書 / 請求書
                </SidebarWithSections.NavItem>
                <SidebarWithSections.NavItem
                  icon={<FeatherBarChart2 />}
                  selected={getSettingsTab(location.pathname) === "usage"}
                  onClick={() => navigate("/settings/usage")}
                >
                  利用量
                </SidebarWithSections.NavItem>
              </SidebarWithSections.NavSection>
            </>
          ) : (
            <>
              <SidebarWithSections.NavItem
                icon={<FeatherPlus />}
                selected={activeSection === "verification"}
                onClick={() => {
                  handleCreateVerification();
                  handleMobileNavClose();
                }}
              >
                {t("nav.newVerification")}
              </SidebarWithSections.NavItem>
              <SidebarWithSections.NavItem
                icon={<FeatherList />}
                selected={activeSection === "home"}
                onClick={() => {
                  navigate("/home");
                  handleMobileNavClose();
                }}
              >
                {t("nav.verificationList")}
              </SidebarWithSections.NavItem>
              <SidebarWithSections.NavItem
                icon={<FeatherBeaker />}
                selected={activeSection === "autonomous-research"}
                className="cursor-default hover:bg-transparent active:bg-transparent"
              >
                {t("nav.autonomousResearch")}
              </SidebarWithSections.NavItem>
              <div className="flex flex-col gap-0.5 pl-7">
                <button
                  type="button"
                  className={`flex items-center gap-2 rounded-md px-2 py-1 text-xs transition-colors cursor-pointer ${
                    activeSection === "autonomous-research" && autonomousSubNav === "topic-driven"
                      ? "text-brand-700 bg-brand-50"
                      : "text-neutral-600 hover:bg-neutral-100"
                  }`}
                  onClick={() => {
                    setAutonomousListViewKey((k) => k + 1);
                    navigate("/autonomous-research/topic-driven");
                    handleMobileNavClose();
                  }}
                >
                  <span className="inline-block h-1 w-1 rounded-full bg-current" />
                  {t("nav.topicDriven")}
                </button>
                <button
                  type="button"
                  className={`flex items-center gap-2 rounded-md px-2 py-1 text-xs transition-colors cursor-pointer ${
                    activeSection === "autonomous-research" &&
                    autonomousSubNav === "hypothesis-driven"
                      ? "text-brand-700 bg-brand-50"
                      : "text-neutral-600 hover:bg-neutral-100"
                  }`}
                  onClick={() => {
                    setAutonomousListViewKey((k) => k + 1);
                    navigate("/autonomous-research/hypothesis-driven");
                    handleMobileNavClose();
                  }}
                >
                  <span className="inline-block h-1 w-1 rounded-full bg-current" />
                  {t("nav.hypothesisDriven")}
                </button>
              </div>
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
              <SubframeCore.DropdownMenu.Root>
                <SubframeCore.DropdownMenu.Trigger asChild={true}>
                  <IconButton
                    variant="neutral-tertiary"
                    size="medium"
                    icon={<FeatherGlobe />}
                    aria-label={t("app.languageSwitcher.ariaLabel")}
                  />
                </SubframeCore.DropdownMenu.Trigger>
                <SubframeCore.DropdownMenu.Portal>
                  <SubframeCore.DropdownMenu.Content
                    side="bottom"
                    align="end"
                    sideOffset={4}
                    asChild={true}
                  >
                    <DropdownMenu>
                      <DropdownMenu.DropdownItem
                        icon={currentLanguage === "ja" ? <FeatherCheck /> : null}
                        onSelect={() => i18n.changeLanguage("ja")}
                      >
                        🇯🇵 日本語
                      </DropdownMenu.DropdownItem>
                      <DropdownMenu.DropdownItem
                        icon={currentLanguage === "en" ? <FeatherCheck /> : null}
                        onSelect={() => i18n.changeLanguage("en")}
                      >
                        🇺🇸 English
                      </DropdownMenu.DropdownItem>
                    </DropdownMenu>
                  </SubframeCore.DropdownMenu.Content>
                </SubframeCore.DropdownMenu.Portal>
              </SubframeCore.DropdownMenu.Root>
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
                variant={
                  activeSection === "notifications" ? "neutral-secondary" : "neutral-tertiary"
                }
                icon={<FeatherBell className="h-4 w-4" />}
                onClick={() => navigate("/notifications")}
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
            autonomousSectionMap={autonomousActiveSectionMap}
            autonomousSessions={autonomousSectionsMap}
            onSelectAutonomousSession={handleSelectAutonomousSession}
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
            onRefreshSessions={(subNav, preferredId) => fetchSections(subNav, preferredId)}
            verifications={verifications}
            onDeleteVerification={handleDeleteVerification}
            onDuplicateVerification={handleDuplicateVerification}
            onUpdateVerification={handleUpdateVerification}
            onCreateWithMethod={handleCreateWithMethod}
            autonomousListViewKey={autonomousListViewKey}
          />
        </div>
      </div>
    </div>
  );

  const guardedContent = eeComponents ? (
    <eeComponents.AuthGuard>{appContent}</eeComponents.AuthGuard>
  ) : (
    appContent
  );

  return (
    <Routes>
      <Route path="/auth/github/callback" element={<GitHubOAuthCallbackRoute />} />
      {isEnterpriseEnabled() && (
        <Route
          path="/auth/callback"
          element={
            eeComponents ? (
              <eeComponents.AuthCallback />
            ) : (
              <div className="flex min-h-screen items-center justify-center">
                <div className="text-muted-foreground">{t("common.loading")}</div>
              </div>
            )
          }
        />
      )}
      <Route path="*" element={guardedContent} />
    </Routes>
  );
}
