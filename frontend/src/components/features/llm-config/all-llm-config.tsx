import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import type { NodeLLMConfig, TopicOpenEndedResearchLLMMapping } from "@/lib/api";
import { NESTED_SUBGRAPH_PATHS, SUBGRAPH_DISPLAY_CONFIG, SUBGRAPH_NODE_CONFIGS } from "./constants";
import { SubgraphLLMConfig } from "./subgraph-llm-config";

interface AllLLMConfigProps {
  llmMapping: TopicOpenEndedResearchLLMMapping | null | undefined;
  onChange: (mapping: TopicOpenEndedResearchLLMMapping | null) => void;
}

type AnyMapping = Record<string, unknown>;

function getSubgraphConfig(
  llmMapping: TopicOpenEndedResearchLLMMapping | null | undefined,
  key: string,
): Record<string, NodeLLMConfig | null> | undefined {
  if (!llmMapping) return undefined;
  const nested = NESTED_SUBGRAPH_PATHS[key];
  if (nested) {
    const parent = (llmMapping as AnyMapping)?.[nested.topKey] as AnyMapping | undefined;
    return parent?.[nested.nestedKey] as Record<string, NodeLLMConfig | null> | undefined;
  }
  return (llmMapping as AnyMapping)?.[key] as Record<string, NodeLLMConfig | null> | undefined;
}

export function AllLLMConfig({ llmMapping, onChange }: AllLLMConfigProps) {
  const [showLLMConfig, setShowLLMConfig] = useState(false);

  const handleSubgraphChange = (
    subgraphKey: string,
    config: Record<string, NodeLLMConfig | null> | null,
  ) => {
    const nested = NESTED_SUBGRAPH_PATHS[subgraphKey];
    if (nested) {
      const currentParent = ((llmMapping as AnyMapping)?.[nested.topKey] ?? {}) as AnyMapping;
      if (!config) {
        const { [nested.nestedKey]: _, ...restParent } = currentParent;
        const newParent = Object.keys(restParent).length === 0 ? undefined : restParent;
        if (!newParent) {
          if (!llmMapping) return;
          const { [nested.topKey]: __, ...restMapping } = llmMapping as AnyMapping;
          onChange(
            Object.keys(restMapping).length === 0
              ? null
              : (restMapping as TopicOpenEndedResearchLLMMapping),
          );
        } else {
          onChange({
            ...llmMapping,
            [nested.topKey]: newParent,
          } as TopicOpenEndedResearchLLMMapping);
        }
      } else {
        onChange({
          ...llmMapping,
          [nested.topKey]: { ...currentParent, [nested.nestedKey]: config },
        } as TopicOpenEndedResearchLLMMapping);
      }
    } else {
      if (!config) {
        if (!llmMapping) return;
        const { [subgraphKey]: _, ...rest } = llmMapping as AnyMapping;
        onChange(
          Object.keys(rest).length === 0 ? null : (rest as TopicOpenEndedResearchLLMMapping),
        );
      } else {
        onChange({
          ...llmMapping,
          [subgraphKey]: config,
        } as TopicOpenEndedResearchLLMMapping);
      }
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
            {SUBGRAPH_DISPLAY_CONFIG.map(({ key, title }) => (
              <SubgraphLLMConfig
                key={key}
                title={title}
                nodes={SUBGRAPH_NODE_CONFIGS[key]}
                config={getSubgraphConfig(llmMapping, key)}
                onChange={(config) => handleSubgraphChange(key, config)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
