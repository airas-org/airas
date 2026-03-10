import { Cpu, Database, Edit3, Plus, Save, Settings2, Sliders, Trash2 } from "lucide-react";
import { useEffect, useId, useState } from "react";
import { useTranslation } from "react-i18next";
import { generateExperimentConfig } from "@/lib/api-mock";
import type { ExperimentConfig, Method } from "@/types/research";
import { Button, Card, TextArea, TextField } from "@/ui";

interface ExperimentConfigSectionProps {
  method: Method | null;
  configs: ExperimentConfig[];
  onConfigsGenerated: (configs: ExperimentConfig[]) => void;
  onStepExecuted?: (configs: ExperimentConfig[]) => void;
  onBranchCreated?: (configs: ExperimentConfig[]) => void;
  onSave?: () => void;
}

export function ExperimentConfigSection({
  method,
  configs,
  onConfigsGenerated,
  onStepExecuted,
  onBranchCreated,
  onSave,
}: ExperimentConfigSectionProps) {
  const { t } = useTranslation();
  const [isGenerating, setIsGenerating] = useState(false);
  const [isManualMode, setIsManualMode] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [editingConfigs, setEditingConfigs] = useState<ExperimentConfig[]>([]);
  const [manualMethodInput, setManualMethodInput] = useState("");
  const [hasExecuted, setHasExecuted] = useState(false);
  const [tempConfigs, setTempConfigs] = useState<ExperimentConfig[]>([]);
  const manualMethodDescriptionId = useId();

  useEffect(() => {
    if (configs.length === 0) {
      setHasExecuted(false);
      setIsManualMode(false);
      setIsEditing(false);
      setEditingConfigs([]);
      setTempConfigs([]);
    }
  }, [configs]);

  const handleGenerate = async () => {
    if (!method) return;
    setIsGenerating(true);
    try {
      const generatedConfigs = await generateExperimentConfig(method);
      setTempConfigs(generatedConfigs);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleConfirmGenerated = () => {
    if (tempConfigs.length === 0) return;
    onConfigsGenerated(tempConfigs);
    if (!hasExecuted && onStepExecuted) {
      onStepExecuted(tempConfigs);
      setHasExecuted(true);
    }
    if (onSave) {
      onSave();
    }
    setTempConfigs([]);
  };

  const createEmptyConfig = (): ExperimentConfig => ({
    id: `manual-config-${Date.now()}`,
    model: "",
    dataset: "",
    hyperparameters: {
      epochs: 100,
      learning_rate: 0.001,
      batch_size: 32,
      hidden_dim: 256,
    },
    description: "",
  });

  const handleStartManualInput = () => {
    setIsManualMode(true);
    if (configs.length === 0) {
      setEditingConfigs([createEmptyConfig()]);
    } else {
      setEditingConfigs([...configs]);
    }
    setIsEditing(true);
  };

  const handleAddConfig = () => {
    setEditingConfigs([...editingConfigs, createEmptyConfig()]);
  };

  const handleRemoveConfig = (index: number) => {
    setEditingConfigs(editingConfigs.filter((_, i) => i !== index));
  };

  const handleConfigChange = (index: number, field: string, value: string | number) => {
    const updated = [...editingConfigs];
    if (field.startsWith("hyperparameters.")) {
      const hyperKey = field.replace("hyperparameters.", "");
      updated[index] = {
        ...updated[index],
        hyperparameters: {
          ...updated[index].hyperparameters,
          [hyperKey]: value,
        },
      };
    } else {
      updated[index] = { ...updated[index], [field]: value };
    }
    setEditingConfigs(updated);
  };

  const handleSaveConfigs = () => {
    const validConfigs = editingConfigs.filter((c) => c.model.trim() && c.dataset.trim());
    if (validConfigs.length > 0) {
      onConfigsGenerated(validConfigs);
      setIsEditing(false);
      if (!hasExecuted && onStepExecuted) {
        onStepExecuted(validConfigs);
        setHasExecuted(true);
      } else if (hasExecuted && onBranchCreated) {
        onBranchCreated(validConfigs);
      }
      if (onSave) {
        onSave();
      }
    }
  };

  const handleEdit = () => {
    setEditingConfigs([...configs]);
    setIsEditing(true);
  };

  const renderTempConfigPreview = () => (
    <div className="space-y-4">
      <div className="p-4 bg-muted/50 border border-border rounded-lg">
        <p className="text-sm text-muted-foreground mb-4">
          {t("features.experimentConfig.generatedPreview")}
        </p>
        {tempConfigs.map((config) => (
          <div key={config.id} className="p-4 border border-border rounded-lg mb-4 last:mb-0">
            <div className="flex items-center gap-2 mb-3">
              <Cpu className="w-4 h-4 text-blue-700" />
              <h4 className="font-medium text-foreground">{config.model}</h4>
            </div>
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div className="flex items-center gap-2">
                <Database className="w-4 h-4 text-muted-foreground" />
                <span className="text-muted-foreground">Dataset:</span>
                <span className="text-foreground">{config.dataset}</span>
              </div>
              <div className="flex items-center gap-2">
                <Sliders className="w-4 h-4 text-muted-foreground" />
                <span className="text-muted-foreground">Epochs:</span>
                <span className="text-foreground">{config.hyperparameters.epochs}</span>
              </div>
            </div>
            <p className="mt-3 text-sm text-muted-foreground">{config.description}</p>
          </div>
        ))}
      </div>
      <Button
        onClick={handleConfirmGenerated}
        className="w-full bg-blue-700 hover:bg-blue-800 text-white"
      >
        <Save className="w-4 h-4 mr-2" />
        {t("features.experimentConfig.confirmConfig")}
      </Button>
    </div>
  );

  return (
    <Card className="p-6">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-10 h-10 rounded-lg bg-blue-700 flex items-center justify-center">
          <Settings2 className="w-5 h-5 text-white" />
        </div>
        <div>
          <h3 className="text-lg font-semibold text-foreground">
            {t("features.experimentConfig.title")}
          </h3>
          <p className="text-sm text-muted-foreground">{t("features.experimentConfig.subtitle")}</p>
        </div>
      </div>

      {configs.length === 0 && !isEditing && tempConfigs.length === 0 && (
        <div className="flex gap-2 mb-6">
          <Button
            variant={!isManualMode ? "brand-primary" : "neutral-secondary"}
            size="small"
            onClick={() => setIsManualMode(false)}
            className={
              !isManualMode ? "bg-blue-700 hover:bg-blue-800 text-white" : "bg-transparent"
            }
          >
            {t("features.experimentConfig.generateFromMethod")}
          </Button>
          <Button
            variant={isManualMode ? "brand-primary" : "neutral-secondary"}
            size="small"
            onClick={handleStartManualInput}
            className={isManualMode ? "bg-blue-700 hover:bg-blue-800 text-white" : "bg-transparent"}
          >
            {t("features.experimentConfig.manualInput")}
          </Button>
        </div>
      )}

      {isManualMode && !method && !isEditing && tempConfigs.length === 0 && (
        <div className="mb-6">
          <label
            className="text-sm font-medium text-foreground mb-2 block"
            htmlFor={manualMethodDescriptionId}
          >
            {t("features.experimentConfig.targetMethodDescription")}
          </label>
          <TextArea>
            <TextArea.Input
              id={manualMethodDescriptionId}
              value={manualMethodInput}
              onChange={(e) => setManualMethodInput(e.target.value)}
              placeholder={t("features.experimentConfig.targetMethodPlaceholder")}
              className="min-h-[100px] mb-4"
            />
          </TextArea>
          <Button
            onClick={handleStartManualInput}
            className="w-full bg-blue-700 hover:bg-blue-800 text-white"
          >
            {t("features.experimentConfig.inputExperimentConfig")}
          </Button>
        </div>
      )}

      {isEditing && (
        <div className="space-y-6">
          {editingConfigs.map((config, index) => {
            const modelId = `${config.id}-model`;
            const datasetId = `${config.id}-dataset`;
            const epochsId = `${config.id}-epochs`;
            const learningRateId = `${config.id}-learning-rate`;
            const batchSizeId = `${config.id}-batch-size`;
            const hiddenDimId = `${config.id}-hidden-dim`;
            const descriptionId = `${config.id}-description`;

            return (
              <div key={config.id} className="p-4 border border-border rounded-lg space-y-4">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium text-foreground">
                    {t("features.experimentConfig.configNumber", { number: index + 1 })}
                  </span>
                  {editingConfigs.length > 1 && (
                    <Button
                      variant="neutral-tertiary"
                      size="small"
                      onClick={() => handleRemoveConfig(index)}
                    >
                      <Trash2 className="w-4 h-4 text-destructive" />
                    </Button>
                  )}
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-xs text-muted-foreground mb-1 block" htmlFor={modelId}>
                      {t("features.experimentConfig.modelName")}
                    </label>
                    <TextField>
                      <TextField.Input
                        id={modelId}
                        value={config.model}
                        onChange={(e) => handleConfigChange(index, "model", e.target.value)}
                        placeholder="例: Transformer"
                      />
                    </TextField>
                  </div>
                  <div>
                    <label className="text-xs text-muted-foreground mb-1 block" htmlFor={datasetId}>
                      {t("features.experimentConfig.dataset")}
                    </label>
                    <TextField>
                      <TextField.Input
                        id={datasetId}
                        value={config.dataset}
                        onChange={(e) => handleConfigChange(index, "dataset", e.target.value)}
                        placeholder="例: CIFAR-10"
                      />
                    </TextField>
                  </div>
                </div>
                <div className="grid grid-cols-4 gap-3">
                  <div>
                    <label className="text-xs text-muted-foreground mb-1 block" htmlFor={epochsId}>
                      Epochs
                    </label>
                    <TextField>
                      <TextField.Input
                        id={epochsId}
                        type="number"
                        value={String(config.hyperparameters.epochs)}
                        onChange={(e) =>
                          handleConfigChange(
                            index,
                            "hyperparameters.epochs",
                            Number.parseInt(e.target.value, 10),
                          )
                        }
                      />
                    </TextField>
                  </div>
                  <div>
                    <label
                      className="text-xs text-muted-foreground mb-1 block"
                      htmlFor={learningRateId}
                    >
                      Learning Rate
                    </label>
                    <TextField>
                      <TextField.Input
                        id={learningRateId}
                        type="number"
                        step="0.0001"
                        value={String(config.hyperparameters.learning_rate)}
                        onChange={(e) =>
                          handleConfigChange(
                            index,
                            "hyperparameters.learning_rate",
                            Number.parseFloat(e.target.value),
                          )
                        }
                      />
                    </TextField>
                  </div>
                  <div>
                    <label
                      className="text-xs text-muted-foreground mb-1 block"
                      htmlFor={batchSizeId}
                    >
                      Batch Size
                    </label>
                    <TextField>
                      <TextField.Input
                        id={batchSizeId}
                        type="number"
                        value={String(config.hyperparameters.batch_size)}
                        onChange={(e) =>
                          handleConfigChange(
                            index,
                            "hyperparameters.batch_size",
                            Number.parseInt(e.target.value, 10),
                          )
                        }
                      />
                    </TextField>
                  </div>
                  <div>
                    <label
                      className="text-xs text-muted-foreground mb-1 block"
                      htmlFor={hiddenDimId}
                    >
                      Hidden Dim
                    </label>
                    <TextField>
                      <TextField.Input
                        id={hiddenDimId}
                        type="number"
                        value={String(config.hyperparameters.hidden_dim)}
                        onChange={(e) =>
                          handleConfigChange(
                            index,
                            "hyperparameters.hidden_dim",
                            Number.parseInt(e.target.value, 10),
                          )
                        }
                      />
                    </TextField>
                  </div>
                </div>
                <div>
                  <label
                    className="text-xs text-muted-foreground mb-1 block"
                    htmlFor={descriptionId}
                  >
                    {t("features.experimentConfig.description")}
                  </label>
                  <TextArea>
                    <TextArea.Input
                      id={descriptionId}
                      value={config.description}
                      onChange={(e) => handleConfigChange(index, "description", e.target.value)}
                      placeholder={t("features.experimentConfig.descriptionPlaceholder")}
                      className="min-h-[60px]"
                    />
                  </TextArea>
                </div>
              </div>
            );
          })}
          <Button
            variant="neutral-secondary"
            onClick={handleAddConfig}
            className="w-full bg-transparent"
          >
            <Plus className="w-4 h-4 mr-2" />
            {t("features.experimentConfig.addConfig")}
          </Button>
          <div className="flex gap-2 justify-end">
            <Button
              variant="neutral-secondary"
              onClick={() => setIsEditing(false)}
              className="bg-transparent"
            >
              {t("common.cancel")}
            </Button>
            <Button
              onClick={handleSaveConfigs}
              className="bg-blue-700 hover:bg-blue-800 text-white"
            >
              <Save className="w-4 h-4 mr-2" />
              {t("common.save")}
            </Button>
          </div>
        </div>
      )}

      {tempConfigs.length > 0 && renderTempConfigPreview()}

      {!isManualMode &&
        !isEditing &&
        configs.length === 0 &&
        tempConfigs.length === 0 &&
        (!method ? (
          <div className="text-center py-8 text-muted-foreground">
            <Settings2 className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>{t("features.experimentConfig.noMethodMessage")}</p>
          </div>
        ) : (
          <>
            <div className="mb-6 p-4 bg-muted rounded-lg">
              <p className="text-sm font-medium text-muted-foreground mb-1">
                {t("features.experimentConfig.targetMethod")}
              </p>
              <p className="text-foreground">{method.name}</p>
            </div>
            <Button
              onClick={handleGenerate}
              disabled={isGenerating}
              className="w-full bg-blue-700 hover:bg-blue-800 text-white"
            >
              {isGenerating
                ? t("features.experimentConfig.generating")
                : t("features.experimentConfig.generate")}
            </Button>
          </>
        ))}

      {configs.length > 0 && !isEditing && (
        <div className="space-y-4">
          <div className="flex items-center justify-between mb-4">
            <span className="text-sm font-medium text-foreground">
              {t("features.experimentConfig.configList")}
            </span>
            <Button variant="neutral-tertiary" size="small" onClick={handleEdit}>
              <Edit3 className="w-4 h-4 mr-1" />
              {t("common.edit")}
            </Button>
          </div>
          {configs.map((config) => (
            <div key={config.id} className="p-4 border border-border rounded-lg">
              <div className="flex items-center gap-2 mb-3">
                <Cpu className="w-4 h-4 text-blue-700" />
                <h4 className="font-medium text-foreground">{config.model}</h4>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center gap-2">
                  <Database className="w-4 h-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Dataset:</span>
                  <span className="text-foreground">{config.dataset}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Sliders className="w-4 h-4 text-muted-foreground" />
                  <span className="text-muted-foreground">Epochs:</span>
                  <span className="text-foreground">{config.hyperparameters.epochs}</span>
                </div>
              </div>
              <p className="mt-3 text-sm text-muted-foreground">{config.description}</p>
              <div className="mt-3 flex flex-wrap gap-2">
                {Object.entries(config.hyperparameters).map(([key, value]) => (
                  <span
                    key={key}
                    className="px-2 py-1 bg-muted rounded text-xs text-muted-foreground"
                  >
                    {key}: {value}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
