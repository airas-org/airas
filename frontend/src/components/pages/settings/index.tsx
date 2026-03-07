import { ApiTokenPage } from "@/components/pages/api-token";
import { FeedbackPage } from "@/components/pages/feedback";
import { HelpPage } from "@/components/pages/help";
import { IntegrationPage } from "@/components/pages/integration";
import { LegalPage } from "@/components/pages/legal";
import { ProfilePage } from "@/components/pages/profile";
import { UserPlanPage } from "@/components/pages/user-plan";

export type SettingsTab =
  | "integration"
  | "user-plan"
  | "profile"
  | "api-token"
  | "feedback"
  | "help"
  | "legal";

interface SettingsPageProps {
  activeTab: SettingsTab;
}

export function SettingsPage({ activeTab }: SettingsPageProps) {
  return (
    <div className="flex-1 min-w-0">
      {activeTab === "integration" && <IntegrationPage />}
      {activeTab === "user-plan" && <UserPlanPage />}
      {activeTab === "profile" && <ProfilePage />}
      {activeTab === "api-token" && <ApiTokenPage />}
      {activeTab === "feedback" && <FeedbackPage />}
      {activeTab === "help" && <HelpPage />}
      {activeTab === "legal" && <LegalPage />}
    </div>
  );
}
