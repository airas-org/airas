import {
  FeatherArrowRight,
  FeatherBarChart3,
  FeatherFlaskConical,
  FeatherGitCompare,
  FeatherLayers,
  FeatherRefreshCw,
} from "@subframe/core";
import { useState } from "react";
import { IconButton } from "@/ui/components/IconButton";

interface ChatInputProps {
  onSubmit: (query: string) => void;
  disabled?: boolean;
  initialQuery?: string;
}

const quickTags = [
  {
    label: "仮説検証",
    icon: FeatherFlaskConical,
    colorClass: "text-brand-500",
    template: "以下の仮説を検証したい: ",
  },
  {
    label: "モデル比較",
    icon: FeatherGitCompare,
    colorClass: "text-success-500",
    template: "以下のモデルを比較検証したい: ",
  },
  {
    label: "アブレーション実験",
    icon: FeatherLayers,
    colorClass: "text-warning-500",
    template: "以下のアブレーション実験を行いたい: ",
  },
  {
    label: "再現実験",
    icon: FeatherRefreshCw,
    colorClass: "text-error-500",
    template: "以下の論文の再現実験を行いたい: ",
  },
  {
    label: "性能ベンチマーク",
    icon: FeatherBarChart3,
    colorClass: "text-neutral-500",
    template: "以下の性能ベンチマークを実施したい: ",
  },
];

export function ChatInput({ onSubmit, disabled = false, initialQuery = "" }: ChatInputProps) {
  const [query, setQuery] = useState(initialQuery);

  const handleSubmit = () => {
    if (query.trim()) {
      onSubmit(query.trim());
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  if (disabled) {
    return (
      <div className="w-full max-w-3xl mx-auto">
        <p className="text-body font-body text-subtext-color">{initialQuery}</p>
      </div>
    );
  }

  return (
    <div className="flex w-full max-w-[576px] mx-auto flex-col items-center gap-10">
      <div className="flex flex-col items-center gap-4">
        <img
          src="/airas_logo.png"
          alt="AIRAS"
          className="h-16 flex-none object-contain opacity-90"
        />
        <h1 className="text-heading-1 font-heading-1 text-default-font text-center">
          何を検証しますか？
        </h1>
        <p className="max-w-[448px] text-body font-body text-subtext-color text-center">
          検証したい仮説や研究テーマを入力してください。AIが検証方針の提案および実行を行います。
        </p>
      </div>
      <div className="flex w-full flex-col items-start gap-4">
        <div className="flex w-full items-start relative">
          <textarea
            placeholder="例: Sparse Attentionは推論速度を改善するか？精度への影響は？"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            rows={3}
            className="grow shrink-0 basis-0 resize-none rounded-xl border border-solid border-neutral-border bg-default-background pl-4 pr-14 py-3 text-body font-body text-default-font shadow-sm outline-none placeholder:text-neutral-400 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary"
          />
          <div className="flex items-start absolute right-3 bottom-3">
            <IconButton
              variant="brand-primary"
              icon={<FeatherArrowRight />}
              onClick={handleSubmit}
            />
          </div>
        </div>
        <div className="flex w-full flex-wrap items-center justify-center gap-3">
          {quickTags.map((tag) => (
            <button
              key={tag.label}
              type="button"
              onClick={() => setQuery(tag.template)}
              className="flex items-center gap-2 rounded-full border border-solid border-neutral-border bg-default-background px-4 py-2 shadow-sm hover:bg-neutral-50 transition-colors cursor-pointer"
            >
              <tag.icon className={`text-body font-body ${tag.colorClass}`} />
              <span className="text-caption font-caption text-subtext-color">{tag.label}</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
