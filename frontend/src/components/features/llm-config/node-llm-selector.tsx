import type { GoogleGenAIParams, NodeLLMConfig, OpenAIParams } from "@/lib/api";
import { Label, Select, TextField } from "@/ui";
import {
  ANTHROPIC_MODELS,
  DEFAULT_NODE_LLM_CONFIG,
  GOOGLE_MODELS,
  OPENAI_MODELS,
} from "./constants";

interface NodeLLMSelectorProps {
  nodeKey: string;
  label: string;
  value: NodeLLMConfig | null | undefined;
  onChange: (config: NodeLLMConfig | null) => void;
}

// Determine provider type from model name
function getProviderType(modelName: string): "openai" | "google" | "anthropic" | null {
  if ((OPENAI_MODELS as readonly string[]).includes(modelName)) return "openai";
  if ((GOOGLE_MODELS as readonly string[]).includes(modelName)) return "google";
  if ((ANTHROPIC_MODELS as readonly string[]).includes(modelName)) return "anthropic";
  // Check for OpenRouter prefixed models
  if (modelName.startsWith("google/")) return "google";
  if (modelName.startsWith("anthropic/")) return "anthropic";
  return null;
}

export function NodeLLMSelector({ nodeKey, label, value, onChange }: NodeLLMSelectorProps) {
  const defaultModelName = DEFAULT_NODE_LLM_CONFIG[nodeKey as keyof typeof DEFAULT_NODE_LLM_CONFIG];
  const currentModelName = value?.llm_name ?? "__default__";
  // If default is selected, determine provider from the default model name
  const actualModelName = currentModelName === "__default__" ? defaultModelName : currentModelName;
  const providerType = getProviderType(actualModelName);
  if (providerType === null) {
    console.warn(`Unknown provider for model: ${actualModelName}`);
  }

  const handleModelChange = (llm_name: string) => {
    if (!llm_name || llm_name === "__default__") {
      onChange(null);
    } else {
      const provider = getProviderType(llm_name);
      if (provider === null) {
        console.warn(`Unknown provider for model: ${llm_name}`);
        return;
      }

      let params: NodeLLMConfig["params"] = null;
      if (provider === "openai") {
        params = { provider_type: "openai", reasoning_effort: null };
      } else if (provider === "google") {
        params = { provider_type: "google_genai", thinking_budget: null };
      } else if (provider === "anthropic") {
        params = { provider_type: "anthropic" };
      }

      onChange({ llm_name: llm_name as NodeLLMConfig["llm_name"], params });
    }
  };

  const handleReasoningEffortChange = (effort: string) => {
    if (!value) return;
    const newParams: OpenAIParams = {
      provider_type: "openai",
      reasoning_effort: effort === "none" ? null : (effort as OpenAIParams["reasoning_effort"]),
    };
    onChange({ ...value, params: newParams });
  };

  const handleThinkingBudgetChange = (budget: string) => {
    if (!value) return;
    const budgetNum = budget === "" ? null : parseInt(budget, 10);
    const newParams: GoogleGenAIParams = {
      provider_type: "google_genai",
      thinking_budget: budgetNum,
    };
    onChange({ ...value, params: newParams });
  };

  return (
    <div className="space-y-2">
      <Label className="text-xs font-semibold text-muted-foreground">{label}</Label>
      <Select
        value={currentModelName}
        onValueChange={handleModelChange}
        placeholder={defaultModelName}
      >
        <Select.Item value="__default__" className="text-blue-600 font-medium">
          {defaultModelName}
        </Select.Item>
        {OPENAI_MODELS.map((model) => (
          <Select.Item key={model} value={model}>
            {model}
          </Select.Item>
        ))}
        {GOOGLE_MODELS.map((model) => (
          <Select.Item key={model} value={model}>
            {model}
          </Select.Item>
        ))}
        {ANTHROPIC_MODELS.map((model) => (
          <Select.Item key={model} value={model}>
            {model}
          </Select.Item>
        ))}
      </Select>

      {/* TODO: We'll refactor when the number of parameters increases. */}

      {/* OpenAI params: reasoning_effort */}
      {providerType === "openai" && (
        <div className="mt-2 pt-2 border-t border-border/50 bg-muted/20 rounded-md p-2.5 space-y-2">
          <Label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">
            Parameters
          </Label>
          <div>
            <Label className="text-xs text-muted-foreground">Reasoning Effort</Label>
            <Select
              value={(value?.params as OpenAIParams)?.reasoning_effort ?? "none"}
              onValueChange={handleReasoningEffortChange}
              placeholder="None"
              className="mt-1"
            >
              <Select.Item value="none">None</Select.Item>
              <Select.Item value="low">Low</Select.Item>
              <Select.Item value="medium">Medium</Select.Item>
              <Select.Item value="high">High</Select.Item>
            </Select>
          </div>
        </div>
      )}

      {/* Google params: thinking_budget */}
      {providerType === "google" && (
        <div className="mt-2 pt-2 border-t border-border/50 bg-muted/20 rounded-md p-2.5 space-y-2">
          <Label className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wide">
            Parameters
          </Label>
          <div>
            <Label className="text-xs text-muted-foreground">Thinking Budget</Label>
            <p className="text-[10px] text-muted-foreground/70 mt-0.5">
              0=off, 1024-32768=fixed, -1=dynamic
            </p>
            <TextField className="mt-1">
              <TextField.Input
                type="number"
                placeholder="None"
                value={(value?.params as GoogleGenAIParams)?.thinking_budget ?? ""}
                onChange={(e) => handleThinkingBudgetChange(e.target.value)}
              />
            </TextField>
          </div>
        </div>
      )}
    </div>
  );
}
