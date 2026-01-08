import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import type { GoogleGenAIParams, NodeLLMConfig, OpenAIParams } from "@/lib/api";
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

  const handleModelChange = (llm_name: string) => {
    if (!llm_name || llm_name === "__default__") {
      onChange(null);
    } else {
      const provider = getProviderType(llm_name);
      let params: NodeLLMConfig["params"] = null;

      // Initialize appropriate params based on provider
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
      <Select value={currentModelName} onValueChange={handleModelChange}>
        <SelectTrigger className="w-full">
          <SelectValue placeholder={`デフォルト (${defaultModelName})`} />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="__default__" className="text-blue-600 font-medium">
            {defaultModelName}
          </SelectItem>
          <SelectSeparator />

          <SelectGroup>
            <SelectLabel>OpenAI</SelectLabel>
            {OPENAI_MODELS.map((model) => (
              <SelectItem key={model} value={model}>
                {model}
              </SelectItem>
            ))}
          </SelectGroup>
          <SelectSeparator />
          <SelectGroup>
            <SelectLabel>Google</SelectLabel>
            {GOOGLE_MODELS.map((model) => (
              <SelectItem key={model} value={model}>
                {model}
              </SelectItem>
            ))}
          </SelectGroup>
          <SelectSeparator />
          <SelectGroup>
            <SelectLabel>Anthropic</SelectLabel>
            {ANTHROPIC_MODELS.map((model) => (
              <SelectItem key={model} value={model}>
                {model}
              </SelectItem>
            ))}
          </SelectGroup>
        </SelectContent>
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
            >
              <SelectTrigger className="w-full mt-1">
                <SelectValue placeholder="None" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="none">None</SelectItem>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
              </SelectContent>
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
            <Input
              type="number"
              placeholder="None"
              value={(value?.params as GoogleGenAIParams)?.thinking_budget ?? ""}
              onChange={(e) => handleThinkingBudgetChange(e.target.value)}
              className="w-full mt-1"
            />
          </div>
        </div>
      )}
    </div>
  );
}
