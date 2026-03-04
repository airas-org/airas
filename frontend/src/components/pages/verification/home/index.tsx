import { FeatherSearch } from "@subframe/core";
import { useState } from "react";
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
    <div className="flex-1 min-w-0 rounded-lg border border-border bg-card p-4">
      <div className="flex items-center gap-2 mb-3">
        <h2 className="text-caption-bold font-caption-bold text-subtext-color uppercase tracking-wider">
          {label}
        </h2>
        <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-neutral-200 px-1.5 text-[10px] font-medium text-neutral-600">
          {count}
        </span>
      </div>
      <div className="flex flex-col gap-2">
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

export function VerificationHomePage({
  verifications,
  onSelectVerification,
  onDeleteVerification,
  onDuplicateVerification,
}: VerificationHomePageProps) {
  const [search, setSearch] = useState("");

  const filtered = search
    ? verifications.filter(
        (v) =>
          v.title.toLowerCase().includes(search.toLowerCase()) ||
          v.query.toLowerCase().includes(search.toLowerCase()),
      )
    : verifications;

  const drafts = filtered.filter((v) => v.phase === "initial");
  const active = filtered.filter(
    (v) => v.phase !== "initial" && v.phase !== "experiments-done" && v.phase !== "paper-writing",
  );
  const completed = filtered.filter(
    (v) => v.phase === "experiments-done" || v.phase === "paper-writing",
  );

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-6xl mx-auto px-8 py-8">
        <div className="flex items-end justify-between gap-4">
          <div>
            <h1 className="text-heading-2 font-heading-2 text-default-font">Verifications</h1>
            <p className="text-caption font-caption text-subtext-color mt-1">
              {verifications.length} projects
            </p>
          </div>
          <div className="w-56 rounded-lg border border-border bg-card px-3 py-1.5 flex items-center gap-2">
            <FeatherSearch className="h-4 w-4 text-subtext-color shrink-0" />
            <input
              type="text"
              placeholder="Search..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full bg-transparent text-body font-body text-default-font outline-none placeholder:text-neutral-400"
            />
          </div>
        </div>

        <div className="mt-6 flex gap-4 items-start">
          <CategoryColumn
            label="Drafts"
            count={drafts.length}
            verifications={drafts}
            onSelect={onSelectVerification}
            onDelete={onDeleteVerification}
            onDuplicate={onDuplicateVerification}
          />
          <CategoryColumn
            label="In Progress"
            count={active.length}
            verifications={active}
            onSelect={onSelectVerification}
            onDelete={onDeleteVerification}
            onDuplicate={onDuplicateVerification}
          />
          <CategoryColumn
            label="Completed"
            count={completed.length}
            verifications={completed}
            onSelect={onSelectVerification}
            onDelete={onDeleteVerification}
            onDuplicate={onDuplicateVerification}
          />
        </div>
      </div>
    </div>
  );
}
