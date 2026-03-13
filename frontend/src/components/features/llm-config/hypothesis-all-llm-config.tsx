import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import type { HypothesisDrivenResearchLLMMapping, NodeLLMConfig } from "@/lib/api";
import {
  HYPOTHESIS_NESTED_SUBGRAPH_PATHS,
  HYPOTHESIS_SUBGRAPH_DISPLAY_CONFIG,
  HYPOTHESIS_SUBGRAPH_NODE_CONFIGS,
} from "./constants";
import { SubgraphLLMConfig } from "./subgraph-llm-config";

type HypothesisSubgraphKey = keyof typeof HYPOTHESIS_SUBGRAPH_NODE_CONFIGS;
type SubgraphNodeMapping = Record<string, NodeLLMConfig | null>;
type AnyMapping = Record<string, unknown>;

function getSubgraphConfig(
  llmMapping: HypothesisDrivenResearchLLMMapping | null | undefined,
  key: string,
): SubgraphNodeMapping | undefined {
  if (!llmMapping) return undefined;
  const path = HYPOTHESIS_NESTED_SUBGRAPH_PATHS[key];
  if (path) {
    let current: unknown = llmMapping;
    for (const pathKey of path) {
      if (!current || typeof current !== "object") return undefined;
      current = (current as AnyMapping)[pathKey];
    }
    return current as SubgraphNodeMapping | undefined;
  }
  return (llmMapping as AnyMapping)[key] as SubgraphNodeMapping | undefined;
}

interface HypothesisAllLLMConfigProps {
  llmMapping: HypothesisDrivenResearchLLMMapping | null | undefined;
  onChange: (mapping: HypothesisDrivenResearchLLMMapping | null) => void;
  hideToggle?: boolean;
}

export function HypothesisAllLLMConfig({
  llmMapping,
  onChange,
  hideToggle,
}: HypothesisAllLLMConfigProps) {
  const { t } = useTranslation();
  const [showLLMConfig, setShowLLMConfig] = useState(false);

  const isOpen = hideToggle || showLLMConfig;

  const handleSubgraphChange = (
    subgraphKey: HypothesisSubgraphKey,
    config: SubgraphNodeMapping | null,
  ) => {
    const path = HYPOTHESIS_NESTED_SUBGRAPH_PATHS[subgraphKey as string];
    if (path) {
      const topKey = path[0] as keyof HypothesisDrivenResearchLLMMapping;
      const currentTop = ((llmMapping as AnyMapping)?.[topKey] ?? {}) as AnyMapping;
      let updatedTop: AnyMapping;
      if (path.length === 2) {
        if (!config) {
          const { [path[1]]: _, ...rest } = currentTop;
          updatedTop = rest;
        } else {
          updatedTop = { ...currentTop, [path[1]]: config };
        }
      } else {
        // path.length === 3
        const currentLevel1 = (currentTop[path[1]] ?? {}) as AnyMapping;
        if (!config) {
          const { [path[2]]: _, ...rest } = currentLevel1;
          const newLevel1 = Object.keys(rest).length === 0 ? undefined : rest;
          if (!newLevel1) {
            const { [path[1]]: _, ...rest2 } = currentTop;
            updatedTop = rest2;
          } else {
            updatedTop = { ...currentTop, [path[1]]: newLevel1 };
          }
        } else {
          updatedTop = { ...currentTop, [path[1]]: { ...currentLevel1, [path[2]]: config } };
        }
      }
      if (Object.keys(updatedTop).length === 0) {
        if (!llmMapping) return;
        const { [topKey]: _, ...rest } = llmMapping;
        onChange(
          Object.keys(rest).length === 0 ? null : (rest as HypothesisDrivenResearchLLMMapping),
        );
      } else {
        onChange({ ...llmMapping, [topKey]: updatedTop } as HypothesisDrivenResearchLLMMapping);
      }
    } else {
      if (!config) {
        if (!llmMapping) return;
        const { [subgraphKey]: _, ...rest } = llmMapping as AnyMapping;
        onChange(
          Object.keys(rest).length === 0 ? null : (rest as HypothesisDrivenResearchLLMMapping),
        );
      } else {
        onChange({ ...llmMapping, [subgraphKey]: config as never });
      }
    }
  };

  return (
    <div className={hideToggle ? "" : "rounded-md bg-muted/40"}>
      {!hideToggle && (
        <button
          type="button"
          className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-foreground cursor-pointer"
          onClick={() => setShowLLMConfig((prev) => !prev)}
          aria-expanded={showLLMConfig}
        >
          <span>{t("features.llmConfig.title")}</span>
          {showLLMConfig ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
        </button>
      )}
      {isOpen && (
        <div className="p-6 space-y-4">
          <p className="text-xs text-muted-foreground">{t("features.llmConfig.description")}</p>
          <div className="divide-y divide-border">
            {HYPOTHESIS_SUBGRAPH_DISPLAY_CONFIG.map(({ key, title }) => (
              <SubgraphLLMConfig
                key={key}
                title={title}
                nodes={HYPOTHESIS_SUBGRAPH_NODE_CONFIGS[key as HypothesisSubgraphKey]}
                config={getSubgraphConfig(llmMapping, key)}
                onChange={(config) => handleSubgraphChange(key as HypothesisSubgraphKey, config)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
