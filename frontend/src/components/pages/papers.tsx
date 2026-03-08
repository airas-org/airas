"use client";

import { useTranslation } from "react-i18next";
import { PaperSearchSection } from "@/components/features/paper-search";
import { cn } from "@/lib/utils";
import type { Paper } from "@/types/research";

interface PapersPageProps {
  selectedPapers: Paper[];
  onPapersChange: (papers: Paper[]) => void;
  onStepExecuted: (papers: Paper[]) => void;
  onSave: () => void;
}

export function PapersPage({
  selectedPapers,
  onPapersChange,
  onStepExecuted,
  onSave,
}: PapersPageProps) {
  const { t } = useTranslation();
  return (
    <div className="flex-1 bg-background overflow-y-auto">
      <div className="sticky top-0 z-10 border-b border-border bg-card px-6 py-4">
        <h2 className="text-lg font-semibold text-foreground">{t("papers.acquisitionTitle")}</h2>
        <p className="text-sm text-muted-foreground">{t("papers.acquisitionSubtitle")}</p>
      </div>
      <div className="p-6">
        <div id="papers" className={cn("scroll-mt-20")}>
          <PaperSearchSection
            selectedPapers={selectedPapers}
            onPapersChange={onPapersChange}
            onStepExecuted={onStepExecuted}
            onSave={onSave}
          />
        </div>
      </div>
    </div>
  );
}
