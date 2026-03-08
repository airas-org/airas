import { FeatherSearch } from "@subframe/core";
import { useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import type { Verification } from "../types";
import { VerificationCard } from "./verification-card";

interface VerificationHomePageProps {
  verifications: Verification[];
  onSelectVerification: (id: string) => void;
  onDeleteVerification: (id: string) => void;
  onDuplicateVerification: (id: string) => void;
}

interface CategoryColumnProps {
  label: string;
  count: number;
  verifications: Verification[];
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  onDuplicate: (id: string) => void;
}

function CategoryColumn({
  label,
  count,
  verifications,
  onSelect,
  onDelete,
  onDuplicate,
}: CategoryColumnProps) {
  return (
    <div className="w-[200px] shrink-0 rounded-lg border border-border bg-card p-2.5">
      <div className="flex items-center gap-1.5 mb-2">
        <h2 className="text-[10px] font-semibold text-subtext-color uppercase tracking-wider whitespace-nowrap">
          {label}
        </h2>
        <span className="flex h-4 min-w-[16px] items-center justify-center rounded-full bg-neutral-200 px-1 text-[9px] font-medium text-neutral-600">
          {count}
        </span>
      </div>
      <div className="flex flex-col gap-1.5">
        {verifications.map((v) => (
          <VerificationCard
            key={v.id}
            verification={v}
            onClick={() => onSelect(v.id)}
            onDelete={() => onDelete(v.id)}
            onDuplicate={() => onDuplicate(v.id)}
          />
        ))}
        {verifications.length === 0 && (
          <p className="py-6 text-center text-caption font-caption text-neutral-400">No items</p>
        )}
      </div>
    </div>
  );
}

type CategoryKey =
  | "hypothesis"
  | "plan-decided"
  | "implementation-done"
  | "experiments-done"
  | "paper-done";

function getCategoryKey(v: Verification): CategoryKey {
  switch (v.phase) {
    case "initial":
    case "methods-proposed":
      return "hypothesis";
    case "plan-generated":
      return "plan-decided";
    case "code-generating":
    case "code-generated":
      return "implementation-done";
    case "experiments-done":
      return "experiments-done";
    case "paper-writing":
      return v.paperDraft?.status === "ready" ? "paper-done" : "experiments-done";
  }
}

export function VerificationHomePage({
  verifications,
  onSelectVerification,
  onDeleteVerification,
  onDuplicateVerification,
}: VerificationHomePageProps) {
  const { t } = useTranslation();
  const categories: { key: CategoryKey; label: string }[] = [
    { key: "hypothesis", label: t("verification.home.categories.hypothesis") },
    { key: "plan-decided", label: t("verification.home.categories.planDecided") },
    { key: "implementation-done", label: t("verification.home.categories.implementationDone") },
    { key: "experiments-done", label: t("verification.home.categories.experimentsDone") },
    { key: "paper-done", label: t("verification.home.categories.paperDone") },
  ];
  const [search, setSearch] = useState("");

  const filtered = search
    ? verifications.filter(
        (v) =>
          v.title.toLowerCase().includes(search.toLowerCase()) ||
          v.query.toLowerCase().includes(search.toLowerCase()),
      )
    : verifications;

  const grouped = useMemo(() => {
    const map: Record<CategoryKey, Verification[]> = {
      hypothesis: [],
      "plan-decided": [],
      "implementation-done": [],
      "experiments-done": [],
      "paper-done": [],
    };
    for (const v of filtered) {
      map[getCategoryKey(v)].push(v);
    }
    return map;
  }, [filtered]);

  return (
    <div className="flex-1 overflow-y-auto overflow-x-clip min-w-0">
      <div className="max-w-full mx-auto px-6 py-6">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h1 className="text-heading-2 font-heading-2 text-default-font">
              {t("verification.home.title")}
            </h1>
            <p className="text-caption font-caption text-subtext-color mt-1">
              {t("verification.home.projects", { count: verifications.length })}
            </p>
          </div>
          <div className="w-56 rounded-lg border border-border bg-card px-3 py-1.5 flex items-center gap-2">
            <FeatherSearch className="h-4 w-4 text-subtext-color shrink-0" />
            <input
              type="text"
              placeholder={t("verification.home.searchPlaceholder")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-transparent text-body font-body text-default-font outline-none placeholder:text-neutral-400"
            />
          </div>
        </div>

        <div className="mt-6 flex gap-2 items-start overflow-x-auto">
          {categories.map((cat) => (
            <CategoryColumn
              key={cat.key}
              label={cat.label}
              count={grouped[cat.key].length}
              verifications={grouped[cat.key]}
              onSelect={onSelectVerification}
              onDelete={onDeleteVerification}
              onDuplicate={onDuplicateVerification}
            />
          ))}
        </div>
      </div>
    </div>
  );
}
