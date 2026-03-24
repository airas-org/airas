import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { MathMarkdown } from "@/components/shared/math-markdown";
import type { VerificationMethod } from "../types";

interface VerificationPlanViewProps {
  verificationMethod: VerificationMethod;
  onGenerateCode: (
    modificationNotes: string,
    repositoryName: string,
    updatedSettings: Record<string, string>,
  ) => void;
  showButton: boolean;
}

export function VerificationPlanView({
  verificationMethod,
  onGenerateCode,
  showButton,
}: VerificationPlanViewProps) {
  const { t } = useTranslation();
  const [editingSettings, setEditingSettings] = useState<Record<string, string>>(
    verificationMethod.experimentSettings,
  );
  const [isEditMode, setIsEditMode] = useState(false);
  const [modificationNotes, setModificationNotes] = useState("");
  const [repositoryName, setRepositoryName] = useState("");

  useEffect(() => {
    setEditingSettings(verificationMethod.experimentSettings);
  }, [verificationMethod.experimentSettings]);

  const handleToggleEdit = () => {
    setIsEditMode((prev) => !prev);
  };

  const handleSettingChange = (experimentKey: string, value: string) => {
    setEditingSettings((prev) => ({
      ...prev,
      [experimentKey]: value,
    }));
  };

  const handleGenerateCode = () => {
    onGenerateCode(modificationNotes, repositoryName, editingSettings);
  };

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
          <MathMarkdown className="text-sm text-muted-foreground mt-1 [&>p]:m-0">
            {verificationMethod.whatToVerify}
          </MathMarkdown>
        </div>

        <div>
          <p className="text-sm font-medium text-foreground">
            {t("verification.detail.verificationPlan.steps")}
          </p>
          <ol className="mt-2 space-y-1.5 list-decimal list-inside">
            {verificationMethod.steps.map((step) => (
              <li key={step} className="text-sm text-muted-foreground">
                <MathMarkdown className="inline [&>p]:inline [&>p]:m-0">{step}</MathMarkdown>
              </li>
            ))}
          </ol>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-foreground">
              {t("verification.detail.verificationPlan.experimentSettings")}
            </p>
            <button
              type="button"
              onClick={handleToggleEdit}
              className="rounded-md bg-neutral-200 px-2.5 py-1 text-xs font-medium text-neutral-700 hover:bg-neutral-300 hover:text-neutral-900 transition-colors cursor-pointer"
            >
              {isEditMode ? "Save" : "Edit"}
            </button>
          </div>
          <div className="rounded-md border border-neutral-200 overflow-hidden">
            <table className="w-full">
              <tbody>
                {Object.entries(editingSettings).map(([experimentKey, description]) => (
                  <tr key={experimentKey} className="border-b border-neutral-100 last:border-0">
                    <td className="px-3 py-2 text-xs font-medium text-foreground whitespace-nowrap">
                      {t("verification.detail.verificationPlan.experimentLabel", {
                        number: experimentKey,
                      })}
                    </td>
                    <td className="px-3 py-2 text-xs text-muted-foreground">
                      {isEditMode ? (
                        <input
                          type="text"
                          value={description}
                          onChange={(e) => handleSettingChange(experimentKey, e.target.value)}
                          className="w-full rounded border border-neutral-300 px-2 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-brand-500"
                        />
                      ) : (
                        <MathMarkdown className="[&>p]:m-0">{description}</MathMarkdown>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-foreground mb-1">
            {t("verification.detail.verificationPlan.modificationNotes")}
          </p>
          <textarea
            value={modificationNotes}
            onChange={(e) => setModificationNotes(e.target.value)}
            placeholder="Enter any modifications to the verification policy..."
            rows={3}
            className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-brand-500 resize-none"
          />
        </div>

        <div>
          <p className="text-sm font-medium text-foreground mb-1">
            {t("verification.detail.verificationPlan.repositoryName")}
          </p>
          <input
            type="text"
            value={repositoryName}
            onChange={(e) => setRepositoryName(e.target.value)}
            placeholder="e.g. my-experiment-repo"
            className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-brand-500"
          />
        </div>
      </div>

      {showButton && (
        <div className="mt-5 flex justify-end">
          <button
            type="button"
            onClick={handleGenerateCode}
            className="rounded-md bg-neutral-200 px-3 py-1.5 text-xs font-medium text-neutral-700 hover:bg-neutral-300 hover:text-neutral-900 transition-colors cursor-pointer"
          >
            Generate experiment code
          </button>
        </div>
      )}
    </div>
  );
}
