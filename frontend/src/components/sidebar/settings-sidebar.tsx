import { SiDiscord } from "@icons-pack/react-simple-icons";
import {
  FeatherArrowLeft,
  FeatherBarChart2,
  FeatherBookOpen,
  FeatherCreditCard,
  FeatherExternalLink,
  FeatherKey,
  FeatherLink,
  FeatherMessageSquare,
  FeatherReceipt,
  FeatherUser,
} from "@subframe/core";
import { useTranslation } from "react-i18next";
import { useLocation, useNavigate } from "react-router-dom";
import { getSettingsTab } from "@/components/pages/settings";
import { SidebarWithSections } from "@/ui";

export function SettingsSidebar() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const location = useLocation();

  return (
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
        label={<span className="text-sm font-medium">{t("settings.externalServicesSection")}</span>}
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
  );
}
