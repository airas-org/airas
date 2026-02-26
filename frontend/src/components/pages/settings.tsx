"use client";

import axios from "axios";
import { CheckCircle, Eye, EyeOff, Github, Loader2, Trash2, XCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { OpenAPI } from "@/lib/api";

interface GitHubSettings {
  is_connected: boolean;
  github_username: string | null;
  token_last4: string | null;
}

interface ConnectionStatus {
  is_valid: boolean;
  github_username: string | null;
  error: string | null;
}

const API_BASE = OpenAPI.BASE || "";

export function SettingsPage() {
  const [githubSettings, setGithubSettings] = useState<GitHubSettings | null>(null);
  const [connectionStatus, setConnectionStatus] = useState<ConnectionStatus | null>(null);
  const [tokenInput, setTokenInput] = useState("");
  const [showToken, setShowToken] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isChecking, setIsChecking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const fetchSettings = useCallback(async () => {
    setIsLoading(true);
    try {
      const response = await axios.get<GitHubSettings>(`${API_BASE}/airas/v1/settings/github`);
      setGithubSettings(response.data);
    } catch {
      setGithubSettings({ is_connected: false, github_username: null, token_last4: null });
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchSettings();
  }, [fetchSettings]);

  const handleSaveToken = async () => {
    if (!tokenInput.trim()) return;
    setIsSaving(true);
    setError(null);
    setSuccessMessage(null);

    try {
      const response = await axios.post<GitHubSettings>(`${API_BASE}/airas/v1/settings/github`, {
        github_token: tokenInput.trim(),
      });
      setGithubSettings(response.data);
      setTokenInput("");
      setSuccessMessage("GitHub token saved successfully");
      setConnectionStatus(null);
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.data?.detail) {
        setError(String(err.response.data.detail));
      } else {
        setError("Failed to save GitHub token");
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteToken = async () => {
    setIsDeleting(true);
    setError(null);
    setSuccessMessage(null);

    try {
      await axios.delete(`${API_BASE}/airas/v1/settings/github`);
      setGithubSettings({ is_connected: false, github_username: null, token_last4: null });
      setConnectionStatus(null);
      setSuccessMessage("GitHub integration removed");
    } catch {
      setError("Failed to remove GitHub integration");
    } finally {
      setIsDeleting(false);
    }
  };

  const handleCheckConnection = async () => {
    setIsChecking(true);
    setError(null);

    try {
      const response = await axios.get<ConnectionStatus>(
        `${API_BASE}/airas/v1/settings/github/status`,
      );
      setConnectionStatus(response.data);
    } catch {
      setError("Failed to check connection status");
    } finally {
      setIsChecking(false);
    }
  };

  return (
    <div className="flex-1 bg-background overflow-y-auto">
      <div className="sticky top-0 z-10 border-b border-border bg-card px-6 py-4">
        <h2 className="text-lg font-semibold text-foreground">Settings</h2>
      </div>
      <div className="p-6 max-w-2xl">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <Github className="h-6 w-6" />
              <div>
                <CardTitle>GitHub Integration</CardTitle>
                <CardDescription>
                  Connect your GitHub account to enable automatic repository creation and management
                </CardDescription>
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            {isLoading ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Loading settings...</span>
              </div>
            ) : (
              <>
                {/* Connection Status */}
                <div className="flex items-center gap-3">
                  <span className="text-sm font-medium">Status:</span>
                  {githubSettings?.is_connected ? (
                    <Badge variant="default" className="gap-1">
                      <CheckCircle className="h-3 w-3" />
                      Connected
                    </Badge>
                  ) : (
                    <Badge variant="outline" className="gap-1">
                      <XCircle className="h-3 w-3" />
                      Not connected
                    </Badge>
                  )}
                </div>

                {/* Connected User Info */}
                {githubSettings?.is_connected && (
                  <div className="rounded-md border border-border bg-card/60 p-4 space-y-2">
                    {githubSettings.github_username && (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">Username:</span>
                        <span className="text-sm font-medium">
                          {githubSettings.github_username}
                        </span>
                      </div>
                    )}
                    {githubSettings.token_last4 && (
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-muted-foreground">Token:</span>
                        <span className="text-sm font-mono">
                          {"*".repeat(36)}
                          {githubSettings.token_last4}
                        </span>
                      </div>
                    )}
                    <div className="flex gap-2 pt-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleCheckConnection}
                        disabled={isChecking}
                      >
                        {isChecking ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          "Check Connection"
                        )}
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={handleDeleteToken}
                        disabled={isDeleting}
                      >
                        {isDeleting ? (
                          <Loader2 className="h-4 w-4 animate-spin" />
                        ) : (
                          <>
                            <Trash2 className="h-4 w-4" />
                            Remove
                          </>
                        )}
                      </Button>
                    </div>

                    {connectionStatus && (
                      <div
                        className={`mt-2 rounded-md p-3 text-sm ${
                          connectionStatus.is_valid
                            ? "bg-green-50 text-green-700 dark:bg-green-950 dark:text-green-300"
                            : "bg-red-50 text-red-700 dark:bg-red-950 dark:text-red-300"
                        }`}
                      >
                        {connectionStatus.is_valid ? (
                          <div className="flex items-center gap-2">
                            <CheckCircle className="h-4 w-4" />
                            <span>
                              Connection successful
                              {connectionStatus.github_username &&
                                ` (${connectionStatus.github_username})`}
                            </span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <XCircle className="h-4 w-4" />
                            <span>{connectionStatus.error || "Connection failed"}</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}

                {/* Token Input */}
                <div className="space-y-3">
                  <Label htmlFor="github-token">
                    {githubSettings?.is_connected
                      ? "Update Personal Access Token"
                      : "Personal Access Token"}
                  </Label>
                  <p className="text-xs text-muted-foreground">
                    Create a token at{" "}
                    <a
                      href="https://github.com/settings/tokens"
                      target="_blank"
                      rel="noreferrer"
                      className="text-primary underline"
                    >
                      github.com/settings/tokens
                    </a>{" "}
                    with <code className="text-xs bg-muted px-1 py-0.5 rounded">repo</code> and{" "}
                    <code className="text-xs bg-muted px-1 py-0.5 rounded">workflow</code> scopes.
                  </p>
                  <div className="flex gap-2">
                    <div className="relative flex-1">
                      <Input
                        id="github-token"
                        type={showToken ? "text" : "password"}
                        value={tokenInput}
                        onChange={(e) => setTokenInput(e.target.value)}
                        placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                        className="pr-10"
                      />
                      <button
                        type="button"
                        className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                        onClick={() => setShowToken((prev) => !prev)}
                      >
                        {showToken ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                      </button>
                    </div>
                    <Button onClick={handleSaveToken} disabled={isSaving || !tokenInput.trim()}>
                      {isSaving ? <Loader2 className="h-4 w-4 animate-spin" /> : "Save"}
                    </Button>
                  </div>
                </div>

                {/* Messages */}
                {error && (
                  <div className="rounded-md bg-red-50 p-3 text-sm text-red-700 dark:bg-red-950 dark:text-red-300">
                    {error}
                  </div>
                )}
                {successMessage && (
                  <div className="rounded-md bg-green-50 p-3 text-sm text-green-700 dark:bg-green-950 dark:text-green-300">
                    {successMessage}
                  </div>
                )}

                {/* Info */}
                <div className="rounded-md border border-border bg-muted/30 p-4 text-xs text-muted-foreground space-y-1">
                  <p className="font-medium text-foreground text-sm">
                    How GitHub integration works
                  </p>
                  <p>
                    When a token is set here, it is used automatically for all GitHub operations
                    (repository creation, code push, GitHub Actions, etc.) without needing to set
                    the{" "}
                    <code className="bg-muted px-1 py-0.5 rounded">GH_PERSONAL_ACCESS_TOKEN</code>{" "}
                    environment variable.
                  </p>
                  <p>If no token is set here, the system falls back to the environment variable.</p>
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
