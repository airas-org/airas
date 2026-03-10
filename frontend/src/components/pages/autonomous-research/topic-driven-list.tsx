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
  FeatherX,
} from "@subframe/core";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { ResearchSection } from "@/types/research";
import { Badge } from "@/ui/components/Badge";
import { Button } from "@/ui/components/Button";
import { DropdownMenu } from "@/ui/components/DropdownMenu";

type SortKey = "newest" | "oldest" | "title";

interface TopicDrivenListProps {
  sessions: ResearchSection[];
  onSelectSession: (section: ResearchSection) => void;
  onNavigateToInput: () => void;
}

export function TopicDrivenList({
  sessions,
  onSelectSession,
  onNavigateToInput,
}: TopicDrivenListProps) {
  const { t, i18n } = useTranslation();
  const [sortKey, setSortKey] = useState<SortKey>("newest");

  const filtered = sessions.sort((a, b) => {
    if (sortKey === "newest") return b.createdAt.getTime() - a.createdAt.getTime();
    if (sortKey === "oldest") return a.createdAt.getTime() - b.createdAt.getTime();
    return a.title.localeCompare(b.title);
  });

  const statusBadge = (status: ResearchSection["status"]) => {
    const cls = "text-[11px] py-0 px-1.5";
    if (status === "completed") {
      return (
        <Badge className={cls} variant="success" icon={<FeatherCheck className="h-3 w-3" />}>
          {t("autonomous.topicDriven.statusCompleted")}
        </Badge>
      );
    }
    if (status === "failed") {
      return (
        <Badge className={cls} variant="error" icon={<FeatherX className="h-3 w-3" />}>
          {t("autonomous.topicDriven.statusFailed")}
        </Badge>
      );
    }
    return (
      <Badge className={cls} variant="brand" icon={<FeatherLoader className="h-3 w-3" />}>
        {t("autonomous.topicDriven.statusRunning")}
      </Badge>
    );
  };

  if (sessions.length === 0) {
    return (
      <div className="flex h-full w-full items-center justify-center bg-default-background">
        <div className="flex flex-col items-center gap-6 text-center">
          <FeatherFlaskConical className="h-12 w-12 text-neutral-300" />
          <button
            type="button"
            onClick={onNavigateToInput}
            className="text-xl font-semibold text-brand-600 hover:text-brand-700 transition-colors cursor-pointer hover:underline underline-offset-4"
          >
            {t("autonomous.topicDriven.emptyStateTitle")}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full w-full flex-col bg-default-background">
      <div className="flex-shrink-0 px-6 py-6">
        <button
          type="button"
          onClick={onNavigateToInput}
          className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-sm font-medium text-neutral-500 hover:bg-neutral-50 active:bg-neutral-100 transition-colors cursor-pointer"
        >
          <FeatherPlus className="h-4 w-4" />
          {t("autonomous.topicDriven.newSession")}
        </button>
      </div>
      <div className="flex-1 overflow-auto flex flex-col items-center px-6 pb-6">
        <div className="flex w-full max-w-[768px] flex-col items-start gap-6">
          <div className="flex w-full items-center gap-2 border-b border-solid border-neutral-border pb-3">
            <span className="grow shrink-0 basis-0 text-body-bold font-body-bold text-default-font">
              {t("autonomous.topicDriven.sessionCount", { count: filtered.length })}
            </span>
            <SubframeCore.DropdownMenu.Root>
              <SubframeCore.DropdownMenu.Trigger asChild>
                <Button
                  variant="neutral-secondary"
                  size="small"
                  icon={<FeatherArrowDownUp />}
                  iconRight={<FeatherChevronDown />}
                >
                  {t("autonomous.topicDriven.sort")}
                </Button>
              </SubframeCore.DropdownMenu.Trigger>
              <SubframeCore.DropdownMenu.Portal>
                <SubframeCore.DropdownMenu.Content side="bottom" align="end" sideOffset={4} asChild>
                  <DropdownMenu>
                    <DropdownMenu.DropdownItem icon={null} onSelect={() => setSortKey("newest")}>
                      {t("autonomous.topicDriven.sortNewest")}
                    </DropdownMenu.DropdownItem>
                    <DropdownMenu.DropdownItem icon={null} onSelect={() => setSortKey("oldest")}>
                      {t("autonomous.topicDriven.sortOldest")}
                    </DropdownMenu.DropdownItem>
                    <DropdownMenu.DropdownItem icon={null} onSelect={() => setSortKey("title")}>
                      {t("autonomous.topicDriven.sortTitle")}
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
                  {t("autonomous.topicDriven.noSessions")}
                </span>
                <button
                  type="button"
                  onClick={onNavigateToInput}
                  className="flex items-center gap-1.5 rounded-md bg-brand-600 px-3 py-1.5 text-sm font-medium text-white hover:bg-brand-700 transition-colors cursor-pointer"
                >
                  <FeatherPlus className="h-4 w-4" />
                  {t("autonomous.topicDriven.firstSession")}
                </button>
              </div>
            )}
            {filtered.map((session) => (
              <button
                key={session.id}
                type="button"
                className="flex w-full flex-col items-start gap-2 rounded-lg border border-solid border-neutral-border bg-default-background px-4 py-3 cursor-pointer hover:border-brand-300 hover:shadow-md transition-all text-left"
                onClick={() => onSelectSession(session)}
              >
                <div className="flex w-full items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FeatherFlaskConical className="text-body font-body text-brand-600" />
                    <span className="text-caption-bold font-caption-bold text-default-font">
                      {session.title}
                    </span>
                  </div>
                  {statusBadge(session.status)}
                </div>
                <div className="flex w-full items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="flex items-center gap-1">
                      <FeatherCalendar className="h-3 w-3 text-subtext-color" />
                      <span className="text-[11px] text-subtext-color">
                        {session.createdAt.toLocaleDateString(i18n.language, {
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
    </div>
  );
}
