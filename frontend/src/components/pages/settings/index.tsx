import { ApiTokenPage } from "@/components/pages/api-token";
import { FeedbackPage } from "@/components/pages/feedback";
import { IntegrationPage } from "@/components/pages/integration";
import { ProfilePage } from "@/components/pages/profile";
import { ReceiptsPage } from "@/components/pages/receipts";
import { UsagePage } from "@/components/pages/usage";
import { UserPlanPage } from "@/components/pages/user-plan";

export type SettingsTab =
  | "profile"
  | "feedback"
  | "integration"
  | "api-token"
  | "user-plan"
  | "receipts"
  | "usage";

export const SETTINGS_TABS: SettingsTab[] = [
  "profile",
  "feedback",
  "integration",
  "api-token",
  "user-plan",
  "receipts",
  "usage",
];

export function getSettingsTab(pathname: string): SettingsTab | null {
  const tab = pathname.split("/settings/")[1] as SettingsTab | undefined;
  if (tab && SETTINGS_TABS.includes(tab)) return tab;
  return null;
}

interface SettingsPageProps {
  activeTab: SettingsTab;
}

export function SettingsPage({ activeTab }: SettingsPageProps) {
  return (
    <div className="flex-1 min-w-0">
      {activeTab === "profile" && <ProfilePage />}
      {activeTab === "feedback" && <FeedbackPage />}
      {activeTab === "integration" && <IntegrationPage />}
      {activeTab === "api-token" && <ApiTokenPage />}
      {activeTab === "user-plan" && <UserPlanPage />}
      {activeTab === "receipts" && <ReceiptsPage />}
      {activeTab === "usage" && <UsagePage />}
    </div>
  );
}
