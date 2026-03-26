import { FeatherChevronDown, FeatherChevronRight } from "@subframe/core";
import { useState } from "react";
import { useTranslation } from "react-i18next";
import { MathMarkdown } from "@/components/shared/math-markdown";
import { Badge } from "@/ui";
import type { ProposedMethod } from "../types";

interface MethodCardProps {
  method: ProposedMethod;
  isSelected: boolean;
  showSelectButton: boolean;
  onSelect: () => void;
}

function MethodCard({ method, isSelected, showSelectButton, onSelect }: MethodCardProps) {
  const { t } = useTranslation();
  return (
    <div
      className={`rounded-md border p-4 transition-colors ${
        isSelected ? "border-brand-600 bg-brand-50" : "border-border hover:border-brand-300"
      }`}
    >
      <div className="flex items-start justify-between gap-2">
        <h3 className="text-sm font-semibold text-foreground">{method.title}</h3>
        {isSelected && (
          <Badge variant="brand">{t("verification.detail.proposedMethods.selected")}</Badge>
        )}
      </div>
      <div className="mt-2">
        <p className="text-xs font-semibold text-foreground">
          {t("verification.detail.proposedMethods.whatToVerify")}
        </p>
        <MathMarkdown className="text-xs text-muted-foreground mt-0.5 [&>p]:m-0">
          {method.whatToVerify}
        </MathMarkdown>
      </div>
      <div className="mt-2">
        <p className="text-xs font-semibold text-foreground">
          {t("verification.detail.proposedMethods.method")}
        </p>
        <MathMarkdown className="text-xs text-muted-foreground mt-0.5 [&>p]:m-0">
          {method.method}
        </MathMarkdown>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs font-semibold text-success-800">Pros</p>
          <ul className="mt-1 space-y-0.5">
            {method.pros.map((pro) => (
              <li key={pro} className="text-xs text-muted-foreground flex gap-1">
                <span className="text-success-800 flex-shrink-0">+</span>
                <MathMarkdown className="inline [&>p]:inline [&>p]:m-0">{pro}</MathMarkdown>
              </li>
            ))}
          </ul>
        </div>
        <div>
          <p className="text-xs font-semibold text-error-700">Cons</p>
          <ul className="mt-1 space-y-0.5">
            {method.cons.map((con) => (
              <li key={con} className="text-xs text-muted-foreground flex gap-1">
                <span className="text-error-700 flex-shrink-0">-</span>
                <MathMarkdown className="inline [&>p]:inline [&>p]:m-0">{con}</MathMarkdown>
              </li>
            ))}
          </ul>
        </div>
      </div>
      {showSelectButton && (
        <div className="mt-3 flex justify-end">
          <button
            type="button"
            onClick={onSelect}
            className="rounded-md bg-neutral-200 px-3 py-1.5 text-xs font-medium text-neutral-700 hover:bg-neutral-300 hover:text-neutral-900 transition-colors cursor-pointer"
          >
            Select this method
          </button>
        </div>
      )}
    </div>
  );
}

interface ProposedMethodsListProps {
  methods: ProposedMethod[];
  selectedMethodId?: string;
  onSelectMethod: (methodId: string) => void;
  onCreateWithMethod?: (method: ProposedMethod) => void;
}

export function ProposedMethodsList({
  methods,
  selectedMethodId,
  onSelectMethod,
  onCreateWithMethod,
}: ProposedMethodsListProps) {
  const { t } = useTranslation();
  const [othersExpanded, setOthersExpanded] = useState(false);

  const selectedMethod = selectedMethodId ? methods.find((m) => m.id === selectedMethodId) : null;
  const otherMethods = selectedMethodId ? methods.filter((m) => m.id !== selectedMethodId) : [];

  // Before selection: show all methods with select buttons
  if (!selectedMethodId) {
    return (
      <div className="rounded-lg border border-border bg-card p-6">
        <h2 className="text-lg font-semibold text-foreground">
          {t("verification.detail.proposedMethods.title")}
        </h2>
        <p className="text-sm text-muted-foreground mt-1">
          {t("verification.detail.proposedMethods.subtitle", { count: methods.length })}
        </p>
        <div className="mt-4 space-y-4">
          {methods.map((method) => (
            <MethodCard
              key={method.id}
              method={method}
              isSelected={false}
              showSelectButton={true}
              onSelect={() => onSelectMethod(method.id)}
            />
          ))}
        </div>
      </div>
    );
  }

  // After selection: show selected + toggle for others
  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <h2 className="text-lg font-semibold text-foreground">
        {t("verification.detail.proposedMethods.title")}
      </h2>
      <div className="mt-4 space-y-4">
        {selectedMethod && (
          <MethodCard
            method={selectedMethod}
            isSelected={true}
            showSelectButton={false}
            onSelect={() => {}}
          />
        )}
        {otherMethods.length > 0 && (
          <div>
            <button
              type="button"
              onClick={() => setOthersExpanded((prev) => !prev)}
              className="flex items-center gap-1.5 text-xs font-medium text-subtext-color hover:text-default-font transition-colors cursor-pointer"
            >
              {othersExpanded ? (
                <FeatherChevronDown className="h-3.5 w-3.5" />
              ) : (
                <FeatherChevronRight className="h-3.5 w-3.5" />
              )}
              {t("verification.detail.proposedMethods.otherMethods", {
                count: otherMethods.length,
              })}
            </button>
            {othersExpanded && (
              <div className="mt-3 space-y-3">
                {otherMethods.map((method) => (
                  <MethodCard
                    key={method.id}
                    method={method}
                    isSelected={false}
                    showSelectButton={!!onCreateWithMethod}
                    onSelect={() => onCreateWithMethod?.(method)}
                  />
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
