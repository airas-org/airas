import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Badge, Button, TextField } from "@/ui";

interface TokenEntry {
  id: string;
  name: string;
  token: string;
  createdAt: Date;
  lastUsed: Date | null;
}

const mockTokens: TokenEntry[] = [
  {
    id: "tok-1",
    name: "Research Script",
    token: "airas_sk_...3f8a",
    createdAt: new Date("2026-02-15"),
    lastUsed: new Date("2026-03-03"),
  },
  {
    id: "tok-2",
    name: "CI/CD Pipeline",
    token: "airas_sk_...9b2c",
    createdAt: new Date("2026-01-20"),
    lastUsed: new Date("2026-02-28"),
  },
];

export function ApiTokenPage() {
  const { t, i18n } = useTranslation();
  const [tokens, setTokens] = useState<TokenEntry[]>(mockTokens);
  const [newTokenName, setNewTokenName] = useState("");
  const [generatedToken, setGeneratedToken] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  const handleGenerate = () => {
    if (!newTokenName.trim()) return;
    const token = `airas_sk_${crypto.randomUUID().replace(/-/g, "").slice(0, 32)}`;
    const entry: TokenEntry = {
      id: `tok-${Date.now()}`,
      name: newTokenName.trim(),
      token,
      createdAt: new Date(),
      lastUsed: null,
    };
    setTokens((prev) => [entry, ...prev]);
    setGeneratedToken(token);
    setNewTokenName("");
  };

  const handleCopy = async () => {
    if (!generatedToken) return;
    if (typeof navigator === "undefined" || !navigator.clipboard) {
      alert(t("apiToken.copyError"));
      return;
    }
    try {
      await navigator.clipboard.writeText(generatedToken);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (error) {
      console.error("Failed to copy API token to clipboard", error);
      alert(t("apiToken.copyError"));
    }
  };

  const handleRevoke = (id: string) => {
    setTokens((prev) => prev.filter((t) => t.id !== id));
  };

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font">{t("apiToken.title")}</h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          {t("apiToken.pageSubtitle")}
        </p>

        {/* Generate new token */}
        <div className="mt-6 rounded-lg border border-border bg-card p-5">
          <h2 className="text-body-bold font-body-bold text-default-font">
            {t("apiToken.generateSection")}
          </h2>
          <div className="mt-3 flex items-end gap-3">
            <div className="flex-1">
              <TextField label={t("apiToken.tokenName")}>
                <TextField.Input
                  placeholder={t("apiToken.tokenNamePlaceholder")}
                  value={newTokenName}
                  onChange={(e) => setNewTokenName(e.target.value)}
                />
              </TextField>
            </div>
            <Button onClick={handleGenerate} disabled={!newTokenName.trim()}>
              {t("apiToken.generateButton")}
            </Button>
          </div>

          {generatedToken && (
            <div className="mt-4 rounded-md border border-warning-200 bg-warning-50 p-3">
              <p className="text-xs font-semibold text-warning-800">{t("apiToken.tokenWarning")}</p>
              <div className="mt-2 flex items-center gap-2">
                <code className="flex-1 rounded bg-neutral-900 px-3 py-2 text-xs text-neutral-100 font-mono break-all">
                  {generatedToken}
                </code>
                <button
                  type="button"
                  onClick={() => void handleCopy()}
                  className="rounded-md bg-neutral-200 px-3 py-1.5 text-xs font-medium text-neutral-700 hover:bg-neutral-300 hover:text-neutral-900 transition-colors cursor-pointer shrink-0"
                >
                  {copied ? t("apiToken.copied") : t("apiToken.copy")}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Existing tokens */}
        <div className="mt-6 rounded-lg border border-border bg-card p-5">
          <h2 className="text-body-bold font-body-bold text-default-font">
            {t("apiToken.issuedTokens")}
          </h2>
          {tokens.length === 0 ? (
            <p className="mt-3 text-caption font-caption text-subtext-color">
              {t("apiToken.noTokensYet")}
            </p>
          ) : (
            <div className="mt-3 space-y-3">
              {tokens.map((entry) => (
                <div
                  key={entry.id}
                  className="flex items-center justify-between rounded-md border border-border px-4 py-3"
                >
                  <div className="flex flex-col gap-0.5">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium text-default-font">{entry.name}</span>
                      <Badge variant="neutral" className="text-[10px]">
                        {entry.token}
                      </Badge>
                    </div>
                    <span className="text-[11px] text-subtext-color">
                      {t("apiToken.createdAt")}: {entry.createdAt.toLocaleDateString(i18n.language)}
                      {entry.lastUsed &&
                        ` / ${t("apiToken.lastUsed")}: ${entry.lastUsed.toLocaleDateString(i18n.language)}`}
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleRevoke(entry.id)}
                    className="rounded-md px-3 py-1.5 text-xs font-medium text-error-700 hover:bg-error-50 transition-colors cursor-pointer"
                  >
                    {t("apiToken.revoke")}
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Usage example */}
        <div className="mt-6 rounded-lg border border-border bg-card p-5">
          <h2 className="text-body-bold font-body-bold text-default-font">
            {t("apiToken.usageExample")}
          </h2>
          <div className="mt-3 rounded-md bg-neutral-900 p-4 overflow-x-auto">
            <pre className="text-xs text-neutral-100 font-mono whitespace-pre">{`curl -H "Authorization: Bearer airas_sk_your_token_here" \\
  https://api.airas.io/v1/verifications`}</pre>
          </div>
        </div>
      </div>
    </div>
  );
}
