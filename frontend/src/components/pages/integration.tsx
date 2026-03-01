import { Eye, EyeOff, Loader2, Save, Trash2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
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

export function IntegrationPage() {
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

  const fetchKeys = useCallback(async () => {
    try {
      const data = await apiFetch<{ keys: ApiKeyEntry[] }>("/api-keys");
      setSavedKeys(data.keys);
    } catch {
      // API not available yet - use empty list as fallback
      setSavedKeys([]);
    }
  }, []);

  useEffect(() => {
    void fetchKeys();
  }, [fetchKeys]);

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
    <div className="flex-1 p-8 overflow-y-auto">
      <h1 className="text-2xl font-bold text-foreground">Integration</h1>

      {error && (
        <div className="mt-4 rounded-md border border-destructive bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="mt-6 space-y-6">
        <Card>
          <CardHeader>
            <CardTitle>GitHub Integration</CardTitle>
            <CardDescription>
              Connect your GitHub account to enable repository access and collaboration features.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <span className="inline-block rounded-md bg-muted px-3 py-1 text-xs text-muted-foreground">
              Coming soon
            </span>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>API Keys</CardTitle>
            <CardDescription>
              Manage your API keys for LLM providers. Keys are encrypted and stored securely.
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {PROVIDERS.map(({ id, label, placeholder }) => {
              const saved = getSavedKey(id);
              return (
                <div key={id} className="space-y-3 rounded-md bg-muted/40 p-4">
                  <div className="flex items-center justify-between">
                    <Label className="text-sm font-semibold">{label}</Label>
                    {saved && (
                      <span className="text-xs text-muted-foreground font-mono">
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
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
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
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
