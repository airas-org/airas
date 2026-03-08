import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { VerificationMethod } from "../types";

interface VerificationPlanViewProps {
  verificationMethod: VerificationMethod;
  onGenerateCode: (
    modificationNotes: string,
    repositoryName: string,
    updatedSettings: Record<string, Record<string, string>>,
  ) => void;
  showButton: boolean;
}

export function VerificationPlanView({
  verificationMethod,
  onGenerateCode,
  showButton,
}: VerificationPlanViewProps) {
  const { t } = useTranslation();
  const [editingSettings, setEditingSettings] = useState<Record<string, Record<string, string>>>(
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

  const handleSettingChange = (experimentKey: string, settingKey: string, value: string) => {
    setEditingSettings((prev) => ({
      ...prev,
      [experimentKey]: {
        ...prev[experimentKey],
        [settingKey]: value,
      },
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
          <p className="text-sm text-muted-foreground mt-1">{verificationMethod.whatToVerify}</p>
        </div>

        <div>
          <p className="text-sm font-medium text-foreground">
            {t("verification.detail.verificationPlan.steps")}
          </p>
          <ol className="mt-2 space-y-1.5 list-decimal list-inside">
            {verificationMethod.steps.map((step, index) => (
              // eslint-disable-next-line react/no-array-index-key
              <li
                key={`step-${index}-${step.slice(0, 20)}`}
                className="text-sm text-muted-foreground"
              >
                {step}
              </li>
            ))}
          </ol>
        </div>

        <div>
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm font-medium text-foreground">Experiment Settings</p>
            <button
              type="button"
              onClick={handleToggleEdit}
              className="rounded-md bg-neutral-200 px-2.5 py-1 text-xs font-medium text-neutral-700 hover:bg-neutral-300 hover:text-neutral-900 transition-colors cursor-pointer"
            >
              {isEditMode ? "Save" : "Edit"}
            </button>
          </div>
          <div className="space-y-3">
            {Object.entries(editingSettings).map(([experimentKey, settings]) => (
              <div
                key={experimentKey}
                className="rounded-md border border-neutral-200 overflow-hidden"
              >
                <div className="bg-neutral-50 px-3 py-2 border-b border-neutral-200">
                  <span className="text-xs font-semibold text-foreground">{experimentKey}</span>
                </div>
                <table className="w-full">
                  <tbody>
                    {Object.entries(settings).map(([key, value]) => (
                      <tr key={key} className="border-b border-neutral-100 last:border-0">
                        <td className="px-3 py-2 text-xs font-medium text-foreground w-1/3">
                          {key}
                        </td>
                        <td className="px-3 py-2 text-xs text-muted-foreground">
                          {isEditMode ? (
                            <input
                              type="text"
                              value={value}
                              onChange={(e) =>
                                handleSettingChange(experimentKey, key, e.target.value)
                              }
                              className="w-full rounded border border-neutral-300 px-2 py-1 text-xs text-foreground focus:outline-none focus:ring-1 focus:ring-brand-500"
                            />
                          ) : (
                            value
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ))}
          </div>
        </div>

        <div>
          <p className="text-sm font-medium text-foreground mb-1">Modification Notes</p>
          <textarea
            value={modificationNotes}
            onChange={(e) => setModificationNotes(e.target.value)}
            placeholder="Enter any modifications to the verification policy..."
            rows={3}
            className="w-full rounded-md border border-neutral-300 px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground focus:outline-none focus:ring-1 focus:ring-brand-500 resize-none"
          />
        </div>

        <div>
          <p className="text-sm font-medium text-foreground mb-1">Repository Name</p>
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
