"use client";

import * as SubframeCore from "@subframe/core";
import {
  FeatherArrowDownUp,
  FeatherCalendar,
  FeatherCheck,
  FeatherChevronDown,
  FeatherChevronRight,
  FeatherFlaskConical,
  FeatherLoader,
  FeatherPlus,
  FeatherSearch,
  FeatherX,
} from "@subframe/core";
import { useState } from "react";
import type { ResearchSection } from "@/types/research";
import { Badge } from "@/ui/components/Badge";
import { Button } from "@/ui/components/Button";
import { DropdownMenu } from "@/ui/components/DropdownMenu";
import { TextField } from "@/ui/components/TextField";

type SortKey = "newest" | "oldest" | "title";

interface HypothesisDrivenListProps {
  sessions: ResearchSection[];
  onSelectSession: (section: ResearchSection) => void;
  onNavigateToInput: () => void;
  onRefreshSessions: (preferredId?: string) => Promise<void>;
}

export function HypothesisDrivenList({
  sessions,
  onSelectSession,
  onNavigateToInput,
  onRefreshSessions,
}: HypothesisDrivenListProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [sortKey, setSortKey] = useState<SortKey>("newest");

  const filtered = sessions
    .filter((s) =>
      searchQuery.trim() ? s.title.toLowerCase().includes(searchQuery.toLowerCase()) : true,
    )
    .sort((a, b) => {
      if (sortKey === "newest") return b.createdAt.getTime() - a.createdAt.getTime();
      if (sortKey === "oldest") return a.createdAt.getTime() - b.createdAt.getTime();
      return a.title.localeCompare(b.title);
    });

  const statusBadge = (status: ResearchSection["status"]) => {
    if (status === "completed") {
      return (
        <Badge variant="success" icon={<FeatherCheck />}>
          完了
        </Badge>
      );
    }
    if (status === "failed") {
      return (
        <Badge variant="error" icon={<FeatherX />}>
          失敗
        </Badge>
      );
    }
    return (
      <Badge variant="brand" icon={<FeatherLoader />}>
        進行中
      </Badge>
    );
  };

  return (
    <div className="flex h-full w-full flex-col items-center bg-default-background px-6 py-12 overflow-auto">
      <div className="flex w-full max-w-[768px] flex-col items-start gap-6">
        <div className="flex w-full flex-col items-center gap-4">
          <img
            className="h-12 flex-none object-contain"
            src="https://res.cloudinary.com/subframe/image/upload/v1772095364/uploads/36719/yglokiomst2au6hj5g8o.png"
            alt=""
          />
          <span className="text-heading-1 font-heading-1 text-default-font text-center">
            仮説駆動研究セッション一覧
          </span>
          <span className="text-body font-body text-subtext-color text-center">
            過去に実行した仮説駆動研究セッションの履歴を確認できます
          </span>
        </div>
        <div className="flex w-full items-center justify-between gap-3">
          <TextField
            className="h-auto grow shrink-0 basis-0"
            variant="outline"
            label=""
            helpText=""
            icon={<FeatherSearch />}
          >
            <TextField.Input
              placeholder="セッションを検索..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </TextField>
          <Button variant="brand-primary" icon={<FeatherPlus />} onClick={onNavigateToInput}>
            新規研究を開始
          </Button>
        </div>
        <div className="flex w-full items-center gap-2 border-b border-solid border-neutral-border pb-3">
          <span className="grow shrink-0 basis-0 text-body-bold font-body-bold text-default-font">
            {filtered.length} 件のセッション
          </span>
          <SubframeCore.DropdownMenu.Root>
            <SubframeCore.DropdownMenu.Trigger asChild>
              <Button
                variant="neutral-secondary"
                size="small"
                icon={<FeatherArrowDownUp />}
                iconRight={<FeatherChevronDown />}
              >
                並び替え
              </Button>
            </SubframeCore.DropdownMenu.Trigger>
            <SubframeCore.DropdownMenu.Portal>
              <SubframeCore.DropdownMenu.Content side="bottom" align="end" sideOffset={4} asChild>
                <DropdownMenu>
                  <DropdownMenu.DropdownItem icon={null} onSelect={() => setSortKey("newest")}>
                    作成日時（新しい順）
                  </DropdownMenu.DropdownItem>
                  <DropdownMenu.DropdownItem icon={null} onSelect={() => setSortKey("oldest")}>
                    作成日時（古い順）
                  </DropdownMenu.DropdownItem>
                  <DropdownMenu.DropdownItem icon={null} onSelect={() => setSortKey("title")}>
                    タイトル順
                  </DropdownMenu.DropdownItem>
                </DropdownMenu>
              </SubframeCore.DropdownMenu.Content>
            </SubframeCore.DropdownMenu.Portal>
          </SubframeCore.DropdownMenu.Root>
        </div>
        <div className="flex w-full flex-col items-start gap-3">
          {filtered.length === 0 && (
            <div className="flex w-full flex-col items-center gap-4 py-12">
              <span className="text-body font-body text-subtext-color">
                {searchQuery.trim()
                  ? "検索結果が見つかりませんでした"
                  : "まだ研究セッションがありません"}
              </span>
              {!searchQuery.trim() && (
                <Button variant="brand-primary" icon={<FeatherPlus />} onClick={onNavigateToInput}>
                  最初の研究を開始
                </Button>
              )}
            </div>
          )}
          {filtered.map((session) => (
            <button
              key={session.id}
              type="button"
              className="flex w-full flex-col items-start gap-3 rounded-lg border border-solid border-neutral-border bg-default-background px-5 py-4 cursor-pointer hover:border-brand-300 hover:shadow-md transition-all text-left"
              onClick={() => onSelectSession(session)}
            >
              <div className="flex w-full items-center justify-between">
                <div className="flex items-center gap-3">
                  <FeatherFlaskConical className="text-heading-3 font-heading-3 text-brand-600" />
                  <span className="text-body-bold font-body-bold text-default-font">
                    {session.title}
                  </span>
                </div>
                {statusBadge(session.status)}
              </div>
              <div className="flex w-full items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-1">
                    <FeatherCalendar className="text-caption font-caption text-subtext-color" />
                    <span className="text-caption font-caption text-subtext-color">
                      {session.createdAt.toLocaleDateString("ja-JP", {
                        year: "numeric",
                        month: "long",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </span>
                  </div>
                </div>
                <FeatherChevronRight className="text-body font-body text-subtext-color" />
              </div>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
