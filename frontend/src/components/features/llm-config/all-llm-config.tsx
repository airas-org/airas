import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import type { NodeLLMConfig, TopicOpenEndedResearchSubgraphLLMMapping } from "@/lib/api";
import { SUBGRAPH_DISPLAY_CONFIG, SUBGRAPH_NODE_CONFIGS } from "./constants";
import { SubgraphLLMConfig } from "./subgraph-llm-config";

interface AllLLMConfigProps {
  llmMapping: TopicOpenEndedResearchSubgraphLLMMapping | null | undefined;
  onChange: (mapping: TopicOpenEndedResearchSubgraphLLMMapping | null) => void;
}

export function AllLLMConfig({ llmMapping, onChange }: AllLLMConfigProps) {
  const [showLLMConfig, setShowLLMConfig] = useState(false);

  const handleSubgraphChange = (
    subgraphKey: keyof TopicOpenEndedResearchSubgraphLLMMapping,
    config: Record<string, NodeLLMConfig | null> | null,
  ) => {
    if (!config) {
      if (!llmMapping) return;
      const { [subgraphKey]: _, ...rest } = llmMapping;
      onChange(Object.keys(rest).length === 0 ? null : rest);
    } else {
      onChange({
        ...llmMapping,
        [subgraphKey]: config,
      });
    }
  };

  return (
    <div className="rounded-md border border-border">
      <button
        type="button"
        className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-foreground"
        onClick={() => setShowLLMConfig((prev) => !prev)}
        aria-expanded={showLLMConfig}
      >
        <span>LLM設定</span>
        {showLLMConfig ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>
      {showLLMConfig && (
        <div className="p-4 space-y-4">
          <p className="text-xs text-muted-foreground">
            各サブグラフで使用するLLMモデルをカスタマイズできます。指定しない場合はデフォルト設定が適用されます。
          </p>
          <div className="space-y-3">
            {SUBGRAPH_DISPLAY_CONFIG.map(({ key, title }) => (
              <SubgraphLLMConfig
                key={key}
                title={title}
                nodes={SUBGRAPH_NODE_CONFIGS[key]}
                config={llmMapping?.[key]}
                onChange={(config) => handleSubgraphChange(key, config)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
