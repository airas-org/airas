import { ChevronDown, ChevronUp } from "lucide-react";
import { useState } from "react";
import { NodeLLMSelector } from "./node-llm-selector";

interface NodeConfig {
  key: string;
  label: string;
}

interface SubgraphLLMConfigProps {
  title: string;
  nodes: readonly NodeConfig[];
  config: any | null | undefined;
  onChange: (config: any | null) => void;
}

export function SubgraphLLMConfig({ title, nodes, config, onChange }: SubgraphLLMConfigProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const handleNodeChange = (nodeKey: string, nodeConfig: any) => {
    onChange({
      ...config,
      [nodeKey]: nodeConfig,
    });
  };

  return (
    <div className="rounded-md border border-border">
      <button
        type="button"
        className="w-full flex items-center justify-between px-3 py-2 text-sm font-medium text-foreground hover:bg-muted/50"
        onClick={() => setIsExpanded((prev) => !prev)}
      >
        <span>{title}</span>
        {isExpanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
      </button>

      {isExpanded && (
        <div className="border-t border-border p-3 space-y-3 bg-card/60">
          {nodes.map((node) => (
            <NodeLLMSelector
              key={node.key}
              nodeKey={node.key}
              label={node.label}
              value={config?.[node.key]}
              onChange={(val) => handleNodeChange(node.key, val)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
