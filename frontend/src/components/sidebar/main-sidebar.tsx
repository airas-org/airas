import { SiDiscord } from "@icons-pack/react-simple-icons";
import {
  FeatherBookOpen,
  FeatherBrainCircuit,
  FeatherExternalLink,
  FeatherKey,
  FeatherRefreshCw,
  FeatherTarget,
} from "@subframe/core";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";
import type { AutonomousSubNav } from "@/components/main-content";
import { getSettingsTab } from "@/components/pages/settings";
import { SidebarWithSections } from "@/ui";

interface MainSidebarProps {
  activeSection: string;
  autonomousSubNav: AutonomousSubNav;
  onMobileNavClose: () => void;
  onAutonomousSubNavClick: () => void;
}

export function MainSidebar({
  activeSection,
  autonomousSubNav,
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
        <SidebarWithSections.NavItem
          icon={<FeatherKey />}
          selected={getSettingsTab(location.pathname) === "api-keys"}
          onClick={() => {
            navigate("/settings/api-keys");
            onMobileNavClose();
          }}
        >
          {t("nav.apiKeys")}
        </SidebarWithSections.NavItem>
      </SidebarWithSections.NavSection>
    </>
  );
}
