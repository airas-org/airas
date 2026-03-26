import { SiDiscord } from "@icons-pack/react-simple-icons";
import {
  FeatherBarChart2,
  FeatherBookOpen,
  FeatherBrainCircuit,
  FeatherCreditCard,
  FeatherExternalLink,
  FeatherKey,
  FeatherLink,
  FeatherMessageSquare,
  FeatherReceipt,
  FeatherRefreshCw,
  FeatherTarget,
  FeatherUser,
} from "@subframe/core";
import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";
import type { AutonomousSubNav } from "@/components/main-content";
import { getSettingsTab, type SettingsTab } from "@/components/pages/settings";
import { SidebarWithSections } from "@/ui";

interface SettingsNavItem {
  tab: SettingsTab;
  icon: ReactNode;
  labelKey: string;
}

const SETTINGS_NAV_ITEMS: SettingsNavItem[] = [
  { tab: "profile", icon: <FeatherUser />, labelKey: "nav.profile" },
  { tab: "integration", icon: <FeatherLink />, labelKey: "nav.integration" },
  { tab: "api-token", icon: <FeatherKey />, labelKey: "apiToken.title" },
  { tab: "user-plan", icon: <FeatherCreditCard />, labelKey: "nav.userPlan" },
  { tab: "receipts", icon: <FeatherReceipt />, labelKey: "receipts.title" },
  { tab: "usage", icon: <FeatherBarChart2 />, labelKey: "usage.title" },
];

interface MainSidebarProps {
  activeSection: string;
  autonomousSubNav: AutonomousSubNav;
  isAuthenticated: boolean;
  settingsTabs: SettingsTab[];
  onMobileNavClose: () => void;
  onAutonomousSubNavClick: () => void;
}

export function MainSidebar({
  activeSection,
  autonomousSubNav,
  isAuthenticated,
  settingsTabs,
  onMobileNavClose,
  onAutonomousSubNavClick,
}: MainSidebarProps) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  return (
    <>
      <SidebarWithSections.NavSection
        label={<span className="text-sm font-medium">{t("nav.research")}</span>}
      >
        <SidebarWithSections.NavItem
          icon={<FeatherTarget />}
          selected={activeSection === "home" || activeSection === "verification"}
          onClick={() => {
            navigate("/home");
            onMobileNavClose();
          }}
        >
          {t("nav.newVerification")}
        </SidebarWithSections.NavItem>
        <SidebarWithSections.NavItem
          icon={<FeatherRefreshCw />}
          selected={activeSection === "reproduction"}
          onClick={() => {
            navigate("/reproduction");
            onMobileNavClose();
          }}
        >
          {t("nav.reproduction")}
        </SidebarWithSections.NavItem>
        <SidebarWithSections.NavItem
          icon={<FeatherBrainCircuit />}
          selected={activeSection === "autonomous-research"}
          className="cursor-default hover:bg-transparent active:bg-transparent"
        >
          {t("nav.autonomousResearch")}
        </SidebarWithSections.NavItem>
        <div className="flex flex-col gap-0.5 pl-7">
          <button
            type="button"
            className={`flex items-center gap-2 rounded-md px-2 py-1 text-sm transition-colors cursor-pointer ${
              activeSection === "autonomous-research" && autonomousSubNav === "topic-driven"
                ? "text-brand-700 bg-brand-50"
                : "text-neutral-600 hover:bg-neutral-100"
            }`}
            onClick={() => {
              onAutonomousSubNavClick();
              navigate("/autonomous-research/topic-driven");
              onMobileNavClose();
            }}
          >
            <span className="inline-block h-1 w-1 rounded-full bg-current" />
            {t("nav.topicDriven")}
          </button>
          <button
            type="button"
            className={`flex items-center gap-2 rounded-md px-2 py-1 text-sm transition-colors cursor-pointer ${
              activeSection === "autonomous-research" && autonomousSubNav === "hypothesis-driven"
                ? "text-brand-700 bg-brand-50"
                : "text-neutral-600 hover:bg-neutral-100"
            }`}
            onClick={() => {
              onAutonomousSubNavClick();
              navigate("/autonomous-research/hypothesis-driven");
              onMobileNavClose();
            }}
          >
            <span className="inline-block h-1 w-1 rounded-full bg-current" />
            {t("nav.hypothesisDriven")}
          </button>
        </div>
      </SidebarWithSections.NavSection>

      {/* --- Settings (EE only) --- */}
      {isAuthenticated && (
        <SidebarWithSections.NavSection
          label={<span className="text-sm font-medium">{t("nav.settings")}</span>}
        >
          {SETTINGS_NAV_ITEMS.filter((item) => settingsTabs.includes(item.tab)).map((item) => (
            <SidebarWithSections.NavItem
              key={item.tab}
              icon={item.icon}
              selected={getSettingsTab(location.pathname) === item.tab}
              onClick={() => {
                navigate(`/settings/${item.tab}`);
                onMobileNavClose();
              }}
            >
              {t(item.labelKey)}
            </SidebarWithSections.NavItem>
          ))}
        </SidebarWithSections.NavSection>
      )}

      {/* --- Support --- */}
      <SidebarWithSections.NavSection
        label={<span className="text-sm font-medium">{t("nav.support")}</span>}
      >
        <SidebarWithSections.NavItem
          icon={<FeatherBookOpen />}
          selected={false}
          rightSlot={<FeatherExternalLink className="h-3 w-3 text-neutral-400" />}
          onClick={() =>
            window.open("https://airas-org.github.io/airas/", "_blank", "noopener,noreferrer")
          }
        >
          {t("nav.docs")}
        </SidebarWithSections.NavItem>
        <SidebarWithSections.NavItem
          icon={<SiDiscord className="h-4 w-4" />}
          selected={false}
          rightSlot={<FeatherExternalLink className="h-3 w-3 text-neutral-400" />}
          onClick={() =>
            window.open("https://discord.gg/uDmkgKfkes", "_blank", "noopener,noreferrer")
          }
        >
          Discord
        </SidebarWithSections.NavItem>
        {isAuthenticated && settingsTabs.includes("feedback") && (
          <SidebarWithSections.NavItem
            icon={<FeatherMessageSquare />}
            selected={getSettingsTab(location.pathname) === "feedback"}
            onClick={() => {
              navigate("/settings/feedback");
              onMobileNavClose();
            }}
          >
            {t("nav.feedback")}
          </SidebarWithSections.NavItem>
        )}
      </SidebarWithSections.NavSection>
    </>
  );
}
