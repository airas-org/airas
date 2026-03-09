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
import { useTranslation } from "react-i18next";
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
}

export function HypothesisDrivenList({
  sessions,
  onSelectSession,
  onNavigateToInput,
}: HypothesisDrivenListProps) {
  const { t, i18n } = useTranslation();
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
    const cls = "text-[11px] py-0 px-1.5";
    if (status === "completed") {
      return (
        <Badge className={cls} variant="success" icon={<FeatherCheck className="h-3 w-3" />}>
          {t("autonomous.hypothesisDriven.statusCompleted")}
        </Badge>
      );
    }
    if (status === "failed") {
      return (
        <Badge className={cls} variant="error" icon={<FeatherX className="h-3 w-3" />}>
          {t("autonomous.hypothesisDriven.statusFailed")}
        </Badge>
      );
    }
    return (
      <Badge className={cls} variant="brand" icon={<FeatherLoader className="h-3 w-3" />}>
        {t("autonomous.hypothesisDriven.statusRunning")}
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
            {t("autonomous.hypothesisDriven.listHeading")}
          </span>
          <span className="text-body font-body text-subtext-color text-center">
            {t("autonomous.hypothesisDriven.listSubtitle")}
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
              placeholder={t("autonomous.hypothesisDriven.searchPlaceholder")}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </TextField>
          <Button variant="brand-primary" icon={<FeatherPlus />} onClick={onNavigateToInput}>
            {t("autonomous.hypothesisDriven.newSession")}
          </Button>
        </div>
        <div className="flex w-full items-center gap-2 border-b border-solid border-neutral-border pb-3">
          <span className="grow shrink-0 basis-0 text-body-bold font-body-bold text-default-font">
            {t("autonomous.hypothesisDriven.sessionCount", { count: filtered.length })}
          </span>
          <SubframeCore.DropdownMenu.Root>
            <SubframeCore.DropdownMenu.Trigger asChild>
              <Button
                variant="neutral-secondary"
                size="small"
                icon={<FeatherArrowDownUp />}
                iconRight={<FeatherChevronDown />}
              >
                {t("autonomous.hypothesisDriven.sort")}
              </Button>
            </SubframeCore.DropdownMenu.Trigger>
            <SubframeCore.DropdownMenu.Portal>
              <SubframeCore.DropdownMenu.Content side="bottom" align="end" sideOffset={4} asChild>
                <DropdownMenu>
                  <DropdownMenu.DropdownItem icon={null} onSelect={() => setSortKey("newest")}>
                    {t("autonomous.hypothesisDriven.sortNewest")}
                  </DropdownMenu.DropdownItem>
                  <DropdownMenu.DropdownItem icon={null} onSelect={() => setSortKey("oldest")}>
                    {t("autonomous.hypothesisDriven.sortOldest")}
                  </DropdownMenu.DropdownItem>
                  <DropdownMenu.DropdownItem icon={null} onSelect={() => setSortKey("title")}>
                    {t("autonomous.hypothesisDriven.sortTitle")}
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
                  ? t("autonomous.hypothesisDriven.noSearchResults")
                  : t("autonomous.hypothesisDriven.noSessions")}
              </span>
              {!searchQuery.trim() && (
                <Button variant="brand-primary" icon={<FeatherPlus />} onClick={onNavigateToInput}>
                  {t("autonomous.hypothesisDriven.firstSession")}
                </Button>
              )}
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
  );
}
