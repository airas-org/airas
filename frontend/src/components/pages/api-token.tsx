import { Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { useEE } from "@/hooks/use-ee-components";
import type { ApiKeyResponse } from "@/lib/api/models/ApiKeyResponse";
import { ApiProvider } from "@/lib/api/models/ApiProvider";
import { EeApiKeysService } from "@/lib/api/services/EeApiKeysService";
import { Badge, Button, TextField } from "@/ui";

const PROVIDERS: { id: ApiProvider; label: string }[] = [
  { id: ApiProvider.OPENAI, label: "OpenAI" },
  { id: ApiProvider.ANTHROPIC, label: "Anthropic" },
  { id: ApiProvider.GEMINI, label: "Google Gemini" },
];

type KeysRecord = Partial<Record<ApiProvider, ApiKeyResponse>>;

interface ApiProviderCardProps {
  id: ApiProvider;
  label: string;
  entry: ApiKeyResponse | undefined;
  inputValue: string;
  isSaving: boolean;
  isDeleting: boolean;
  onInputChange: (value: string) => void;
  onSave: () => void;
  onDelete: () => void;
}

function ApiProviderCard({
  id,
  label,
  entry,
  inputValue,
  isSaving,
  isDeleting,
  onInputChange,
  onSave,
  onDelete,
}: ApiProviderCardProps) {
  const { t, i18n } = useTranslation();

  return (
    <div
      key={id}
      className="flex w-full flex-col items-start overflow-hidden rounded-xl border border-solid border-neutral-800 bg-neutral-900 shadow-sm"
    >
      <div className="flex w-full flex-col items-start gap-5 px-6 py-6">
        <div className="flex w-full items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 flex-none items-center justify-center rounded-lg bg-neutral-800">
              <span className="text-sm font-bold text-neutral-300">{label.charAt(0)}</span>
            </div>
            <span className="text-heading-2 font-heading-2 text-white">{label}</span>
          </div>
          {!entry && <Badge variant="neutral">{t("apiToken.notConfigured")}</Badge>}
        </div>

        {entry ? (
          <div className="flex w-full items-center justify-between rounded-lg px-5 py-4 border border-solid border-neutral-800/60 bg-neutral-950/50">
            <div className="flex flex-col items-start gap-1">
              <code className="text-sm font-mono text-neutral-300">{entry.masked_key}</code>
              <span className="text-caption font-caption text-neutral-500">
                {t("apiToken.updatedAt")}:{" "}
                {new Date(entry.updated_at).toLocaleDateString(i18n.language)}
              </span>
            </div>
            <Button
              variant="destructive-secondary"
              size="small"
              onClick={onDelete}
              disabled={isDeleting}
            >
              {isDeleting && <Loader2 className="h-3 w-3 animate-spin" />}
              {t("apiToken.delete")}
            </Button>
          </div>
        ) : (
          <div className="flex w-full items-end gap-3">
            <div className="flex-1">
              <TextField label={`${label} API Key`} className="gap-2">
                <TextField.Input
                  type="password"
                  placeholder={t("apiToken.apiKeyPlaceholder")}
                  value={inputValue}
                  onChange={(e) => onInputChange(e.target.value)}
                />
              </TextField>
            </div>
            <Button
              variant="brand-primary"
              onClick={onSave}
              disabled={!inputValue.trim() || isSaving}
            >
              {isSaving && <Loader2 className="h-3 w-3 animate-spin" />}
              {isSaving ? t("apiToken.saving") : t("apiToken.save")}
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

export function ApiTokenPage() {
  const { t } = useTranslation();
  const { loading: eeLoading } = useEE();
  const [keys, setKeys] = useState<KeysRecord>({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [inputValues, setInputValues] = useState<Record<ApiProvider, string>>({
    [ApiProvider.OPENAI]: "",
    [ApiProvider.ANTHROPIC]: "",
    [ApiProvider.GEMINI]: "",
  });
  const [savingProvider, setSavingProvider] = useState<ApiProvider | null>(null);
  const [deletingProvider, setDeletingProvider] = useState<ApiProvider | null>(null);

  const fetchKeys = useCallback(async () => {
    try {
      const data = await EeApiKeysService.listApiKeysAirasEeApiKeysGet();
      const record = Object.fromEntries(data.keys.map((key) => [key.provider, key])) as KeysRecord;
      setKeys(record);
      setError(null);
    } catch {
      setError(t("apiToken.fetchError"));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    if (!eeLoading) {
      void fetchKeys();
    }
  }, [eeLoading, fetchKeys]);

  const handleSave = async (provider: ApiProvider) => {
    const apiKey = inputValues[provider].trim();
    if (!apiKey) return;

    setSavingProvider(provider);
    setError(null);
    try {
      await EeApiKeysService.saveApiKeyAirasEeApiKeysPost({
        provider,
        api_key: apiKey,
      });
      setInputValues((prev) => ({ ...prev, [provider]: "" }));
      await fetchKeys();
    } catch {
      setError(t("apiToken.saveError"));
    } finally {
      setSavingProvider(null);
    }
  };

  const handleDelete = async (provider: ApiProvider) => {
    const providerLabel = PROVIDERS.find((p) => p.id === provider)?.label ?? String(provider);
    if (!window.confirm(t("apiToken.deleteConfirm", { provider: providerLabel }))) return;

    setDeletingProvider(provider);
    setError(null);
    try {
      await EeApiKeysService.deleteApiKeyAirasEeApiKeysProviderDelete(provider);
      await fetchKeys();
    } catch {
      setError(t("apiToken.deleteError"));
    } finally {
      setDeletingProvider(null);
    }
  };

  return (
    <div className="flex w-full items-start h-full font-body text-white">
      <div className="flex flex-col items-center px-8 py-12 flex-1 overflow-y-auto">
        <div className="flex w-full max-w-[768px] flex-col items-start gap-8">
          <div className="flex w-full flex-col items-start gap-2">
            <span className="text-heading-1 font-heading-1 text-white">{t("apiToken.title")}</span>
            <span className="text-body font-body text-neutral-400">
              {t("apiToken.pageSubtitle")}
            </span>
          </div>

          {error && (
            <div className="w-full rounded-lg border border-error-800 bg-error-900/20 px-4 py-3 text-caption font-caption text-error-400">
              {error}
            </div>
          )}

          {loading ? (
            <div className="flex w-full items-center justify-center py-12">
              <Loader2 className="h-6 w-6 animate-spin text-neutral-400" />
            </div>
          ) : (
            <div className="flex w-full flex-col items-start gap-6">
              {PROVIDERS.map(({ id, label }) => (
                <ApiProviderCard
                  key={id}
                  id={id}
                  label={label}
                  entry={keys[id]}
                  inputValue={inputValues[id]}
                  isSaving={savingProvider === id}
                  isDeleting={deletingProvider === id}
                  onInputChange={(value) => setInputValues((prev) => ({ ...prev, [id]: value }))}
                  onSave={() => void handleSave(id)}
                  onDelete={() => void handleDelete(id)}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
