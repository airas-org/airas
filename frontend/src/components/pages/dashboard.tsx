import {
  FeatherActivity,
  FeatherCheckCircle,
  FeatherFileText,
  FeatherFlaskConical,
  FeatherList,
  FeatherPlus,
} from "@subframe/core";
import { Badge, Button, IconWithBackground, Table } from "@/ui";

interface DashboardPageProps {
  onNavigate: (nav: string) => void;
}

const stats = [
  { label: "全検証数", value: "24", icon: <FeatherFlaskConical />, variant: "brand" as const },
  { label: "実行中", value: "5", icon: <FeatherActivity />, variant: "warning" as const },
  { label: "完了", value: "16", icon: <FeatherCheckCircle />, variant: "success" as const },
  { label: "論文生成済み", value: "3", icon: <FeatherFileText />, variant: "neutral" as const },
];

const recentActivity = [
  {
    id: "1",
    timestamp: "2026-03-04 14:32",
    description: "「強化学習による最適化」の実験が完了しました",
    status: "完了",
    variant: "success" as const,
  },
  {
    id: "2",
    timestamp: "2026-03-04 12:15",
    description: "「LLMの推論能力評価」の検証コードを生成中",
    status: "実行中",
    variant: "warning" as const,
  },
  {
    id: "3",
    timestamp: "2026-03-04 10:00",
    description: "「画像認識モデルの比較」の論文が生成されました",
    status: "論文生成",
    variant: "brand" as const,
  },
  {
    id: "4",
    timestamp: "2026-03-03 18:45",
    description: "「自然言語処理の精度向上」の検証方針が提案されました",
    status: "方針提案",
    variant: "neutral" as const,
  },
  {
    id: "5",
    timestamp: "2026-03-03 15:20",
    description: "「データ拡張手法の効果検証」を新規作成しました",
    status: "新規",
    variant: "brand" as const,
  },
];

export function DashboardPage({ onNavigate }: DashboardPageProps) {
  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-5xl mx-auto px-8 py-8">
        <div className="mb-8">
          <h1 className="text-heading-2 font-heading-2 text-default-font">ダッシュボード</h1>
          <p className="text-body font-body text-subtext-color mt-1">
            検証プロジェクトの概要と最近のアクティビティ
          </p>
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
              最近のアクティビティ
            </h2>
          </div>
          <Table
            header={
              <Table.HeaderRow>
                <Table.HeaderCell>日時</Table.HeaderCell>
                <Table.HeaderCell>内容</Table.HeaderCell>
                <Table.HeaderCell>ステータス</Table.HeaderCell>
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
            新規検証
          </Button>
          <Button
            variant="neutral-secondary"
            icon={<FeatherList />}
            onClick={() => onNavigate("verifications")}
          >
            検証一覧を見る
          </Button>
        </div>
      </div>
    </div>
  );
}
