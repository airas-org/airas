import { SiGithub, SiX } from "@icons-pack/react-simple-icons";
import * as SubframeCore from "@subframe/core";
import {
  FeatherBell,
  FeatherCheck,
  FeatherGlobe,
  FeatherPanelLeftClose,
  FeatherPanelLeftOpen,
  FeatherUser,
} from "@subframe/core";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";
import {
  AUTONOMOUS_SUB_NAVS,
  type AutonomousSubNav,
  getAutonomousSubNav,
  MainContent,
} from "@/components/main-content";
import {
  type AutonomousActiveSectionMap,
  type AutonomousSectionsMap,
  useAutonomousResearchSessions,
} from "@/components/pages/autonomous-research/use-autonomous-research-sessions";
import { MainSidebar } from "@/components/sidebar/main-sidebar";
import { isEnterpriseEnabled } from "@/ee/config";
import type { EEState } from "@/hooks/use-ee-components";
import { useIsMobile } from "@/hooks/use-mobile";
import { useVerifications } from "@/hooks/use-verifications";
import { useWorkflowTree } from "@/hooks/use-workflow-tree";
import { cn } from "@/lib/utils";
import type { ResearchSection } from "@/types/research";
import { DropdownMenu, IconButton, SidebarWithSections, TopbarWithRightNav } from "@/ui";

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

function getActiveSection(pathname: string): string {
  if (pathname.startsWith("/autonomous-research")) return "autonomous-research";
  if (pathname.startsWith("/settings")) return "settings";
  if (pathname.startsWith("/verification")) return "verification";
  if (pathname.startsWith("/notifications")) return "notifications";
  if (pathname.startsWith("/reproduction")) return "reproduction";
  if (pathname.startsWith("/papers")) return "papers";
  return "home";
}

interface AppLayoutProps {
  ee: EEState;
}

export function AppLayout({ ee }: AppLayoutProps) {
  const { t, i18n } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();
  const enterprise = isEnterpriseEnabled();

  const activeSection = getActiveSection(location.pathname);
  const autonomousSubNav = getAutonomousSubNav(location.pathname);

  // Autonomous Research
  const [autonomousSectionsMap, setAutonomousSectionsMap] = useState<AutonomousSectionsMap>(
    initialAutonomousSectionsMap,
  );
  const [autonomousActiveSectionMap, setAutonomousActiveSectionMap] =
    useState<AutonomousActiveSectionMap>(initialAutonomousActiveSectionMap);

  // Workflow
  const {
    workflowTree,
    activeNodeId,
    setActiveNodeId,
    handleNavigate,
    addWorkflowNode,
    updateNodeSnapshot,
    resetDownstreamSessions,
    resetWorkflow,
  } = useWorkflowTree();

  // Verification
  const {
    verifications,
    handleUpdateVerification,
    handleDeleteVerification,
    handleDuplicateVerification,
    handleCreateWithMethod,
    handleCreateWithQuery,
  } = useVerifications();

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

  function handleSelectAutonomousSession(subNav: AutonomousSubNav, section: ResearchSection) {
    setAutonomousActiveSectionMap((prev) => ({
      ...prev,
      [subNav]: section,
    }));
  }

  function handleCreateSection(subNav: AutonomousSubNav) {
    setAutonomousActiveSectionMap((prev) => ({ ...prev, [subNav]: null }));
    resetWorkflow();
  }

  function handleUpdateSectionTitle(subNav: AutonomousSubNav, title: string) {
    setAutonomousActiveSectionMap((prevActive) => {
      const current = prevActive[subNav];
      if (!current) return prevActive;
      setAutonomousSectionsMap((prevSections) => ({
        ...prevSections,
        [subNav]: prevSections[subNav].map((s) => (s.id === current.id ? { ...s, title } : s)),
      }));
      return { ...prevActive, [subNav]: { ...current, title } };
    });
  }

  function handleMobileNavClose() {
    if (isMobile) setSidebarOpen(false);
  }

  const currentLanguage = (i18n.resolvedLanguage ?? i18n.language)?.toLowerCase().startsWith("ja")
    ? "ja"
    : "en";

  const dropdownItemClassName =
    "[&_span]:text-xs [&_span]:text-white hover:bg-neutral-700 data-[highlighted]:bg-neutral-700 [&_.text-default-font]:text-white";

  function handleRefreshSessions(subNav: AutonomousSubNav, preferredId?: string) {
    return fetchSections(subNav, preferredId);
  }

  return (
    <div className="flex min-h-screen bg-default-background">
      <aside
        className={cn(
          "fixed left-0 top-0 h-screen bg-default-background transition-[width] duration-200 ease-in-out overflow-hidden",
          sidebarOpen ? "w-60" : "w-0",
          isMobile ? "z-40" : "z-30",
        )}
      >
        <SidebarWithSections
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
          footer={undefined}
        >
          <MainSidebar
            activeSection={activeSection}
            autonomousSubNav={autonomousSubNav}
            isAuthenticated={ee.isAuthenticated}
            onMobileNavClose={handleMobileNavClose}
            onAutonomousSubNavClick={() => setAutonomousListViewKey((k) => k + 1)}
          />
        </SidebarWithSections>
      </aside>

      {isMobile && sidebarOpen && (
        <button
          type="button"
          aria-label="Close sidebar"
          className="fixed inset-0 z-20 bg-black/50 transition-opacity cursor-pointer"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <div
        className={cn(
          "flex-1 flex flex-col min-w-0 overflow-x-clip transition-[margin-left] duration-200 ease-in-out",
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
                    <DropdownMenu className="bg-neutral-900 min-w-[120px] border-neutral-700">
                      <DropdownMenu.DropdownItem
                        icon={currentLanguage === "ja" ? <FeatherCheck /> : null}
                        onSelect={() => i18n.changeLanguage("ja")}
                        className={dropdownItemClassName}
                      >
                        日本語
                      </DropdownMenu.DropdownItem>
                      <DropdownMenu.DropdownItem
                        icon={currentLanguage === "en" ? <FeatherCheck /> : null}
                        onSelect={() => i18n.changeLanguage("en")}
                        className={dropdownItemClassName}
                      >
                        English
                      </DropdownMenu.DropdownItem>
                    </DropdownMenu>
                  </SubframeCore.DropdownMenu.Content>
                </SubframeCore.DropdownMenu.Portal>
              </SubframeCore.DropdownMenu.Root>
              <div className="hidden md:flex items-center gap-4">
                <IconButton
                  variant="neutral-tertiary"
                  icon={<SiGithub className="h-4 w-4" />}
                  onClick={() =>
                    window.open(
                      "https://github.com/airas-org/airas",
                      "_blank",
                      "noopener,noreferrer",
                    )
                  }
                  aria-label="Open GitHub repository"
                />
                <IconButton
                  variant="neutral-tertiary"
                  icon={<SiX className="h-4 w-4" />}
                  onClick={() =>
                    window.open("https://x.com/fuyu_quant", "_blank", "noopener,noreferrer")
                  }
                  aria-label="Open X profile"
                />
              </div>
              <IconButton
                variant={
                  activeSection === "notifications" ? "neutral-secondary" : "neutral-tertiary"
                }
                icon={<FeatherBell className="h-4 w-4" />}
                onClick={() => navigate("/notifications")}
                aria-label="Open notifications"
              />
              {!ee.loading &&
                (ee.isAuthenticated && ee.components ? (
                  <ee.components.UserMenu />
                ) : enterprise && ee.components ? (
                  <IconButton
                    variant="neutral-secondary"
                    icon={<FeatherUser />}
                    onClick={() => navigate("/login")}
                    aria-label="Log in"
                  />
                ) : null)}
            </>
          }
        />
        <div className="flex-1 flex min-h-0">
          <MainContent
            assistedResearchProps={{
              workflowTree,
              activeNodeId,
              setActiveNodeId,
              addWorkflowNode,
              updateNodeSnapshot,
              resetDownstreamSessions,
              onNavigate: handleNavigate,
            }}
            verificationProps={{
              verifications,
              onDeleteVerification: handleDeleteVerification,
              onDuplicateVerification: handleDuplicateVerification,
              onUpdateVerification: handleUpdateVerification,
              onCreateWithQuery: handleCreateWithQuery,
              onCreateWithMethod: handleCreateWithMethod,
            }}
            autonomousResearchProps={{
              sectionsMap: autonomousSectionsMap,
              activeSectionMap: autonomousActiveSectionMap,
              onSelectSession: handleSelectAutonomousSession,
              onCreateSection: handleCreateSection,
              onUpdateSectionTitle: handleUpdateSectionTitle,
              onRefreshSessions: handleRefreshSessions,
              listViewKey: autonomousListViewKey,
            }}
          />
        </div>
      </div>
    </div>
  );
}
