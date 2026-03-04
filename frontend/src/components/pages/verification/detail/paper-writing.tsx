import { useCallback, useState } from "react";
import { Badge, Button, Checkbox, Loader } from "@/ui";
import type { ExperimentSetting, PaperDraft } from "../types";

interface PaperWritingSectionProps {
  experiments: ExperimentSetting[];
  paperDraft?: PaperDraft;
  onGeneratePaper: (selectedExperimentIds: string[]) => void;
}

export function PaperWritingSection({
  experiments,
  paperDraft,
  onGeneratePaper,
}: PaperWritingSectionProps) {
  const completedExperiments = experiments.filter((exp) => exp.status === "completed");
  const [selectedIds, setSelectedIds] = useState<string[]>(
    paperDraft?.selectedExperimentIds ?? completedExperiments.map((exp) => exp.id),
  );
  const [isGenerating, setIsGenerating] = useState(false);

  const handleToggle = useCallback((id: string) => {
    setSelectedIds((prev) => (prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]));
  }, []);

  const handleGenerate = useCallback(() => {
    setIsGenerating(true);
    onGeneratePaper(selectedIds);
  }, [selectedIds, onGeneratePaper]);

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <h2 className="text-lg font-semibold text-foreground">論文執筆</h2>
      <p className="text-sm text-muted-foreground mt-1">実験結果を基に論文ドラフトを生成します</p>

      <div className="mt-4">
        <h3 className="text-sm font-semibold text-foreground">含める実験を選択</h3>
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
        <div className="mt-4">
          <Button
            variant="brand-primary"
            onClick={handleGenerate}
            disabled={selectedIds.length === 0}
          >
            論文を生成
          </Button>
        </div>
      )}

      {isGenerating && !paperDraft && (
        <div className="mt-4 flex items-center gap-2">
          <Loader size="small" />
          <span className="text-sm text-muted-foreground">論文ドラフトを生成中...</span>
        </div>
      )}

      {paperDraft && (
        <div className="mt-4 rounded-md border border-border p-4">
          <div className="flex items-center gap-2">
            <h3 className="text-sm font-semibold text-foreground">{paperDraft.title}</h3>
            <Badge variant={paperDraft.status === "ready" ? "success" : "warning"}>
              {paperDraft.status === "ready" ? "生成完了" : "生成中"}
            </Badge>
          </div>
          {paperDraft.status === "ready" && (
            <div className="mt-3">
              <a
                href={paperDraft.overleafUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-brand-600 hover:underline"
              >
                Overleafで編集する
              </a>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
