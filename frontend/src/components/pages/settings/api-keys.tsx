import { FeatherAlertTriangle, FeatherCheckCircle } from "@subframe/core";
import type { TFunction } from "i18next";
import { Loader2 } from "lucide-react";
import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "@/lib/api/core/ApiError";
import type { CredentialStatus } from "@/lib/api/models/CredentialStatus";
import { CredentialsService } from "@/lib/api/services/CredentialsService";
import { GithubActionsService } from "@/lib/api/services/GithubActionsService";
import { Alert } from "@/ui/components/Alert";
import { Button } from "@/ui/components/Button";
import { TextField } from "@/ui/components/TextField";

// Turn a caught request failure into a short " (reason)" suffix so the user
// sees why a save failed instead of a generic message.
function describeApiError(error: unknown, t: TFunction): string {
  if (error instanceof ApiError) {
    const detail = (error.body as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === "string" && detail) return `: ${detail}`;
    if (error.status) return `: ${error.status} ${error.statusText}`.trimEnd();
    return "";
  }
  // No HTTP response at all — the dashboard API is unreachable.
  return `: ${t("credentials.networkError")}`;
}

const CATEGORIES: { key: string; names: string[] }[] = [
  { key: "github", names: ["GH_PERSONAL_ACCESS_TOKEN", "GITHUB_OWNER"] },
  {
    key: "llm",
    names: [
      "OPENAI_API_KEY",
      "ANTHROPIC_API_KEY",
      "GEMINI_API_KEY",
      "OPENROUTER_API_KEY",
      "AWS_BEARER_TOKEN_BEDROCK",
    ],
  },
  {
    key: "papers",
    names: ["SEMANTIC_SCHOLAR_API_KEY", "OPENALEX_API_KEY"],
  },
  {
    key: "compute",
    names: ["AIXS_API_KEY", "AIXS_BASE_URL"],
  },
  {
    key: "integrations",
    names: ["WANDB_API_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_PUBLIC_KEY", "LANGFUSE_BASE_URL"],
  },
];

export function ApiKeysPage() {
  const { t } = useTranslation();
  const [credentials, setCredentials] = useState<CredentialStatus[] | null>(null);
  // Only fields the user touched are sent; "" requests removal.
  const [edits, setEdits] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncRepo, setSyncRepo] = useState("");
  const [syncingName, setSyncingName] = useState<string | null>(null);
  const [syncResults, setSyncResults] = useState<Record<string, "success" | "error">>({});

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
    } catch (e) {
      setError(`${t("credentials.saveError")}${describeApiError(e, t)}`);
    } finally {
      setSaving(false);
    }
  };

  const renderCredential = (credential: CredentialStatus) => {
    const edited = credential.name in edits;
    const clearedForRemoval = edited && edits[credential.name] === "";
    // Single-line rows: the configured/not-configured state lives in the
    // input placeholder instead of a separate help-text line.
    const placeholder = clearedForRemoval
      ? t("credentials.willBeRemoved")
      : credential.is_set
        ? `${t("credentials.configured")}${credential.preview ? ` (${credential.preview})` : ""} — ${t("credentials.replacePlaceholder")}`
        : `${t("credentials.notConfigured")} — ${t("credentials.placeholder")}`;
    // GH_PERSONAL_ACCESS_TOKEN is the gate for syncing, not a syncable
    // secret itself (the experiment workflows use the runner's own token).
    const syncable = credential.is_secret && credential.name !== "GH_PERSONAL_ACCESS_TOKEN";
    const syncDisabledReason = !githubTokenSet
      ? t("credentials.sync.requiresToken")
      : parsedSync.repo === "" || parsedSync.owner === ""
        ? t("credentials.sync.requiresRepo")
        : !credential.is_set
          ? t("credentials.sync.requiresValue")
          : undefined;
    const syncResult = syncResults[credential.name];
    return (
      <div key={credential.name} className="flex items-center gap-3">
        <span className="w-72 shrink-0 text-caption-bold font-caption-bold text-default-font break-all">
          {credential.name}
        </span>
        <TextField className="flex-1" error={false}>
          <TextField.Input
            type={credential.is_secret ? "password" : "text"}
            placeholder={placeholder}
            value={edits[credential.name] ?? ""}
            onChange={(e) => updateEdit(credential.name, e.target.value)}
          />
        </TextField>
        <div className="w-16 shrink-0">
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
        {syncable && (
          <div className="w-40 shrink-0 flex items-center gap-2" title={syncDisabledReason}>
            <Button
              variant="neutral-secondary"
              size="small"
              disabled={syncDisabledReason !== undefined || syncingName !== null}
              onClick={() => handleSyncSecret(credential.name)}
            >
              {syncingName === credential.name
                ? t("credentials.sync.syncing")
                : t("credentials.sync.rowButton")}
            </Button>
            {syncResult === "success" && (
              <FeatherCheckCircle
                className="text-success-600"
                aria-label={t("credentials.sync.rowSynced")}
              />
            )}
            {syncResult === "error" && (
              <FeatherAlertTriangle
                className="text-error-600"
                aria-label={t("credentials.sync.rowError")}
              />
            )}
          </div>
        )}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center py-16">
        <Loader2 className="h-6 w-6 animate-spin text-subtext-color" />
      </div>
    );
  }

  const all = credentials ?? [];
  const isSet = (name: string) => all.some((c) => c.name === name && c.is_set);
  const githubTokenSet = isSet("GH_PERSONAL_ACCESS_TOKEN");
  const githubOwner = all.find((c) => c.name === "GITHUB_OWNER");
  // "owner/repo" also works; a bare name falls back to the GITHUB_OWNER credential.
  const parsedSync = syncRepo.includes("/")
    ? { owner: syncRepo.split("/")[0].trim(), repo: syncRepo.split("/")[1].trim() }
    : { owner: githubOwner?.preview ?? "", repo: syncRepo.trim() };

  const handleSyncSecret = async (name: string) => {
    setSyncingName(name);
    setSyncResults((prev) => {
      const next = { ...prev };
      delete next[name];
      return next;
    });
    try {
      const res = await GithubActionsService.setGithubActionsSecretsAirasV1GithubActionsSecretsPost(
        {
          github_config: {
            github_owner: parsedSync.owner,
            repository_name: parsedSync.repo,
            branch_name: "main",
          },
          secret_names: [name],
        },
      );
      setSyncResults((prev) => ({ ...prev, [name]: res.secrets_set ? "success" : "error" }));
    } catch {
      setSyncResults((prev) => ({ ...prev, [name]: "error" }));
    } finally {
      setSyncingName(null);
    }
  };

  const categorizedNames = new Set(CATEGORIES.flatMap((c) => c.names));
  const sections = [
    ...CATEGORIES.map((category) => ({
      key: category.key,
      items: all.filter((c) => category.names.includes(c.name)),
    })),
    // Credentials the backend knows but this page has not categorized yet.
    { key: "other", items: all.filter((c) => !categorizedNames.has(c.name)) },
  ].filter((section) => section.items.length > 0);

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

        {sections.map((section) => (
          <div key={section.key} className="mt-6">
            <h2 className="text-heading-3 font-heading-3 text-default-font">
              {t(`credentials.categories.${section.key}`)}
            </h2>
            <div className="mt-2 rounded-lg border border-border bg-card p-6 flex flex-col gap-5">
              {section.items.map(renderCredential)}
              {section.key === "github" && (
                <div className="flex items-center gap-3 border-t border-border pt-4">
                  <span className="w-72 shrink-0 text-caption-bold font-caption-bold text-default-font">
                    {t("credentials.sync.targetLabel")}
                  </span>
                  <TextField className="flex-1" error={false}>
                    <TextField.Input
                      type="text"
                      placeholder={
                        githubOwner?.preview
                          ? t("credentials.sync.repoPlaceholderWithOwner", {
                              owner: githubOwner.preview,
                            })
                          : t("credentials.sync.repoPlaceholder")
                      }
                      value={syncRepo}
                      onChange={(e) => setSyncRepo(e.target.value)}
                      disabled={!githubTokenSet}
                    />
                  </TextField>
                  <div className="w-16 shrink-0" />
                </div>
              )}
            </div>
            {section.key === "github" && (
              <p className="text-caption font-caption text-subtext-color mt-2">
                {githubTokenSet ? t("credentials.sync.hint") : t("credentials.sync.requiresToken")}
              </p>
            )}
          </div>
        ))}

        <div className="mt-6 flex items-center justify-between gap-4">
          <p className="text-caption font-caption text-subtext-color">
            {t("credentials.storageNote")}
          </p>
          <Button onClick={handleSave} disabled={saving || Object.keys(edits).length === 0}>
            {saving ? t("credentials.saving") : t("credentials.save")}
          </Button>
        </div>
      </div>
    </div>
  );
}
