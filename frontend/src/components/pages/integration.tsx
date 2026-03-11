import { FeatherGithub, FeatherSlack } from "@subframe/core";
import { Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { OpenAPI } from "@/lib/api";
import { Avatar } from "@/ui/components/Avatar";
import { Button } from "@/ui/components/Button";
import { Switch } from "@/ui/components/Switch";

const GITHUB_SESSION_KEY = "github_session_token";

interface GitHubConnection {
  connected: boolean;
  github_login: string | null;
  connected_at: string | null;
}

function getGitHubSessionHeaders(): Record<string, string> {
  const sessionToken = localStorage.getItem(GITHUB_SESSION_KEY);
  if (sessionToken) {
    return { "X-GitHub-Session": sessionToken };
  }
  return {};
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...getGitHubSessionHeaders(),
  };
  const res = await fetch(`${OpenAPI.BASE}/airas/ee${path}`, {
    ...init,
    headers: { ...headers, ...(init?.headers as Record<string, string>) },
  });
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json() as Promise<T>;
}

export function GitHubOAuthCallback({ code }: { code: string }) {
  const { t } = useTranslation();
  const [status, setStatus] = useState<"loading" | "success" | "error">("loading");

  useEffect(() => {
    const redirectUri = `${window.location.origin}/auth/github/callback`;
    const state = sessionStorage.getItem("github_oauth_state") ?? "";

    fetch(`${OpenAPI.BASE}/airas/ee/github/callback`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ code, state, redirect_uri: redirectUri }),
    })
      .then(async (res) => {
        if (!res.ok) throw new Error(`API error: ${res.status}`);
        return res.json() as Promise<{
          connected: boolean;
          github_login: string;
          session_token: string;
        }>;
      })
      .then((data) => {
        sessionStorage.removeItem("github_oauth_state");
        localStorage.setItem(GITHUB_SESSION_KEY, data.session_token);
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
    <div className="flex min-h-screen items-center justify-center bg-neutral-950">
      <div className="text-center space-y-2">
        {status === "loading" && (
          <p className="text-neutral-400">{t("integration.github.connecting")}</p>
        )}
        {status === "success" && (
          <p className="text-success-400">{t("integration.github.success")}</p>
        )}
        {status === "error" && (
          <div>
            <p className="text-error-400">{t("integration.github.error")}</p>
            <button
              type="button"
              className="mt-2 text-sm underline text-neutral-400"
              onClick={() => {
                window.location.href = "/settings/integration";
              }}
            >
              {t("integration.github.backToPage")}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

export function IntegrationPage() {
  const { t, i18n } = useTranslation();
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
      setError(t("integration.github.connectError"));
      setGithubConnecting(false);
    }
  };

  const handleGithubDisconnect = async () => {
    setGithubDisconnecting(true);
    setError(null);
    try {
      await apiFetch("/github/disconnect", { method: "DELETE" });
      localStorage.removeItem(GITHUB_SESSION_KEY);
      await fetchGithubStatus();
    } catch {
      setError(t("integration.github.disconnectError"));
    } finally {
      setGithubDisconnecting(false);
    }
  };

  const connectedAt = githubStatus.connected_at
    ? new Date(githubStatus.connected_at).toLocaleDateString(i18n.language)
    : null;

  return (
    <div className="flex w-full items-start h-full font-body text-white">
      <div className="flex flex-col items-center px-8 py-12 flex-1 overflow-y-auto">
        <div className="flex w-full max-w-[768px] flex-col items-start gap-8">
          <div className="flex w-full flex-col items-start gap-2">
            <span className="text-heading-1 font-heading-1 text-white">
              {t("integration.connectionTitle")}
            </span>
            <span className="text-body font-body text-neutral-400">
              {t("integration.connectionSubtitle")}
            </span>
          </div>

          {error && (
            <div className="w-full rounded-lg border border-error-800 bg-error-900/20 px-4 py-3 text-caption font-caption text-error-400">
              {error}
            </div>
          )}

          <div className="flex w-full flex-col items-start gap-6">
            {/* GitHub Integration Card */}
            <div className="flex w-full flex-col items-start overflow-hidden rounded-xl border border-solid border-neutral-800 bg-neutral-900 shadow-sm">
              <div className="flex w-full flex-col items-start gap-6 px-6 py-6">
                <div className="flex w-full flex-col items-start gap-2">
                  <div className="flex w-full items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 flex-none items-center justify-center rounded-lg bg-neutral-800">
                        <FeatherGithub className="text-heading-2 font-heading-2 text-white" />
                      </div>
                      <span className="text-heading-2 font-heading-2 text-white">
                        GitHub<span className="text-error-400 ml-1">*</span>
                      </span>
                    </div>
                    {githubStatus.connected ? (
                      <Button
                        className="bg-error-900/10 text-error-400 hover:bg-error-900/20 border-error-400"
                        variant="destructive-secondary"
                        size="large"
                        onClick={handleGithubDisconnect}
                        disabled={githubDisconnecting}
                      >
                        {githubDisconnecting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                        {t("integration.github.disconnect")}
                      </Button>
                    ) : (
                      <Button
                        className="bg-neutral-800 text-neutral-300 hover:bg-neutral-700 border-neutral-700 text-caption font-caption"
                        variant="neutral-secondary"
                        size="medium"
                        onClick={handleGithubConnect}
                        disabled={githubConnecting}
                      >
                        {githubConnecting ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
                        {t("integration.github.connect")}
                      </Button>
                    )}
                  </div>
                  <span className="text-body font-body text-neutral-400">
                    {t("integration.github.description")}
                  </span>
                </div>

                {githubStatus.connected ? (
                  <>
                    <div className="flex w-full items-center justify-between rounded-lg px-5 py-4 border border-solid border-neutral-800/60 bg-neutral-950/50">
                      <div className="flex items-center gap-4">
                        <Avatar size="large">
                          {githubStatus.github_login?.charAt(0).toUpperCase() ?? "G"}
                        </Avatar>
                        <div className="flex flex-col items-start">
                          <span className="text-body-bold font-body-bold text-white">
                            {githubStatus.github_login}
                          </span>
                          <div className="flex items-center gap-1.5">
                            <div className="flex h-2 w-2 flex-none items-start rounded-full bg-success-500" />
                            <span className="text-caption font-caption text-neutral-400">
                              {t("integration.github.connected")}
                              {connectedAt ? ` (${connectedAt})` : ""}
                            </span>
                          </div>
                        </div>
                      </div>
                      <Button
                        className="border-neutral-700 bg-neutral-800 text-white hover:bg-neutral-700"
                        variant="neutral-secondary"
                        size="large"
                        onClick={handleGithubConnect}
                        disabled={githubConnecting}
                      >
                        {githubConnecting ? <Loader2 className="h-4 w-4 animate-spin" /> : null}
                        {t("integration.github.changeAccount")}
                      </Button>
                    </div>
                    <div className="flex w-full flex-col items-start gap-4 pt-6 border-t border-solid border-neutral-800/60">
                      <div className="flex w-full items-center justify-between">
                        <div className="flex flex-col items-start gap-1">
                          <span className="text-body-bold font-body-bold text-white">
                            {t("integration.github.privateRepo")}
                          </span>
                          <span className="text-caption font-caption text-neutral-400">
                            {t("integration.github.privateRepoDesc")}
                          </span>
                        </div>
                        <Switch
                          checked={isRepoPrivate}
                          onCheckedChange={(checked: boolean) => setIsRepoPrivate(checked)}
                        />
                      </div>
                    </div>
                  </>
                ) : null}
              </div>
            </div>

            {/* Slack Card (coming soon) */}
            <div className="flex w-full flex-col items-start overflow-hidden rounded-xl border border-solid border-neutral-800 bg-neutral-900 shadow-sm">
              <div className="flex w-full flex-col items-start gap-6 px-6 py-6">
                <div className="flex w-full flex-col items-start gap-2">
                  <div className="flex w-full items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className="flex h-10 w-10 flex-none items-center justify-center rounded-lg bg-neutral-800">
                        <FeatherSlack className="text-heading-2 font-heading-2 text-white" />
                      </div>
                      <span className="text-heading-2 font-heading-2 text-white">
                        {t("integration.slack.name")}
                      </span>
                    </div>
                    <Button
                      className="bg-neutral-800 text-neutral-300 border-neutral-700 text-caption font-caption"
                      variant="neutral-secondary"
                      size="medium"
                      disabled
                    >
                      {t("integration.slack.connect")}
                    </Button>
                  </div>
                  <span className="text-body font-body text-neutral-400">
                    {t("integration.slack.description")}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
