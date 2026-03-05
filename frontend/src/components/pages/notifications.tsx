import {
  FeatherAlertTriangle,
  FeatherCheckCircle,
  FeatherFileText,
  FeatherMessageSquare,
} from "@subframe/core";
import { useState } from "react";
import { Badge, Button, IconWithBackground } from "@/ui";

type NotificationType = "experiment-done" | "paper-done" | "comment" | "system-alert";
type FilterKey = "all" | "unread" | "read";

interface Notification {
  id: string;
  type: NotificationType;
  title: string;
  description: string;
  timestamp: string;
  read: boolean;
}

const initialNotifications: Notification[] = [
  {
    id: "1",
    type: "experiment-done",
    title: "実験完了",
    description: "「強化学習による最適化」の実験が正常に完了しました。結果を確認してください。",
    timestamp: "5分前",
    read: false,
  },
  {
    id: "2",
    type: "paper-done",
    title: "論文生成完了",
    description: "「画像認識モデルの比較」の論文ドラフトが生成されました。",
    timestamp: "30分前",
    read: false,
  },
  {
    id: "3",
    type: "comment",
    title: "コメント",
    description:
      "田中さんが「LLMの推論能力評価」にコメントしました: 「実験パラメータを確認してください」",
    timestamp: "1時間前",
    read: false,
  },
  {
    id: "4",
    type: "system-alert",
    title: "システムアラート",
    description:
      "GPUリソースの使用率が90%を超えています。実行中の実験に影響がある可能性があります。",
    timestamp: "2時間前",
    read: false,
  },
  {
    id: "5",
    type: "experiment-done",
    title: "実験完了",
    description: "「データ拡張手法の効果検証」の実験が完了しました。精度が3.2%向上しています。",
    timestamp: "昨日",
    read: true,
  },
  {
    id: "6",
    type: "comment",
    title: "コメント",
    description:
      "佐藤さんが「自然言語処理の精度向上」に返信しました: 「BERTベースのモデルも試しましょう」",
    timestamp: "昨日",
    read: true,
  },
  {
    id: "7",
    type: "paper-done",
    title: "論文生成完了",
    description:
      "「強化学習アルゴリズムの収束性解析」の論文が生成されました。レビューをお願いします。",
    timestamp: "2日前",
    read: true,
  },
  {
    id: "8",
    type: "system-alert",
    title: "システムアラート",
    description: "メンテナンスのため、3月5日 02:00-04:00 にサービスが一時停止します。",
    timestamp: "3日前",
    read: true,
  },
];

function getNotificationIcon(type: NotificationType): React.ReactNode {
  switch (type) {
    case "experiment-done":
      return <FeatherCheckCircle />;
    case "paper-done":
      return <FeatherFileText />;
    case "comment":
      return <FeatherMessageSquare />;
    case "system-alert":
      return <FeatherAlertTriangle />;
  }
}

function getNotificationVariant(type: NotificationType): "success" | "brand" | "warning" | "error" {
  switch (type) {
    case "experiment-done":
      return "success";
    case "paper-done":
      return "brand";
    case "comment":
      return "warning";
    case "system-alert":
      return "error";
  }
}

const filters: { key: FilterKey; label: string }[] = [
  { key: "all", label: "すべて" },
  { key: "unread", label: "未読" },
  { key: "read", label: "既読" },
];

export function NotificationsPage() {
  const [notifications, setNotifications] = useState<Notification[]>(initialNotifications);
  const [filter, setFilter] = useState<FilterKey>("all");

  const unreadCount = notifications.filter((n) => !n.read).length;

  const filtered = notifications.filter((n) => {
    if (filter === "unread") return !n.read;
    if (filter === "read") return n.read;
    return true;
  });

  const markAsRead = (id: string) => {
    setNotifications((prev) => prev.map((n) => (n.id === id ? { ...n, read: true } : n)));
  };

  const markAllAsRead = () => {
    setNotifications((prev) => prev.map((n) => ({ ...n, read: true })));
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <h1 className="text-heading-2 font-heading-2 text-default-font">通知</h1>
            {unreadCount > 0 && <Badge variant="brand">{unreadCount}</Badge>}
          </div>
          {unreadCount > 0 && (
            <Button variant="neutral-secondary" size="small" onClick={markAllAsRead}>
              すべて既読にする
            </Button>
          )}
        </div>

        <div className="flex items-center gap-2 mb-6">
          {filters.map((f) => (
            <Button
              key={f.key}
              variant={filter === f.key ? "brand-secondary" : "neutral-tertiary"}
              size="small"
              onClick={() => setFilter(f.key)}
            >
              {f.label}
            </Button>
          ))}
        </div>

        <div className="flex flex-col gap-2">
          {filtered.map((n) => (
            <button
              key={n.id}
              type="button"
              className={`flex items-start gap-4 rounded-lg border p-4 text-left transition-colors ${
                n.read ? "border-border bg-card" : "border-brand-200 bg-brand-50 hover:bg-brand-100"
              }`}
              onClick={() => markAsRead(n.id)}
            >
              <IconWithBackground
                variant={getNotificationVariant(n.type)}
                size="medium"
                icon={getNotificationIcon(n.type)}
              />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-body-bold font-body-bold text-default-font">{n.title}</span>
                  {!n.read && <span className="h-2 w-2 rounded-full bg-brand-600 shrink-0" />}
                </div>
                <p className="text-body font-body text-subtext-color mt-1">{n.description}</p>
                <span className="text-caption font-caption text-neutral-400 mt-2 block">
                  {n.timestamp}
                </span>
              </div>
            </button>
          ))}
          {filtered.length === 0 && (
            <p className="py-12 text-center text-body font-body text-subtext-color">
              通知はありません
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
