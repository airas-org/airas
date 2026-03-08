import { Eye, EyeOff, Loader2, Save, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { OpenAPI } from "@/lib/api";

type ApiProvider = "openai" | "anthropic" | "gemini";

interface ApiKeyEntry {
  provider: ApiProvider;
  masked_key: string;
  created_at: string;
  updated_at: string;
}

const PROVIDERS: { id: ApiProvider; label: string; placeholder: string }[] = [
  { id: "openai", label: "OpenAI", placeholder: "sk-..." },
  { id: "anthropic", label: "Anthropic", placeholder: "sk-ant-..." },
  { id: "gemini", label: "Gemini", placeholder: "AI..." },
];

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };
  if (OpenAPI.TOKEN) {
    const token =
      typeof OpenAPI.TOKEN === "function"
        ? await (OpenAPI.TOKEN as (options: unknown) => Promise<string>)({})
        : OpenAPI.TOKEN;
    if (token) headers.Authorization = `Bearer ${token}`;
  }
  const res = await fetch(`${OpenAPI.BASE}/airas/ee${path}`, {
    ...init,
    headers: { ...headers, ...(init?.headers as Record<string, string>) },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<T>;
}

export function ApiTokenPage() {
  const { t } = useTranslation();
  const [savedKeys, setSavedKeys] = useState<ApiKeyEntry[]>([]);
  const [drafts, setDrafts] = useState<Record<ApiProvider, string>>({
    openai: "",
    anthropic: "",
    gemini: "",
  });
  const [visibleDrafts, setVisibleDrafts] = useState<Record<ApiProvider, boolean>>({
    openai: false,
    anthropic: false,
    gemini: false,
  });
  const [saving, setSaving] = useState<ApiProvider | null>(null);
  const [deleting, setDeleting] = useState<ApiProvider | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [requiresApiKeys, setRequiresApiKeys] = useState(true);

  const fetchPlan = useCallback(async () => {
    try {
      const data = await apiFetch<{ requires_api_keys: boolean }>("/plan");
      setRequiresApiKeys(data.requires_api_keys);
    } catch {
      setRequiresApiKeys(true);
    }
  }, []);

  const fetchKeys = useCallback(async () => {
    try {
      const data = await apiFetch<{ keys: ApiKeyEntry[] }>("/api-keys");
      setSavedKeys(data.keys);
    } catch {
      setSavedKeys([]);
    }
  }, []);

  useEffect(() => {
    void fetchPlan();
    void fetchKeys();
  }, [fetchPlan, fetchKeys]);

  const handleSave = async (provider: ApiProvider) => {
    const key = drafts[provider].trim();
    if (!key) return;
    setSaving(provider);
    setError(null);
    try {
      await apiFetch("/api-keys", {
        method: "POST",
        body: JSON.stringify({ provider, api_key: key }),
      });
      setDrafts((prev) => ({ ...prev, [provider]: "" }));
      await fetchKeys();
    } catch {
      setError(`Failed to save ${provider} key`);
    } finally {
      setSaving(null);
    }
  };

  const handleDelete = async (provider: ApiProvider) => {
    setDeleting(provider);
    setError(null);
    try {
      await apiFetch(`/api-keys/${provider}`, { method: "DELETE" });
      await fetchKeys();
    } catch {
      setError(`Failed to delete ${provider} key`);
    } finally {
      setDeleting(null);
    }
  };

  const getSavedKey = (provider: ApiProvider) => savedKeys.find((k) => k.provider === provider);

  const toggleVisibility = (provider: ApiProvider) => {
    setVisibleDrafts((prev) => ({ ...prev, [provider]: !prev[provider] }));
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-2xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font">{t("apiToken.title")}</h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          {t("apiToken.pageSubtitle")}
        </p>

        {error && (
          <div className="mt-4 rounded-md border border-error-200 bg-error-50 px-4 py-3 text-caption font-caption text-error-700">
            {error}
          </div>
        )}

        {requiresApiKeys ? (
          <div className="mt-6 rounded-lg border border-border bg-card p-5">
            <h2 className="text-body-bold font-body-bold text-default-font">API Keys</h2>
            <p className="text-caption font-caption text-subtext-color mt-1">
              APIキーは暗号化されて安全に保存されます。
            </p>
            <div className="mt-4 space-y-4">
              {PROVIDERS.map(({ id, label, placeholder }) => {
                const saved = getSavedKey(id);
                return (
                  <div key={id} className="space-y-3 rounded-md bg-neutral-50 p-4">
                    <div className="flex items-center justify-between">
                      <Label className="text-body-bold font-body-bold text-default-font">
                        {label}
                      </Label>
                      {saved && (
                        <span className="text-caption font-caption text-subtext-color font-mono">
                          {saved.masked_key}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2">
                      <div className="relative flex-1">
                        <Input
                          type={visibleDrafts[id] ? "text" : "password"}
                          value={drafts[id]}
                          onChange={(e) => setDrafts((prev) => ({ ...prev, [id]: e.target.value }))}
                          placeholder={saved ? "Enter new key to update..." : placeholder}
                          className="pr-10"
                        />
                        <button
                          type="button"
                          onClick={() => toggleVisibility(id)}
                          className="absolute right-2 top-1/2 -translate-y-1/2 text-subtext-color hover:text-default-font cursor-pointer"
                        >
                          {visibleDrafts[id] ? (
                            <EyeOff className="h-4 w-4" />
                          ) : (
                            <Eye className="h-4 w-4" />
                          )}
                        </button>
                      </div>
                      <Button
                        size="sm"
                        onClick={() => handleSave(id)}
                        disabled={!drafts[id].trim() || saving === id}
                      >
                        {saving === id ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <Save className="h-4 w-4" />
                        )}
                      </Button>
                      {saved && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleDelete(id)}
                          disabled={deleting === id}
                          className="text-destructive hover:text-destructive"
                        >
                          {deleting === id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <Trash2 className="h-4 w-4" />
                          )}
                        </Button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        ) : (
          <div className="mt-6 rounded-lg border border-border bg-card p-5">
            <p className="text-body font-body text-subtext-color">
              現在のプランではAPIキーの設定は不要です。
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
