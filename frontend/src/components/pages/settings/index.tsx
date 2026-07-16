import { FeedbackPage } from "@/components/pages/feedback";
import { ApiKeysPage } from "@/components/pages/settings/api-keys";

export type SettingsTab = "feedback" | "api-keys";

export const SETTINGS_TABS: SettingsTab[] = ["feedback", "api-keys"];

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
      {activeTab === "feedback" && <FeedbackPage />}
      {activeTab === "api-keys" && <ApiKeysPage />}
    </div>
  );
}
