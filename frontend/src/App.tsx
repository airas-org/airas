// frontend/src/App.tsx

import { SiDiscord, SiGithub, SiX } from "@icons-pack/react-simple-icons";
import * as SubframeCore from "@subframe/core";
import {
  FeatherBell,
  FeatherChevronUp,
  FeatherFileText,
  FeatherHelpCircle,
  FeatherHome,
  FeatherKey,
  FeatherList,
  FeatherLogOut,
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
import { useTranslation } from "react-i18next";
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
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { isEnterpriseEnabled } from "@/ee/config";
import { useIsMobile } from "@/hooks/use-mobile";
import { OpenAPI } from "@/lib/api";
import { cn } from "@/lib/utils";
import type { FeatureType, ResearchSection, WorkflowNode, WorkflowTree } from "@/types/research";
import { Avatar, DropdownMenu, IconButton, SidebarWithSections, TopbarWithRightNav } from "@/ui";

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
  const { t, i18n } = useTranslation();

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
      title: t("verification.detail.newTitle"),
      query: "",
      createdAt: new Date(),
      phase: "initial",
    };
    setVerifications((prev) => [newVerification, ...prev]);
    setActiveVerificationId(newVerification.id);
    setActiveNav("verification");
  }, [t]);

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

  const toggleLanguage = useCallback(() => {
    i18n.changeLanguage(i18n.language === "ja" ? "en" : "ja");
  }, [i18n]);

  // Handle OAuth callback route
  if (isEnterpriseEnabled() && window.location.pathname === "/auth/callback") {
    if (!eeComponents) {
      return (
        <div className="flex min-h-screen items-center justify-center">
          <div className="text-muted-foreground">{t("common.loading")}</div>
        </div>
      );
    }
    return <eeComponents.AuthCallback />;
  }

  const appContent = (
    <div className="flex min-h-screen bg-default-background">
      <aside
        className={cn(
          "fixed left-0 top-0 h-screen transition-[width] duration-200 ease-in-out overflow-hidden",
          sidebarOpen ? "w-60" : "w-0",
          isMobile ? "z-40" : "z-30",
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
            <SubframeCore.DropdownMenu.Root>
              <SubframeCore.DropdownMenu.Trigger asChild>
                <button
                  type="button"
                  className="flex w-full items-center gap-3 rounded-md px-1 py-1 -mx-1 hover:bg-neutral-100 transition-colors cursor-pointer"
                >
                  <Avatar variant="brand" size="small">
                    Dev
                  </Avatar>
                  <span className="flex-1 text-body font-body text-default-font text-left">
                    {t("userMenu.developer")}
                  </span>
                  <FeatherChevronUp className="h-4 w-4 text-subtext-color" />
                </button>
              </SubframeCore.DropdownMenu.Trigger>
              <SubframeCore.DropdownMenu.Portal>
                <SubframeCore.DropdownMenu.Content side="top" align="start" sideOffset={8}>
                  <DropdownMenu>
                    <DropdownMenu.DropdownItem
                      icon={<FeatherUser />}
                      onSelect={() => {
                        handleNavChange("profile");
                        handleMobileNavClose();
                      }}
                    >
                      {t("userMenu.profile")}
                    </DropdownMenu.DropdownItem>
                    <DropdownMenu.DropdownItem
                      icon={<FeatherKey />}
                      onSelect={() => {
                        handleNavChange("api-token");
                        handleMobileNavClose();
                      }}
                    >
                      {t("userMenu.apiToken")}
                    </DropdownMenu.DropdownItem>
                    <DropdownMenu.DropdownItem
                      icon={<FeatherSettings />}
                      onSelect={() => {
                        handleNavChange("integration");
                        handleMobileNavClose();
                      }}
                    >
                      {t("userMenu.integration")}
                    </DropdownMenu.DropdownItem>
                    <DropdownMenu.DropdownDivider />
                    <DropdownMenu.DropdownItem icon={<FeatherLogOut />}>
                      {t("userMenu.logout")}
                    </DropdownMenu.DropdownItem>
                  </DropdownMenu>
                </SubframeCore.DropdownMenu.Content>
              </SubframeCore.DropdownMenu.Portal>
            </SubframeCore.DropdownMenu.Root>
          }
        >
          <SidebarWithSections.NavItem
            icon={<FeatherHome />}
            selected={activeNav === "dashboard"}
            onClick={() => {
              handleNavChange("dashboard");
              handleMobileNavClose();
            }}
          >
            {t("nav.dashboard")}
          </SidebarWithSections.NavItem>
          <SidebarWithSections.NavItem
            icon={<FeatherPlus />}
            onClick={() => {
              handleCreateVerification();
              handleMobileNavClose();
            }}
            className="bg-brand-50"
          >
            {t("nav.newVerification")}
          </SidebarWithSections.NavItem>
          <SidebarWithSections.NavItem
            icon={<FeatherList />}
            selected={activeNav === "home"}
            onClick={() => {
              handleNavChange("home");
              handleMobileNavClose();
            }}
          >
            {t("nav.verificationList")}
          </SidebarWithSections.NavItem>
          <SidebarWithSections.NavItem
            icon={<FeatherSearch />}
            selected={activeNav === "search"}
            onClick={() => {
              handleNavChange("search");
              handleMobileNavClose();
            }}
          >
            {t("nav.search")}
          </SidebarWithSections.NavItem>
          <SidebarWithSections.NavItem
            icon={<FeatherBell />}
            selected={activeNav === "notifications"}
            onClick={() => {
              handleNavChange("notifications");
              handleMobileNavClose();
            }}
          >
            {t("nav.notifications")}
          </SidebarWithSections.NavItem>
          <SidebarWithSections.NavSection
            label={
              <>
                {t("nav.autonomousResearch")}{" "}
                <span className="text-[10px] font-normal text-neutral-400">
                  {t("nav.experimental")}
                </span>
              </>
            }
          >
            <SidebarWithSections.NavItem
              icon={<span className="inline-block h-1.5 w-1.5 rounded-full bg-current" />}
              selected={activeNav === "autonomous-research" && autonomousSubNav === "topic-driven"}
              onClick={() => {
                setAutonomousSubNav("topic-driven");
                handleNavChange("autonomous-research");
                handleMobileNavClose();
              }}
            >
              {t("nav.topicDriven")}
            </SidebarWithSections.NavItem>
            <SidebarWithSections.NavItem
              icon={<span className="inline-block h-1.5 w-1.5 rounded-full bg-current" />}
              selected={
                activeNav === "autonomous-research" && autonomousSubNav === "hypothesis-driven"
              }
              onClick={() => {
                setAutonomousSubNav("hypothesis-driven");
                handleNavChange("autonomous-research");
                handleMobileNavClose();
              }}
            >
              {t("nav.hypothesisDriven")}
            </SidebarWithSections.NavItem>
          </SidebarWithSections.NavSection>
          <SidebarWithSections.NavSection label={t("nav.settings")}>
            <SidebarWithSections.NavItem
              icon={<FeatherSettings />}
              selected={activeNav === "integration"}
              onClick={() => {
                handleNavChange("integration");
                handleMobileNavClose();
              }}
            >
              {t("nav.integration")}
            </SidebarWithSections.NavItem>
            <SidebarWithSections.NavItem
              icon={<FeatherUser />}
              selected={activeNav === "user-plan"}
              onClick={() => {
                handleNavChange("user-plan");
                handleMobileNavClose();
              }}
            >
              {t("nav.userPlan")}
            </SidebarWithSections.NavItem>
            <SidebarWithSections.NavItem
              icon={<FeatherUser />}
              selected={activeNav === "profile"}
              onClick={() => {
                handleNavChange("profile");
                handleMobileNavClose();
              }}
            >
              {t("nav.profile")}
            </SidebarWithSections.NavItem>
          </SidebarWithSections.NavSection>
          <SidebarWithSections.NavSection label={t("nav.support")}>
            <SidebarWithSections.NavItem
              icon={<FeatherMessageSquare />}
              selected={activeNav === "feedback"}
              onClick={() => {
                handleNavChange("feedback");
                handleMobileNavClose();
              }}
            >
              {t("nav.feedback")}
            </SidebarWithSections.NavItem>
            <SidebarWithSections.NavItem
              icon={<FeatherHelpCircle />}
              selected={activeNav === "help"}
              onClick={() => {
                handleNavChange("help");
                handleMobileNavClose();
              }}
            >
              {t("nav.help")}
            </SidebarWithSections.NavItem>
            <SidebarWithSections.NavItem
              icon={<FeatherFileText />}
              onClick={() => window.open("https://airas-org.github.io/airas/", "_blank")}
            >
              {t("nav.docs")}
            </SidebarWithSections.NavItem>
            <SidebarWithSections.NavItem
              icon={<FeatherShield />}
              selected={activeNav === "legal"}
              onClick={() => {
                handleNavChange("legal");
                handleMobileNavClose();
              }}
            >
              {t("nav.legal")}
            </SidebarWithSections.NavItem>
          </SidebarWithSections.NavSection>
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
          "flex-1 flex flex-col min-w-0 transition-[margin-left] duration-200 ease-in-out",
          !isMobile && sidebarOpen ? "ml-60" : "ml-0",
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
                <button
                  type="button"
                  onClick={toggleLanguage}
                  className="text-caption font-caption text-subtext-color hover:text-default-font px-2 py-1 rounded border border-neutral-border hover:bg-neutral-100 transition-colors"
                >
                  {t("languageToggle.switchTo")}
                </button>
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
              </div>
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
