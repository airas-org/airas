"use client";

import {
  Check,
  Download,
  Edit3,
  FileCode,
  FileText,
  Plus,
  Save,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useId, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Textarea } from "@/components/ui/textarea";
import { generateLaTeX, generatePaperText } from "@/lib/api-mock";
import type { ExperimentConfig, ExperimentResult, GeneratedPaper, Method } from "@/types/research";

interface PaperWritingSectionProps {
  method: Method | null;
  configs: ExperimentConfig[];
  results: ExperimentResult[];
  analysisText: string | null;
  generatedPaper: GeneratedPaper | null;
  onPaperGenerated: (paper: GeneratedPaper) => void;
  onStepExecuted?: (paper: GeneratedPaper) => void;
  onBranchCreated?: (paper: GeneratedPaper) => void;
  onSave?: () => void;
}

function SimpleMarkdown({ content }: { content: string }) {
  const lines = content.split("\n");
  const lineOccurrences = new Map<string, number>();
  return (
    <div className="space-y-2">
      {lines.map((line) => {
        const count = lineOccurrences.get(line) ?? 0;
        const occurrence = count + 1;
        lineOccurrences.set(line, occurrence);
        const key = `${line}-${occurrence}`;
        if (line.startsWith("## ")) {
          return (
            <h2 key={key} className="text-lg font-bold text-foreground mt-3">
              {line.slice(3)}
            </h2>
          );
        }
        if (line.startsWith("### ")) {
          return (
            <h3 key={key} className="text-base font-semibold text-foreground mt-2">
              {line.slice(4)}
            </h3>
          );
        }
        if (line.startsWith("- ")) {
          return (
            <li key={key} className="text-muted-foreground ml-4 text-sm">
              {line.slice(2)}
            </li>
          );
        }
        if (line.trim() === "") {
          return <div key={key} className="h-1" />;
        }
        return (
          <p key={key} className="text-muted-foreground text-sm">
            {line}
          </p>
        );
      })}
    </div>
  );
}

type ManualSection = { id: string; name: string; content: string };

interface ManualPaperInput {
  title: string;
  abstract: string;
  sections: ManualSection[];
}

const createSectionId = () =>
  typeof crypto !== "undefined" && "randomUUID" in crypto
    ? crypto.randomUUID()
    : `section-${Date.now()}-${Math.random().toString(16).slice(2)}`;

const createSection = (name = "", content = ""): ManualSection => ({
  id: createSectionId(),
  name,
  content,
});

export function PaperWritingSection({
  method,
  configs,
  results,
  analysisText,
  generatedPaper,
  onPaperGenerated,
  onStepExecuted,
  onBranchCreated,
  onSave,
}: PaperWritingSectionProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [latex, setLatex] = useState<string | null>(null);
  const [isManualMode, setIsManualMode] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [previewPaper, setPreviewPaper] = useState<GeneratedPaper | null>(null);
  const [isConfirmed, setIsConfirmed] = useState(false);
  const [manualInput, setManualInput] = useState<ManualPaperInput>({
    title: "",
    abstract: "",
    sections: [
      createSection("Introduction"),
      createSection("Related Work"),
      createSection("Methods"),
      createSection("Experiments"),
      createSection("Conclusion"),
    ],
  });
  const manualTitleId = useId();
  const manualAbstractId = useId();

  const canGenerate = method && configs.length > 0 && results.length > 0 && analysisText;

  const handleGenerate = async () => {
    if (!canGenerate) return;
    setIsGenerating(true);
    try {
      const paper = await generatePaperText(method, configs, results, analysisText);
      setPreviewPaper(paper);
      const generatedLatex = await generateLaTeX(paper);
      setLatex(generatedLatex);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleConfirm = () => {
    if (!previewPaper) return;
    onPaperGenerated(previewPaper);
    setIsConfirmed(true);
    if (onStepExecuted) {
      onStepExecuted(previewPaper);
    }
    if (onSave) {
      onSave();
    }
  };

  const handleManualSave = async () => {
    if (!manualInput.title.trim() || !manualInput.abstract.trim()) return;
    const cleanedSections = manualInput.sections
      .filter((s) => s.name.trim() && s.content.trim())
      .map(({ name, content }) => ({ name, content }));
    const paper: GeneratedPaper = {
      title: manualInput.title,
      abstract: manualInput.abstract,
      sections: cleanedSections,
    };
    onPaperGenerated(paper);
    const generatedLatex = await generateLaTeX(paper);
    setLatex(generatedLatex);
    setIsEditing(false);
    if (!isConfirmed && onStepExecuted) {
      onStepExecuted(paper);
      setIsConfirmed(true);
    } else if (isConfirmed && onBranchCreated) {
      onBranchCreated(paper);
    }
    if (onSave) {
      onSave();
    }
  };

  const handleEdit = () => {
    const paperToEdit = generatedPaper || previewPaper;
    if (paperToEdit) {
      setManualInput({
        title: paperToEdit.title,
        abstract: paperToEdit.abstract,
        sections: paperToEdit.sections.map((section) =>
          createSection(section.name, section.content),
        ),
      });
    }
    setIsEditing(true);
  };

  const handleStartManualInput = () => {
    setIsManualMode(true);
    setIsEditing(true);
  };

  const handleSectionChange = (index: number, field: "name" | "content", value: string) => {
    const updated = [...manualInput.sections];
    updated[index] = { ...updated[index], [field]: value };
    setManualInput({ ...manualInput, sections: updated });
  };

  const handleAddSection = () => {
    setManualInput({
      ...manualInput,
      sections: [...manualInput.sections, createSection()],
    });
  };

  const handleRemoveSection = (index: number) => {
    setManualInput({
      ...manualInput,
      sections: manualInput.sections.filter((_, i) => i !== index),
    });
  };

  const displayPaper = generatedPaper || previewPaper;

  if (generatedPaper && !isConfirmed) {
    setIsConfirmed(true);
  }

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-blue-700 flex items-center justify-center">
          <FileText className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground">論文の作成</h3>
          <p className="text-sm text-muted-foreground">研究成果をまとめた論文を自動生成</p>
        </div>
      </div>

      {!displayPaper && !isEditing && (
        <div className="flex gap-2 mb-6">
          <Button
            variant={!isManualMode ? "default" : "outline"}
            size="sm"
            onClick={() => setIsManualMode(false)}
            className={
              !isManualMode ? "bg-blue-700 hover:bg-blue-800 text-white" : "bg-transparent"
            }
          >
            実験結果から生成
          </Button>
          <Button
            variant={isManualMode ? "default" : "outline"}
            size="sm"
            onClick={handleStartManualInput}
            className={isManualMode ? "bg-blue-700 hover:bg-blue-800 text-white" : "bg-transparent"}
          >
            手動で入力
          </Button>
        </div>
      )}

      {isEditing && (
        <div className="space-y-6">
          <div>
            <label
              className="text-sm font-medium text-foreground mb-2 block"
              htmlFor={manualTitleId}
            >
              論文タイトル
            </label>
            <Input
              id={manualTitleId}
              value={manualInput.title}
              onChange={(e) => setManualInput({ ...manualInput, title: e.target.value })}
              placeholder="例: A Novel Approach to Graph Neural Networks"
              className="bg-background"
            />
          </div>
          <div>
            <label
              className="text-sm font-medium text-foreground mb-2 block"
              htmlFor={manualAbstractId}
            >
              アブストラクト
            </label>
            <Textarea
              id={manualAbstractId}
              value={manualInput.abstract}
              onChange={(e) => setManualInput({ ...manualInput, abstract: e.target.value })}
              placeholder="研究の概要を入力..."
              className="min-h-[120px] bg-background"
            />
          </div>
          <div className="space-y-4">
            <p className="text-sm font-medium text-foreground">セクション</p>
            {manualInput.sections.map((section, index) => {
              const sectionNameId = `${section.id}-name`;
              const sectionContentId = `${section.id}-content`;
              return (
                <div key={section.id} className="p-4 border border-border rounded-lg space-y-3">
                  <div className="flex items-center gap-2">
                    <Input
                      id={sectionNameId}
                      value={section.name}
                      onChange={(e) => handleSectionChange(index, "name", e.target.value)}
                      placeholder="セクション名"
                      className="flex-1 bg-background"
                    />
                    <Button variant="ghost" size="sm" onClick={() => handleRemoveSection(index)}>
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </Button>
                  </div>
                  <Textarea
                    id={sectionContentId}
                    value={section.content}
                    onChange={(e) => handleSectionChange(index, "content", e.target.value)}
                    placeholder="セクション内容..."
                    className="min-h-[100px] bg-background"
                  />
                </div>
              );
            })}
            <Button variant="outline" onClick={handleAddSection} className="w-full bg-transparent">
              <Plus className="w-4 h-4 mr-2" />
              セクションを追加
            </Button>
          </div>
          <div className="flex gap-2 justify-end">
            <Button
              variant="outline"
              onClick={() => setIsEditing(false)}
              className="bg-transparent"
            >
              キャンセル
            </Button>
            <Button
              onClick={handleManualSave}
              disabled={!manualInput.title.trim() || !manualInput.abstract.trim()}
              className="bg-blue-700 hover:bg-blue-800 text-white"
            >
              <Save className="w-4 h-4 mr-2" />
              保存
            </Button>
          </div>
        </div>
      )}

      {!isManualMode &&
        !isEditing &&
        !displayPaper &&
        (!canGenerate ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>全ての前工程を完了するか、手動入力モードを使用してください</p>
          </div>
        ) : (
          <Button
            onClick={handleGenerate}
            disabled={isGenerating}
            className="w-full bg-blue-700 hover:bg-blue-800 text-white"
          >
            <Sparkles className="w-4 h-4 mr-2" />
            {isGenerating ? "生成中..." : "論文を生成"}
          </Button>
        ))}

      {displayPaper && !isEditing && (
        <div className="space-y-6">
          <div className="flex justify-end">
            <Button variant="ghost" size="sm" onClick={handleEdit}>
              <Edit3 className="w-4 h-4 mr-1" />
              編集
            </Button>
          </div>
          <Tabs defaultValue="preview" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="preview">プレビュー</TabsTrigger>
              <TabsTrigger value="latex">LaTeX</TabsTrigger>
            </TabsList>

            <TabsContent value="preview" className="mt-4">
              <div className="bg-card border border-border rounded-lg p-8 shadow-sm">
                <h1 className="text-2xl font-bold text-foreground text-center mb-4">
                  {displayPaper.title}
                </h1>
                <div className="text-center text-sm text-muted-foreground mb-6">Research Team</div>
                <div className="mb-8">
                  <h2 className="text-sm font-semibold text-muted-foreground uppercase tracking-wide mb-2">
                    Abstract
                  </h2>
                  <p className="text-muted-foreground text-sm leading-relaxed italic">
                    {displayPaper.abstract}
                  </p>
                </div>
                <div className="space-y-6">
                  {displayPaper.sections.map((section, index) => {
                    const sectionKey = `${section.name}-${section.content.slice(0, 16)}`;
                    return (
                      <div key={sectionKey}>
                        <h2 className="text-lg font-semibold text-foreground mb-2">
                          {index + 1}. {section.name}
                        </h2>
                        <SimpleMarkdown content={section.content} />
                      </div>
                    );
                  })}
                </div>
              </div>
            </TabsContent>

            <TabsContent value="latex" className="mt-4">
              {latex && (
                <div className="bg-secondary rounded-lg p-4 overflow-x-auto">
                  <pre className="text-sm text-secondary-foreground font-mono whitespace-pre-wrap">
                    {latex}
                  </pre>
                </div>
              )}
            </TabsContent>
          </Tabs>

          {!isConfirmed && previewPaper && (
            <Button
              onClick={handleConfirm}
              className="w-full bg-blue-700 hover:bg-blue-800 text-white"
            >
              <Check className="w-4 h-4 mr-2" />
              この論文を確定
            </Button>
          )}

          {isConfirmed && (
            <div className="flex items-center justify-center gap-2 p-3 bg-muted rounded-lg">
              <Check className="w-5 h-5 text-blue-700" />
              <span className="text-sm text-muted-foreground">確定済み</span>
            </div>
          )}

          <div className="flex gap-3">
            <Button variant="outline" className="flex-1 bg-transparent">
              <FileCode className="w-4 h-4 mr-2" />
              LaTeXをダウンロード
            </Button>
            <Button className="flex-1">
              <Download className="w-4 h-4 mr-2" />
              PDFをダウンロード
            </Button>
          </div>
        </div>
      )}
    </Card>
  );
}
