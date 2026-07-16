import { FeatherAlertTriangle, FeatherCheckCircle } from "@subframe/core";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import type { CredentialStatus } from "@/lib/api/models/CredentialStatus";
import { CredentialsService } from "@/lib/api/services/CredentialsService";
import { Alert } from "@/ui/components/Alert";
import { Button } from "@/ui/components/Button";
import { TextField } from "@/ui/components/TextField";

export function ApiKeysPage() {
  const { t } = useTranslation();
  const [credentials, setCredentials] = useState<CredentialStatus[] | null>(null);
  // Only fields the user touched are sent; "" requests removal.
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    CredentialsService.listCredentialsAirasV1CredentialsGet()
      .then((res) => setCredentials(res.credentials))
      .catch(() => setError(t("credentials.fetchError")))
      .finally(() => setLoading(false));
  }, [t]);

  const updateEdit = (name: string, value: string) => {
    // New edits invalidate the "saved" confirmation.
    setSaved(false);
    setEdits((prev) => ({ ...prev, [name]: value }));
  };

  const handleSave = async () => {
    setSaving(true);
    setSaved(false);
    setError(null);
    try {
      const res = await CredentialsService.updateCredentialsAirasV1CredentialsPut({
        updates: edits,
      });
      setCredentials(res.credentials);
      setEdits({});
      setSaved(true);
    } catch {
      setError(t("credentials.saveError"));
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-subtext-color" />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font">
          {t("credentials.pageTitle")}
        </h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          {t("credentials.pageSubtitle")}
        </p>

        {saved && (
          <div className="mt-4">
            <Alert
              variant="success"
              icon={<FeatherCheckCircle />}
              title={t("credentials.savedTitle")}
            />
          </div>
        )}

        {error && (
          <div className="mt-4">
            <Alert variant="error" icon={<FeatherAlertTriangle />} title={error} />
          </div>
        )}

        <div className="mt-6 rounded-lg border border-border bg-card p-6 flex flex-col gap-5">
          {(credentials ?? []).map((credential) => {
            const edited = credential.name in edits;
            const clearedForRemoval = edited && edits[credential.name] === "";
            const statusText = clearedForRemoval
              ? t("credentials.willBeRemoved")
              : credential.is_set
                ? `${t("credentials.configured")}${credential.preview ? ` (${credential.preview})` : ""}`
                : t("credentials.notConfigured");
            return (
              <TextField
                key={credential.name}
                label={credential.name}
                helpText={statusText}
                error={false}
              >
                <div className="flex items-center gap-2 w-full">
                  <TextField.Input
                    type={credential.is_secret ? "password" : "text"}
                    placeholder={
                      credential.is_set
                        ? t("credentials.replacePlaceholder")
                        : t("credentials.placeholder")
                    }
                    value={edits[credential.name] ?? ""}
                    onChange={(e) => updateEdit(credential.name, e.target.value)}
                  />
                  {credential.is_set && !clearedForRemoval && (
                    <Button
                      variant="neutral-tertiary"
                      size="small"
                      onClick={() => updateEdit(credential.name, "")}
                    >
                      {t("credentials.clear")}
                    </Button>
                  )}
                </div>
              </TextField>
            );
          })}

          <div className="flex items-center justify-between gap-4 pt-2">
            <p className="text-caption font-caption text-subtext-color">
              {t("credentials.storageNote")}
            </p>
            <Button onClick={handleSave} disabled={saving || Object.keys(edits).length === 0}>
              {saving ? t("credentials.saving") : t("credentials.save")}
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}
