import {
  FeatherFileText,
  FeatherHelpCircle,
  FeatherKey,
  FeatherMessageSquare,
  FeatherSettings,
  FeatherShield,
  FeatherUser,
} from "@subframe/core";
import { useState } from "react";
import { ApiTokenPage } from "@/components/pages/api-token";
import { FeedbackPage } from "@/components/pages/feedback";
import { HelpPage } from "@/components/pages/help";
import { IntegrationPage } from "@/components/pages/integration";
import { LegalPage } from "@/components/pages/legal";
import { ProfilePage } from "@/components/pages/profile";
import { UserPlanPage } from "@/components/pages/user-plan";

type SettingsTab =
  | "integration"
  | "user-plan"
  | "profile"
  | "api-token"
  | "feedback"
  | "help"
  | "legal";

const settingsNav: { key: SettingsTab; label: string; icon: React.ReactNode }[] = [
  {
    key: "integration",
    label: "インテグレーション",
    icon: <FeatherSettings className="h-4 w-4" />,
  },
  { key: "user-plan", label: "プラン", icon: <FeatherUser className="h-4 w-4" /> },
  { key: "profile", label: "プロフィール", icon: <FeatherUser className="h-4 w-4" /> },
  { key: "api-token", label: "API Token", icon: <FeatherKey className="h-4 w-4" /> },
  { key: "feedback", label: "お問い合わせ", icon: <FeatherMessageSquare className="h-4 w-4" /> },
  { key: "help", label: "ヘルプ", icon: <FeatherHelpCircle className="h-4 w-4" /> },
  { key: "legal", label: "利用規約", icon: <FeatherShield className="h-4 w-4" /> },
];

interface SettingsPageProps {
  initialTab?: string;
}

export function SettingsPage({ initialTab }: SettingsPageProps) {
  const [activeTab, setActiveTab] = useState<SettingsTab>(() => {
    const found = settingsNav.find((n) => n.key === initialTab);
    return found ? found.key : "integration";
  });

  return (
    <div className="flex-1 flex min-w-0">
      <nav className="w-52 shrink-0 border-r border-solid border-neutral-border bg-default-background p-4">
        <h2 className="text-heading-3 font-heading-3 text-default-font px-3 py-2 mb-2">設定</h2>
        <div className="flex flex-col gap-0.5">
          {settingsNav.map((item) => (
            <button
              key={item.key}
              type="button"
              onClick={() => setActiveTab(item.key)}
              className={`flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors cursor-pointer ${
                activeTab === item.key
                  ? "bg-brand-50 text-brand-700"
                  : "text-neutral-600 hover:bg-neutral-50"
              }`}
            >
              <span className={activeTab === item.key ? "text-brand-700" : "text-neutral-400"}>
                {item.icon}
              </span>
              {item.label}
            </button>
          ))}
        </div>
        <div className="my-3 h-px bg-neutral-200" />
        <button
          type="button"
          onClick={() => window.open("https://airas-org.github.io/airas/", "_blank")}
          className="flex w-full items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium text-neutral-600 hover:bg-neutral-50 transition-colors cursor-pointer"
        >
          <span className="text-neutral-400">
            <FeatherFileText className="h-4 w-4" />
          </span>
          ドキュメント
        </button>
      </nav>
      <div className="flex-1 min-w-0">
        {activeTab === "integration" && <IntegrationPage />}
        {activeTab === "user-plan" && <UserPlanPage />}
        {activeTab === "profile" && <ProfilePage />}
        {activeTab === "api-token" && <ApiTokenPage />}
        {activeTab === "feedback" && <FeedbackPage />}
        {activeTab === "help" && <HelpPage />}
        {activeTab === "legal" && <LegalPage />}
      </div>
    </div>
  );
}
