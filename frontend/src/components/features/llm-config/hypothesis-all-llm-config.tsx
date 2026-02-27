import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import type { HypothesisDrivenResearchLLMMapping, NodeLLMConfig } from "@/lib/api";
import { HYPOTHESIS_SUBGRAPH_DISPLAY_CONFIG, HYPOTHESIS_SUBGRAPH_NODE_CONFIGS } from "./constants";
import { SubgraphLLMConfig } from "./subgraph-llm-config";

type HypothesisSubgraphKey = keyof typeof HYPOTHESIS_SUBGRAPH_NODE_CONFIGS;
type SubgraphNodeMapping = Record<string, NodeLLMConfig | null>;

interface HypothesisAllLLMConfigProps {
  llmMapping: HypothesisDrivenResearchLLMMapping | null | undefined;
  onChange: (mapping: HypothesisDrivenResearchLLMMapping | null) => void;
}

export function HypothesisAllLLMConfig({ llmMapping, onChange }: HypothesisAllLLMConfigProps) {
  const [showLLMConfig, setShowLLMConfig] = useState(false);

  const handleSubgraphChange = (
    subgraphKey: HypothesisSubgraphKey,
    config: SubgraphNodeMapping | null,
  ) => {
    if (!config) {
      if (!llmMapping) return;
      const { [subgraphKey]: _, ...rest } = llmMapping;
      onChange(
        Object.keys(rest).length === 0 ? null : (rest as HypothesisDrivenResearchLLMMapping),
      );
    } else {
      onChange({
        ...llmMapping,
        [subgraphKey]: config as never,
      });
    }
  };

  return (
    <div className="rounded-md bg-muted/40">
      <button
        type="button"
        className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-foreground cursor-pointer"
        onClick={() => setShowLLMConfig((prev) => !prev)}
        aria-expanded={showLLMConfig}
      >
        <span>LLM設定</span>
        {showLLMConfig ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>
      {showLLMConfig && (
        <div className="p-6 space-y-4">
          <p className="text-xs text-muted-foreground">
            各サブグラフで使用するLLMモデルをカスタマイズできます。指定しない場合はデフォルト設定が適用されます。
          </p>
          <div className="divide-y divide-border">
            {HYPOTHESIS_SUBGRAPH_DISPLAY_CONFIG.map(({ key, title }) => (
              <SubgraphLLMConfig
                key={key}
                title={title}
                nodes={HYPOTHESIS_SUBGRAPH_NODE_CONFIGS[key]}
                config={llmMapping?.[key] as SubgraphNodeMapping | null | undefined}
                onChange={(config) => handleSubgraphChange(key, config)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
