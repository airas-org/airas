import { SiGithub, SiX } from "@icons-pack/react-simple-icons";
import * as SubframeCore from "@subframe/core";
import {
  FeatherBell,
  FeatherCheck,
  FeatherGlobe,
  FeatherPanelLeftClose,
  FeatherPanelLeftOpen,
  FeatherSettings,
  FeatherUser,
} from "@subframe/core";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";
import { AUTONOMOUS_SUB_NAVS, type AutonomousSubNav, getAutonomousSubNav, MainContent } from "@/components/main-content";
import {
  type AutonomousActiveSectionMap,
  type AutonomousSectionsMap,
  useAutonomousResearchSessions,
} from "@/components/pages/autonomous-research/use-autonomous-research-sessions";
import { useVerifications } from "@/components/pages/verification/use-verifications";
import { MainSidebar } from "@/components/sidebar/main-sidebar";
import { SettingsSidebar } from "@/components/sidebar/settings-sidebar";
import type { EEComponents } from "@/hooks/use-ee-components";
import { useIsMobile } from "@/hooks/use-mobile";
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
  eeComponents: EEComponents | null;
}

export function AppLayout({ eeComponents }: AppLayoutProps) {
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
  } = useVerifications(navigate);

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
    resetWorkflow();
  }, [resetWorkflow]);

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
          footer={
            !isSettingsView ? (
              <button
                type="button"
                className="flex w-full items-center gap-2.5 rounded-md px-1 py-1 -mx-1 transition-colors cursor-pointer text-neutral-600 hover:bg-neutral-100"
                onClick={() => navigate("/settings/profile")}
              >
                <FeatherSettings className="h-4 w-4" />
                <span className="text-sm font-medium">{t("nav.settings")}</span>
              </button>
            ) : undefined
          }
        >
          {isSettingsView ? (
            <SettingsSidebar />
          ) : (
            <MainSidebar
              activeSection={activeSection}
              autonomousSubNav={autonomousSubNav}
              onMobileNavClose={handleMobileNavClose}
              onAutonomousSubNavClick={() => setAutonomousListViewKey((k) => k + 1)}
            />
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
                        className="[&_span]:text-xs [&_span]:text-white hover:bg-neutral-700 data-[highlighted]:bg-neutral-700 [&_.text-default-font]:text-white"
                      >
                        日本語
                      </DropdownMenu.DropdownItem>
                      <DropdownMenu.DropdownItem
                        icon={currentLanguage === "en" ? <FeatherCheck /> : null}
                        onSelect={() => i18n.changeLanguage("en")}
                        className="[&_span]:text-xs [&_span]:text-white hover:bg-neutral-700 data-[highlighted]:bg-neutral-700 [&_.text-default-font]:text-white"
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
                <span title="Enterprise Edition is not enabled">
                  <IconButton disabled variant="neutral-secondary" icon={<FeatherUser />} />
                </span>
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
            onCreateWithQuery={handleCreateWithQuery}
            onCreateWithMethod={handleCreateWithMethod}
            autonomousListViewKey={autonomousListViewKey}
          />
        </div>
      </div>
    </div>
  );
}
