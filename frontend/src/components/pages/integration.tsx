import { Eye, EyeOff, Github, Loader2, Save, Trash2, Unlink } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
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

interface GitHubConnection {
  connected: boolean;
  github_login: string | null;
  connected_at: string | null;
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

export function GitHubOAuthCallback({ code }: { code: string }) {
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    const redirectUri = `${window.location.origin}/auth/github/callback`;
    const state = sessionStorage.getItem("github_oauth_state") ?? "";
    apiFetch("/github/callback", {
      method: "POST",
      body: JSON.stringify({ code, state, redirect_uri: redirectUri }),
    })
      .then(() => {
        sessionStorage.removeItem("github_oauth_state");
        setStatus("success");
        setTimeout(() => {
          window.location.href = "/?nav=integration";
        }, 1500);
      })
      .catch(() => {
        setStatus("error");
      });
  }, [code]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center space-y-2">
        {status === "loading" && <p className="text-muted-foreground">GitHubと連携中...</p>}
        {status === "success" && (
          <p className="text-green-600">GitHub連携が完了しました。リダイレクト中...</p>
        )}
        {status === "error" && (
          <div>
            <p className="text-destructive">GitHub連携に失敗しました。</p>
            <button
              type="button"
              className="mt-2 text-sm underline"
              onClick={() => {
                window.location.href = "/?nav=integration";
              }}
            >
              Integrationページに戻る
            </button>
          </div>
        )}
      </div>
    </div>
  );
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
  const [requiresApiKeys, setRequiresApiKeys] = useState(true);

  // GitHub OAuth state
  const [githubStatus, setGithubStatus] = useState<GitHubConnection>({
    connected: false,
    github_login: null,
    connected_at: null,
  });
  const [githubConnecting, setGithubConnecting] = useState(false);
  const [githubDisconnecting, setGithubDisconnecting] = useState(false);
  const [isRepoPrivate, setIsRepoPrivate] = useState(false);

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

  const fetchGithubStatus = useCallback(async () => {
    try {
      const data = await apiFetch<GitHubConnection>("/github/status");
      setGithubStatus(data);
    } catch {
      setGithubStatus({ connected: false, github_login: null, connected_at: null });
    }
  }, []);

  useEffect(() => {
    void fetchPlan();
    void fetchKeys();
    void fetchGithubStatus();
  }, [fetchPlan, fetchKeys, fetchGithubStatus]);

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

  const handleGithubConnect = async () => {
    setGithubConnecting(true);
    setError(null);
    try {
      const redirectUri = `${window.location.origin}/auth/github/callback`;
      const data = await apiFetch<{ authorize_url: string; state: string }>(
        `/github/authorize?redirect_uri=${encodeURIComponent(redirectUri)}`,
      );
      sessionStorage.setItem("github_oauth_state", data.state);
      window.location.href = data.authorize_url;
    } catch {
      setError("GitHub連携の開始に失敗しました");
      setGithubConnecting(false);
    }
  };

  const handleGithubDisconnect = async () => {
    setGithubDisconnecting(true);
    setError(null);
    try {
      await apiFetch("/github/disconnect", { method: "DELETE" });
      await fetchGithubStatus();
    } catch {
      setError("GitHub連携の解除に失敗しました");
    } finally {
      setGithubDisconnecting(false);
    }
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
              GitHubアカウントを連携して、リポジトリへのアクセスを有効にします。
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {githubStatus.connected ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3 rounded-md bg-muted/40 p-4">
                  <Github className="h-5 w-5" />
                  <div className="flex-1">
                    <p className="text-sm font-semibold">{githubStatus.github_login}</p>
                    <p className="text-xs text-muted-foreground">連携済み</p>
                  </div>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={handleGithubDisconnect}
                    disabled={githubDisconnecting}
                    className="text-destructive hover:text-destructive"
                  >
                    {githubDisconnecting ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <Unlink className="h-4 w-4" />
                    )}
                    <span className="ml-1">連携解除</span>
                  </Button>
                </div>
                <div className="flex items-center gap-3 rounded-md bg-muted/40 p-4">
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="repo-private"
                      checked={isRepoPrivate}
                      onCheckedChange={(checked) => setIsRepoPrivate(checked === true)}
                    />
                    <Label htmlFor="repo-private" className="text-sm">
                      リポジトリをプライベートで作成する
                    </Label>
                  </div>
                </div>
              </div>
            ) : (
              <Button onClick={handleGithubConnect} disabled={githubConnecting}>
                {githubConnecting ? (
                  <Loader2 className="h-4 w-4 animate-spin mr-2" />
                ) : (
                  <Github className="h-4 w-4 mr-2" />
                )}
                GitHubと連携する
              </Button>
            )}
          </CardContent>
        </Card>

        {requiresApiKeys ? (
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
                          onChange={(e) =>
                            setDrafts((prev) => ({ ...prev, [id]: e.target.value }))
                          }
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
        ) : null}
      </div>
    </div>
  );
}
