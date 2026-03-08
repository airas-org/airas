import { Github, Loader2, Unlink } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { OpenAPI } from "@/lib/api";

interface GitHubConnection {
  connected: boolean;
  github_login: string | null;
  connected_at: string | null;
}

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
          window.location.href = "/settings/integration";
        }, 1500);
      })
      .catch(() => {
        setStatus("error");
      });
  }, [code]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center space-y-2">
        {status === "loading" && <p className="text-subtext-color">GitHubと連携中...</p>}
        {status === "success" && (
          <p className="text-success-800">GitHub連携が完了しました。リダイレクト中...</p>
        )}
        {status === "error" && (
          <div>
            <p className="text-error-700">GitHub連携に失敗しました。</p>
            <button
              type="button"
              className="mt-2 text-sm underline"
              onClick={() => {
                window.location.href = "/settings/integration";
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
  const [error, setError] = useState<string | null>(null);

  const [githubStatus, setGithubStatus] = useState<GitHubConnection>({
    connected: false,
    github_login: null,
    connected_at: null,
  });
  const [githubConnecting, setGithubConnecting] = useState(false);
  const [githubDisconnecting, setGithubDisconnecting] = useState(false);
  const [isRepoPrivate, setIsRepoPrivate] = useState(false);

  const fetchGithubStatus = useCallback(async () => {
    try {
      const data = await apiFetch<GitHubConnection>("/github/status");
      setGithubStatus(data);
    } catch {
      setGithubStatus({ connected: false, github_login: null, connected_at: null });
    }
  }, []);

  useEffect(() => {
    void fetchGithubStatus();
  }, [fetchGithubStatus]);

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
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-2xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font">接続</h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          外部サービスとの連携を管理します
        </p>

        {error && (
          <div className="mt-4 rounded-md border border-error-200 bg-error-50 px-4 py-3 text-caption font-caption text-error-700">
            {error}
          </div>
        )}

        <div className="mt-6 rounded-lg border border-border bg-card p-5">
          <h2 className="text-body-bold font-body-bold text-default-font">GitHub Integration</h2>
          <p className="text-caption font-caption text-subtext-color mt-1">
            GitHubアカウントを連携して、リポジトリへのアクセスを有効にします。
          </p>
          <div className="mt-4">
            {githubStatus.connected ? (
              <div className="space-y-4">
                <div className="flex items-center gap-3 rounded-md bg-neutral-50 p-4">
                  <Github className="h-5 w-5" />
                  <div className="flex-1">
                    <p className="text-body-bold font-body-bold text-default-font">
                      {githubStatus.github_login}
                    </p>
                    <p className="text-caption font-caption text-subtext-color">連携済み</p>
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
                <div className="flex items-center gap-3 rounded-md bg-neutral-50 p-4">
                  <div className="flex items-center gap-2">
                    <Checkbox
                      id="repo-private"
                      checked={isRepoPrivate}
                      onCheckedChange={(checked) => setIsRepoPrivate(checked === true)}
                    />
                    <Label htmlFor="repo-private" className="text-body font-body text-default-font">
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
          </div>
        </div>
      </div>
    </div>
  );
}
