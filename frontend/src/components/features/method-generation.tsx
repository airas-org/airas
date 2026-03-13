import { Edit3, FileText, Lightbulb, Save, Sparkles } from "lucide-react";
import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import { generateMethod } from "@/lib/api-mock";
import type { Method, Paper } from "@/types/research";
import { Button, Card, TextArea, TextField } from "@/ui";

interface MethodGenerationSectionProps {
  selectedPapers: Paper[];
  generatedMethod: Method | null;
  onMethodGenerated: (method: Method) => void;
  onStepExecuted?: (method: Method) => void;
  onBranchCreated?: (method: Method) => void;
  onSave?: () => void;
}

export function MethodGenerationSection({
  selectedPapers,
  generatedMethod,
  onMethodGenerated,
  onStepExecuted,
  onBranchCreated,
  onSave,
}: MethodGenerationSectionProps) {
  const { t } = useTranslation();
  const [isGenerating, setIsGenerating] = useState(false);
  const [editedDescription, setEditedDescription] = useState("");
  const [isManualMode, setIsManualMode] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [manualMethodName, setManualMethodName] = useState("");
  const [manualMethodDescription, setManualMethodDescription] = useState("");
  const [hasExecuted, setHasExecuted] = useState(false);
  const [tempMethod, setTempMethod] = useState<Method | null>(null);
  const manualMethodNameId = useId();
  const manualMethodDescriptionId = useId();
  const previewDescriptionId = useId();
  const editMethodNameId = useId();
  const editMethodDescriptionId = useId();

  const handleGenerate = async () => {
    if (selectedPapers.length === 0) return;
    setIsGenerating(true);
    try {
      const method = await generateMethod(selectedPapers.map((p) => p.id));
      setTempMethod(method);
      setEditedDescription(method.description);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleConfirmGenerated = () => {
    if (!tempMethod) return;
    const methodToSave = { ...tempMethod, description: editedDescription };
    onMethodGenerated(methodToSave);
    if (!hasExecuted && onStepExecuted) {
      onStepExecuted(methodToSave);
      setHasExecuted(true);
    }
    if (onSave) {
      onSave();
    }
    setTempMethod(null);
  };

  const handleDescriptionChange = (value: string) => {
    setEditedDescription(value);
    if (tempMethod) {
      setTempMethod({ ...tempMethod, description: value });
    }
  };

  const handleManualSave = () => {
    if (!manualMethodName.trim() || !manualMethodDescription.trim()) return;
    const manualMethod: Method = {
      id: `manual-${Date.now()}`,
      name: manualMethodName,
      description: manualMethodDescription,
      basedOn: [],
    };
    onMethodGenerated(manualMethod);
    setEditedDescription(manualMethodDescription);
    setIsEditing(false);
    if (!hasExecuted && onStepExecuted) {
      onStepExecuted(manualMethod);
      setHasExecuted(true);
    } else if (hasExecuted && onBranchCreated) {
      onBranchCreated(manualMethod);
    }
    if (onSave) {
      onSave();
    }
  };

  const handleEdit = () => {
    setIsEditing(true);
    if (generatedMethod) {
      setManualMethodName(generatedMethod.name);
      setManualMethodDescription(generatedMethod.description);
    }
  };

  const handleSaveEdit = () => {
    if (!manualMethodName.trim() || !manualMethodDescription.trim()) return;
    const updatedMethod: Method = {
      id: `edited-${Date.now()}`,
      name: manualMethodName,
      description: manualMethodDescription,
      basedOn: generatedMethod?.basedOn || [],
    };
    onMethodGenerated(updatedMethod);
    setIsEditing(false);
    if (onBranchCreated) {
      onBranchCreated(updatedMethod);
    }
    if (onSave) {
      onSave();
    }
  };

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-blue-700 flex items-center justify-center">
          <Lightbulb className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground">
            {t("features.methodGeneration.title")}
          </h3>
          <p className="text-sm text-muted-foreground">{t("features.methodGeneration.subtitle")}</p>
        </div>
      </div>

      {!generatedMethod && !tempMethod && (
        <div className="flex gap-2 mb-6">
          <Button
            variant={!isManualMode ? "brand-primary" : "neutral-secondary"}
            size="small"
            onClick={() => setIsManualMode(false)}
            className={
              !isManualMode ? "bg-blue-700 hover:bg-blue-800 text-white" : "bg-transparent"
            }
          >
            {t("features.methodGeneration.generateFromPapers")}
          </Button>
          <Button
            variant={isManualMode ? "brand-primary" : "neutral-secondary"}
            size="small"
            onClick={() => setIsManualMode(true)}
            className={isManualMode ? "bg-blue-700 hover:bg-blue-800 text-white" : "bg-transparent"}
          >
            {t("features.methodGeneration.manualInput")}
          </Button>
        </div>
      )}

      {isManualMode && !generatedMethod && !tempMethod && (
        <div className="space-y-4">
          <div>
            <label
              className="text-sm font-medium text-foreground mb-2 block"
              htmlFor={manualMethodNameId}
            >
              {t("features.methodGeneration.methodName")}
            </label>
            <TextField>
              <TextField.Input
                id={manualMethodNameId}
                value={manualMethodName}
                onChange={(e) => setManualMethodName(e.target.value)}
                placeholder="例: Attention-based Graph Neural Network"
              />
            </TextField>
          </div>
          <div>
            <label
              className="text-sm font-medium text-foreground mb-2 block"
              htmlFor={manualMethodDescriptionId}
            >
              {t("features.methodGeneration.methodDescription")}
            </label>
            <TextArea>
              <TextArea.Input
                id={manualMethodDescriptionId}
                value={manualMethodDescription}
                onChange={(e) => setManualMethodDescription(e.target.value)}
                placeholder={t("features.methodGeneration.descriptionPlaceholder")}
                className="min-h-[200px] font-mono text-sm"
              />
            </TextArea>
          </div>
          <Button
            onClick={handleManualSave}
            disabled={!manualMethodName.trim() || !manualMethodDescription.trim()}
            className="w-full bg-blue-700 hover:bg-blue-800 text-white"
          >
            <Save className="w-4 h-4 mr-2" />
            {t("common.save")}
          </Button>
        </div>
      )}

      {!isManualMode &&
        !generatedMethod &&
        !tempMethod &&
        (selectedPapers.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <FileText className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>{t("features.methodGeneration.noPapersMessage")}</p>
          </div>
        ) : (
          <>
            <div className="mb-6">
              <p className="text-sm text-muted-foreground mb-3">
                {t("features.methodGeneration.paperCountMessage", { count: selectedPapers.length })}
              </p>
              <div className="flex flex-wrap gap-2">
                {selectedPapers.map((paper) => (
                  <span
                    key={paper.id}
                    className="px-3 py-1 bg-muted rounded-full text-sm text-foreground"
                  >
                    {paper.title.substring(0, 30)}...
                  </span>
                ))}
              </div>
            </div>
            <Button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full bg-blue-700 hover:bg-blue-800 text-white"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              {isGenerating
                ? t("features.methodGeneration.generating")
                : t("features.methodGeneration.generate")}
            </Button>
          </>
        ))}

      {tempMethod && !generatedMethod && (
        <div className="space-y-4">
          <div className="p-4 bg-muted/50 border border-border rounded-lg">
            <p className="text-sm text-muted-foreground mb-2">
              {t("features.methodGeneration.generatedPreview")}
            </p>
            <p className="text-lg font-semibold text-foreground mb-2">{tempMethod.name}</p>
            <div>
              <label
                className="text-sm font-medium text-foreground mb-2 block"
                htmlFor={previewDescriptionId}
              >
                {t("features.methodGeneration.editableDescription")}
              </label>
              <TextArea>
                <TextArea.Input
                  id={previewDescriptionId}
                  value={editedDescription}
                  onChange={(e) => handleDescriptionChange(e.target.value)}
                  className="min-h-[200px] font-mono text-sm"
                />
              </TextArea>
            </div>
          </div>
          <Button
            onClick={handleConfirmGenerated}
            className="w-full bg-blue-700 hover:bg-blue-800 text-white"
          >
            <Save className="w-4 h-4 mr-2" />
            {t("features.methodGeneration.confirmMethod")}
          </Button>
        </div>
      )}

      {generatedMethod && (
        <div className="space-y-4">
          {isEditing ? (
            <>
              <div>
                <label
                  className="text-sm font-medium text-foreground mb-2 block"
                  htmlFor={editMethodNameId}
                >
                  {t("features.methodGeneration.methodName")}
                </label>
                <TextField>
                  <TextField.Input
                    id={editMethodNameId}
                    value={manualMethodName}
                    onChange={(e) => setManualMethodName(e.target.value)}
                  />
                </TextField>
              </div>
              <div>
                <label
                  className="text-sm font-medium text-foreground mb-2 block"
                  htmlFor={editMethodDescriptionId}
                >
                  {t("features.methodGeneration.methodDescription")}
                </label>
                <TextArea>
                  <TextArea.Input
                    id={editMethodDescriptionId}
                    value={manualMethodDescription}
                    onChange={(e) => setManualMethodDescription(e.target.value)}
                    className="min-h-[300px] font-mono text-sm"
                  />
                </TextArea>
              </div>
              <div className="flex gap-2 justify-end">
                <Button
                  variant="neutral-secondary"
                  onClick={() => setIsEditing(false)}
                  className="bg-transparent"
                >
                  {t("common.cancel")}
                </Button>
                <Button
                  onClick={handleSaveEdit}
                  className="bg-blue-700 hover:bg-blue-800 text-white"
                >
                  <Save className="w-4 h-4 mr-2" />
                  {t("common.save")}
                </Button>
              </div>
            </>
          ) : (
            <>
              <div className="flex items-center justify-between">
                <p className="text-sm font-medium text-foreground">
                  {t("features.methodGeneration.methodName")}
                </p>
                <Button variant="neutral-tertiary" size="small" onClick={handleEdit}>
                  <Edit3 className="w-4 h-4 mr-1" />
                  {t("common.edit")}
                </Button>
              </div>
              <p className="text-lg font-semibold text-foreground">{generatedMethod.name}</p>
              <div>
                <p className="text-sm font-medium text-foreground mb-2 block">
                  {t("features.methodGeneration.methodDescription")}
                </p>
                <div className="p-4 bg-muted rounded-lg">
                  <p className="text-sm text-foreground whitespace-pre-wrap">
                    {generatedMethod.description}
                  </p>
                </div>
              </div>
            </>
          )}
        </div>
      )}
    </Card>
  );
}
