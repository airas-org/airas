import { useCallback, useState } from "react";
import { useTranslation } from "react-i18next";
import { Checkbox } from "@/ui";
import type { ExperimentSetting, PaperDraft } from "../types";

interface PaperWritingSectionProps {
  experiments: ExperimentSetting[];
  paperDraft?: PaperDraft;
  isGenerating: boolean;
  onGeneratePaper: (selectedExperimentIds: string[]) => void;
}

export function PaperWritingSection({
  experiments,
  paperDraft,
  isGenerating,
  onGeneratePaper,
}: PaperWritingSectionProps) {
  const { t } = useTranslation();
  const completedExperiments = experiments.filter((exp) => exp.status === "completed");
  const [selectedIds, setSelectedIds] = useState<string[]>(
    paperDraft?.selectedExperimentIds ?? completedExperiments.map((exp) => exp.id),
  );

  const handleToggle = useCallback((id: string) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }, []);

  const handleGenerate = useCallback(() => {
    onGeneratePaper(selectedIds);
  }, [selectedIds, onGeneratePaper]);

  return (
    <>
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="text-lg font-semibold text-foreground">
          {t("verification.detail.paperWriting.title")}
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          {t("verification.detail.paperWriting.subtitle")}
        </p>

        <div className="mt-4">
          <h3 className="text-sm font-semibold text-foreground">
            {t("verification.detail.paperWriting.selectExperiments")}
          </h3>
          <div className="mt-2 space-y-2">
            {completedExperiments.map((exp) => (
              <Checkbox
                key={exp.id}
                label={`${exp.title} - ${exp.result?.summary ?? ""}`}
                checked={selectedIds.includes(exp.id)}
                onCheckedChange={() => handleToggle(exp.id)}
              />
            ))}
          </div>
        </div>

        {!paperDraft && !isGenerating && (
          <div className="mt-5 flex justify-end">
            <button
              type="button"
              onClick={handleGenerate}
              disabled={selectedIds.length === 0}
              className="rounded-md bg-neutral-200 px-3 py-1.5 text-xs font-medium text-neutral-700 hover:bg-neutral-300 hover:text-neutral-900 transition-colors cursor-pointer disabled:opacity-50 disabled:cursor-default"
            >
              {t("verification.detail.paperWriting.generatePaper")}
            </button>
          </div>
        )}
      </div>

      {paperDraft && (
        <div id="sec-generated-paper" className="rounded-lg border border-border bg-card p-6">
          <h2 className="text-lg font-semibold text-foreground">
            {t("verification.detail.paper.title")}
          </h2>
          <div className="mt-3 flex items-center gap-2">
            <span className="text-sm font-medium text-foreground">GitHub URL:</span>
            <a
              href={paperDraft.paperUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-brand-600 hover:underline"
            >
              {paperDraft.paperUrl}
            </a>
          </div>
          <div className="mt-3 flex justify-end">
            <a
              href={paperDraft.overleafUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-md bg-neutral-200 px-3 py-1.5 text-xs font-medium text-neutral-700 hover:bg-neutral-300 hover:text-neutral-900 transition-colors"
            >
              Edit on Overleaf
            </a>
          </div>
        </div>
      )}
    </>
  );
}
