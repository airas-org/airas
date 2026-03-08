import {
  FeatherActivity,
  FeatherCheckCircle,
  FeatherFileText,
  FeatherFlaskConical,
  FeatherList,
  FeatherPlus,
} from "@subframe/core";
import { useTranslation } from "react-i18next";
import { Badge, Button, IconWithBackground, Table } from "@/ui";

interface DashboardPageProps {
  onNavigate: (nav: string) => void;
}

export function DashboardPage({ onNavigate }: DashboardPageProps) {
  const { t } = useTranslation();

  const stats = [
    {
      label: t("dashboard.stats.total"),
      value: "24",
      icon: <FeatherFlaskConical />,
      variant: "brand" as const,
    },
    {
      label: t("dashboard.stats.running"),
      value: "5",
      icon: <FeatherActivity />,
      variant: "warning" as const,
    },
    {
      label: t("dashboard.stats.completed"),
      value: "16",
      icon: <FeatherCheckCircle />,
      variant: "success" as const,
    },
    {
      label: t("dashboard.stats.paperGenerated"),
      value: "3",
      icon: <FeatherFileText />,
      variant: "neutral" as const,
    },
  ];

  const recentActivity = [
    {
      id: "1",
      timestamp: "2026-03-04 14:32",
      description: "「強化学習による最適化」の実験が完了しました",
      status: t("dashboard.status.completed"),
      variant: "success" as const,
    },
    {
      id: "2",
      timestamp: "2026-03-04 12:15",
      description: "「LLMの推論能力評価」の検証コードを生成中",
      status: t("dashboard.status.running"),
      variant: "warning" as const,
    },
    {
      id: "3",
      timestamp: "2026-03-04 10:00",
      description: "「画像認識モデルの比較」の論文が生成されました",
      status: t("dashboard.status.paperGenerated"),
      variant: "brand" as const,
    },
    {
      id: "4",
      timestamp: "2026-03-03 18:45",
      description: "「自然言語処理の精度向上」の検証方針が提案されました",
      status: t("dashboard.status.proposed"),
      variant: "neutral" as const,
    },
    {
      id: "5",
      timestamp: "2026-03-03 15:20",
      description: "「データ拡張手法の効果検証」を新規作成しました",
      status: t("dashboard.status.new"),
      variant: "brand" as const,
    },
  ];

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-5xl mx-auto px-8 py-8">
        <div className="mb-8">
          <h1 className="text-heading-2 font-heading-2 text-default-font">
            {t("dashboard.title")}
          </h1>
          <p className="text-body font-body text-subtext-color mt-1">{t("dashboard.subtitle")}</p>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-8">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="rounded-lg border border-border bg-card p-5 flex flex-col gap-3"
            >
              <div className="flex items-center justify-between">
                <span className="text-caption font-caption text-subtext-color">{stat.label}</span>
                <IconWithBackground variant={stat.variant} size="small" icon={stat.icon} />
              </div>
              <span className="text-heading-1 font-heading-1 text-default-font">{stat.value}</span>
            </div>
          ))}
        </div>

        <div className="rounded-lg border border-border bg-card mb-8">
          <div className="px-5 py-4 border-b border-border">
            <h2 className="text-body-bold font-body-bold text-default-font">
              {t("dashboard.recentActivity")}
            </h2>
          </div>
          <Table
            header={
              <Table.HeaderRow>
                <Table.HeaderCell>{t("dashboard.table.datetime")}</Table.HeaderCell>
                <Table.HeaderCell>{t("dashboard.table.content")}</Table.HeaderCell>
                <Table.HeaderCell>{t("dashboard.table.status")}</Table.HeaderCell>
              </Table.HeaderRow>
            }
          >
            {recentActivity.map((item) => (
              <Table.Row key={item.id}>
                <Table.Cell>
                  <span className="text-caption font-caption text-subtext-color whitespace-nowrap">
                    {item.timestamp}
                  </span>
                </Table.Cell>
                <Table.Cell>
                  <span className="text-body font-body text-default-font">{item.description}</span>
                </Table.Cell>
                <Table.Cell>
                  <Badge variant={item.variant}>{item.status}</Badge>
                </Table.Cell>
              </Table.Row>
            ))}
          </Table>
        </div>

        <div className="flex items-center gap-3">
          <Button icon={<FeatherPlus />} onClick={() => onNavigate("new-verification")}>
            {t("dashboard.newVerification")}
          </Button>
          <Button
            variant="neutral-secondary"
            icon={<FeatherList />}
            onClick={() => onNavigate("verifications")}
          >
            {t("dashboard.viewList")}
          </Button>
        </div>
      </div>
    </div>
  );
}
