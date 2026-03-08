import {
  FeatherArrowRight,
  FeatherBarChart3,
  FeatherFlaskConical,
  FeatherGitCompare,
  FeatherLayers,
  FeatherRefreshCw,
} from "@subframe/core";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { IconButton } from "@/ui/components/IconButton";

interface ChatInputProps {
  onSubmit: (query: string) => void;
  disabled?: boolean;
  initialQuery?: string;
}

export function ChatInput({ onSubmit, disabled = false, initialQuery = "" }: ChatInputProps) {
  const { t } = useTranslation();
  const [query, setQuery] = useState(initialQuery);

  const quickTags = [
    {
      label: t("verification.detail.quickTags.hypothesisVerification"),
      icon: FeatherFlaskConical,
      colorClass: "text-brand-500",
      template: t("verification.detail.quickTagTemplates.hypothesisVerification"),
    },
    {
      label: t("verification.detail.quickTags.modelComparison"),
      icon: FeatherGitCompare,
      colorClass: "text-success-500",
      template: t("verification.detail.quickTagTemplates.modelComparison"),
    },
    {
      label: t("verification.detail.quickTags.ablationStudy"),
      icon: FeatherLayers,
      colorClass: "text-warning-500",
      template: t("verification.detail.quickTagTemplates.ablationStudy"),
    },
    {
      label: t("verification.detail.quickTags.reproductionExperiment"),
      icon: FeatherRefreshCw,
      colorClass: "text-error-500",
      template: t("verification.detail.quickTagTemplates.reproductionExperiment"),
    },
    {
      label: t("verification.detail.quickTags.performanceBenchmark"),
      icon: FeatherBarChart3,
      colorClass: "text-neutral-500",
      template: t("verification.detail.quickTagTemplates.performanceBenchmark"),
    },
  ];

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
          {t("verification.detail.chatInput.title")}
        </h1>
        <p className="max-w-[448px] text-body font-body text-subtext-color text-center">
          {t("verification.detail.chatInput.subtitle")}
        </p>
      </div>
      <div className="flex w-full flex-col items-start gap-4">
        <div className="flex w-full items-start relative">
          <textarea
            placeholder={t("verification.detail.chatInput.placeholder")}
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
