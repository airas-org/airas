import { useTranslation } from "react-i18next";
import type { VerificationPlan } from "../types";

interface VerificationPlanViewProps {
  plan: VerificationPlan;
  onGenerateCode: () => void;
  showButton: boolean;
}

function splitToSteps(text: string): string[] {
  const sentences = text.split(/[。．]/).filter((s) => s.trim());
  return sentences.map((s) => s.trim());
}

export function VerificationPlanView({
  plan,
  onGenerateCode,
  showButton,
}: VerificationPlanViewProps) {
  const { t } = useTranslation();
  const steps = splitToSteps(plan.method);

  return (
    <div className="rounded-lg border border-border bg-card p-6">
      <h2 className="text-lg font-semibold text-foreground">
        {t("verification.detail.verificationPlan.title")}
      </h2>
      <div className="mt-4 space-y-4">
        <div>
          <p className="text-sm font-medium text-foreground">
            {t("verification.detail.verificationPlan.whatToVerify")}
          </p>
          <p className="text-sm text-muted-foreground mt-1">{plan.whatToVerify}</p>
        </div>
        <div>
          <p className="text-sm font-medium text-foreground">
            {t("verification.detail.verificationPlan.steps")}
          </p>
          <ul className="mt-2 space-y-1.5">
            {steps.map((step) => (
              <li key={step} className="flex gap-2 text-sm text-muted-foreground">
                <span className="text-brand-600 shrink-0">•</span>
                {step}
              </li>
            ))}
          </ul>
        </div>
      </div>
      {showButton && (
        <div className="mt-5 flex justify-end">
          <button
            type="button"
            onClick={onGenerateCode}
            className="rounded-md bg-neutral-200 px-3 py-1.5 text-xs font-medium text-neutral-700 hover:bg-neutral-300 hover:text-neutral-900 transition-colors cursor-pointer"
          >
            Generate experiment code
          </button>
        </div>
      )}
    </div>
  );
}
