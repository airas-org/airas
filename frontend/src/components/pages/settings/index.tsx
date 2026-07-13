import { FeedbackPage } from "@/components/pages/feedback";

export type SettingsTab = "feedback";

export const SETTINGS_TABS: SettingsTab[] = ["feedback"];

export function getSettingsTab(pathname: string): SettingsTab | null {
  const tab = pathname.split("/settings/")[1] as SettingsTab | undefined;
  if (tab && SETTINGS_TABS.includes(tab)) return tab;
  return null;
}

interface SettingsPageProps {
  activeTab: SettingsTab;
}

export function SettingsPage({ activeTab }: SettingsPageProps) {
  return <div className="flex-1 min-w-0">{activeTab === "feedback" && <FeedbackPage />}</div>;
}
