import { FeatherArrowRight } from "@subframe/core";
import { useState } from "react";

interface ChatInputProps {
  onSubmit: (query: string) => void;
  disabled?: boolean;
  initialQuery?: string;
}

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
    <div className="w-full max-w-2xl mx-auto flex flex-col items-center gap-10">
      <div className="flex flex-col items-center gap-4">
        <img src="/airas_logo.png" alt="AIRAS" className="h-16 w-auto opacity-90" />
        <h1 className="text-heading-1 font-heading-1 text-default-font">
          What would you like to verify?
        </h1>
        <p className="text-body font-body text-subtext-color text-center max-w-md">
          Describe your research hypothesis or question, and AIRAS will design experiments to verify
          it.
        </p>
      </div>
      <div className="w-full relative">
        <textarea
          placeholder="e.g. Does sparse attention improve transformer inference speed without significant accuracy loss?"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={3}
          className="w-full resize-none rounded-xl border border-solid border-neutral-border bg-default-background px-4 py-3 pr-12 text-body font-body text-default-font outline-none placeholder:text-neutral-400 focus:border-brand-primary focus:ring-1 focus:ring-brand-primary shadow-sm"
        />
        <button
          type="button"
          onClick={handleSubmit}
          disabled={!query.trim()}
          className="absolute right-2.5 bottom-2.5 flex h-9 w-9 items-center justify-center rounded-lg bg-neutral-900 text-white shadow-sm transition-all hover:bg-neutral-800 hover:shadow-md active:scale-95 disabled:bg-neutral-200 disabled:text-neutral-400 disabled:shadow-none disabled:cursor-default cursor-pointer"
        >
          <FeatherArrowRight className="h-4 w-4" />
        </button>
      </div>
      <div className="flex items-center gap-6">
        {["Hypothesis Testing", "Model Comparison", "Ablation Study"].map((tag) => (
          <button
            key={tag}
            type="button"
            onClick={() => setQuery(`I want to conduct ${tag.toLowerCase()}: `)}
            className="rounded-full border border-solid border-neutral-border bg-default-background px-4 py-1.5 text-caption font-caption text-subtext-color hover:bg-neutral-50 hover:text-default-font transition-colors cursor-pointer"
          >
            {tag}
          </button>
        ))}
      </div>
    </div>
  );
}
