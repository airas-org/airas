import {
  FeatherBrainCircuit,
  FeatherRefreshCw,
  FeatherTarget,
} from "@subframe/core";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import type { AutonomousSubNav } from "@/components/main-content";
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

  return (
    <>
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
          className={`flex items-center gap-2 rounded-md px-2 py-1 text-xs transition-colors cursor-pointer ${
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
          className={`flex items-center gap-2 rounded-md px-2 py-1 text-xs transition-colors cursor-pointer ${
            activeSection === "autonomous-research" &&
            autonomousSubNav === "hypothesis-driven"
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
    </>
  );
}
