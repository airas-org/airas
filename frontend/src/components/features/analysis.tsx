"use client";

import { BarChart3, Check, Sparkles } from "lucide-react";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { analyzeResults } from "@/lib/api-mock";
import type { ExperimentResult } from "@/types/research";

interface AnalysisSectionProps {
  results: ExperimentResult[];
  analysisText: string | null;
  onAnalysisGenerated: (text: string) => void;
  onStepExecuted?: (text: string) => void;
  onSave?: () => void;
}

function SimpleMarkdown({ content }: { content: string }) {
  const lines = content.split("\n");
  const lineOccurrences = new Map<string, number>();
  return (
    <div className="space-y-3">
      {lines.map((line) => {
        const count = lineOccurrences.get(line) ?? 0;
        const occurrence = count + 1;
        lineOccurrences.set(line, occurrence);
        const key = `${line}-${occurrence}`;
        if (line.startsWith("## ")) {
          return (
            <h2 key={key} className="text-xl font-bold text-foreground mt-4">
              {line.slice(3)}
            </h2>
          );
        }
        if (line.startsWith("### ")) {
          return (
            <h3 key={key} className="text-lg font-semibold text-foreground mt-3">
              {line.slice(4)}
            </h3>
          );
        }
        if (line.startsWith("- ")) {
          return (
            <li key={key} className="text-muted-foreground ml-4">
              {line.slice(2)}
            </li>
          );
        }
        if (line.match(/^\d+\./)) {
          return (
            <p key={key} className="text-muted-foreground font-medium">
              {line}
            </p>
          );
        }
        if (line.trim() === "") {
          return <div key={key} className="h-2" />;
        }
        return (
          <p key={key} className="text-muted-foreground">
            {line}
          </p>
        );
      })}
    </div>
  );
}

export function AnalysisSection({
  results,
  analysisText,
  onAnalysisGenerated,
  onStepExecuted,
  onSave,
}: AnalysisSectionProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [previewText, setPreviewText] = useState<string | null>(null);
  const [isConfirmed, setIsConfirmed] = useState(false);

  const handleAnalyze = async () => {
    if (results.length === 0) return;
    setIsAnalyzing(true);
    try {
      const analysis = await analyzeResults(results);
      setPreviewText(analysis);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleConfirm = () => {
    if (!previewText) return;
    onAnalysisGenerated(previewText);
    setIsConfirmed(true);
    if (onStepExecuted) {
      onStepExecuted(previewText);
    }
    if (onSave) {
      onSave();
    }
  };

  const completedResults = results.filter((r) => r.status === "completed");
  const displayText = analysisText || previewText;

  if (analysisText && !isConfirmed) {
    setIsConfirmed(true);
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-blue-700 flex items-center justify-center">
          <BarChart3 className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground">実験結果の分析</h3>
          <p className="text-sm text-muted-foreground">実験結果を分析し洞察を導出</p>
        </div>
      </div>

      {completedResults.length === 0 ? (
        <div className="text-center py-8 text-muted-foreground">
          <BarChart3 className="w-12 h-12 mx-auto mb-3 opacity-50" />
          <p>先に実験を実行してください</p>
        </div>
      ) : (
        <>
          {!displayText && (
            <div className="space-y-4">
              <div className="p-4 bg-muted rounded-lg">
                <p className="text-sm text-muted-foreground">
                  {completedResults.length} 件の実験結果を分析します
                </p>
              </div>
              <Button
                onClick={handleAnalyze}
                disabled={isAnalyzing}
                className="w-full bg-blue-700 hover:bg-blue-800 text-white"
              >
                <Sparkles className="w-4 h-4 mr-2" />
                {isAnalyzing ? "分析中..." : "結果を分析"}
              </Button>
            </div>
          )}

          {displayText && (
            <div className="space-y-4">
              <div className="p-4 bg-muted rounded-lg">
                <SimpleMarkdown content={displayText} />
              </div>

              {!isConfirmed && previewText && (
                <Button
                  onClick={handleConfirm}
                  className="w-full bg-blue-700 hover:bg-blue-800 text-white"
                >
                  <Check className="w-4 h-4 mr-2" />
                  この分析を確定
                </Button>
              )}

              {isConfirmed && (
                <div className="flex items-center justify-center gap-2 p-3 bg-muted rounded-lg">
                  <Check className="w-5 h-5 text-blue-700" />
                  <span className="text-sm text-muted-foreground">確定済み</span>
                </div>
              )}
            </div>
          )}
        </>
      )}
    </Card>
  );
}
