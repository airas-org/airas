import { Check, ExternalLink, Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { OpenAPI } from "@/lib/api";
import { Button } from "@/ui";

interface PlanInfo {
  plan_type: string;
  status: string;
  stripe_customer_id: string | null;
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

const FREE_FEATURES = ["Basic autonomous research", "Community support", "Standard LLM access"];

const PRO_FEATURES = [
  "Everything in Free",
  "Priority research execution",
  "Advanced LLM models",
  "Priority support",
  "Custom integrations",
];

export function UserPlanPage() {
  const [plan, setPlan] = useState<PlanInfo>({
    plan_type: "free",
    status: "active",
    stripe_customer_id: null,
  });
  const [loading, setLoading] = useState(true);
  const [upgrading, setUpgrading] = useState(false);
  const [downgrading, setDowngrading] = useState(false);
  const [confirmDowngrade, setConfirmDowngrade] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchPlan = useCallback(async () => {
    try {
      const data = await apiFetch<PlanInfo>("/plan");
      setPlan(data);
    } catch {
      setPlan({ plan_type: "free", status: "active", stripe_customer_id: null });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.has("plan")) {
      params.delete("plan");
      const cleanUrl = `${window.location.pathname}${params.toString() ? `?${params}` : ""}`;
      window.history.replaceState({}, "", cleanUrl);

      let attempts = 0;
      const poll = setInterval(() => {
        attempts++;
        void fetchPlan();
        if (attempts >= 10) clearInterval(poll);
      }, 2000);
      return () => clearInterval(poll);
    }
    void fetchPlan();
  }, [fetchPlan]);

  const handleDowngrade = async () => {
    if (!confirmDowngrade) {
      setConfirmDowngrade(true);
      return;
    }
    setDowngrading(true);
    setConfirmDowngrade(false);
    setError(null);
    try {
      await apiFetch("/stripe/cancel", { method: "POST" });
      window.location.reload();
    } catch {
      setError("ダウングレードに失敗しました。もう一度お試しください。");
    } finally {
      setDowngrading(false);
    }
  };

  const handleUpgrade = async () => {
    setUpgrading(true);
    setError(null);
    try {
      const data = await apiFetch<{ checkout_url: string }>("/stripe/checkout", {
        method: "POST",
        body: JSON.stringify({
          success_url: `${window.location.origin}/settings/user-plan?plan=upgraded`,
          cancel_url: window.location.href,
        }),
      });
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch {
      setError("チェックアウトの開始に失敗しました。もう一度お試しください。");
    } finally {
      setUpgrading(false);
    }
  };

  const currentPlan = plan.plan_type.toLowerCase();

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-subtext-color" />
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto">
      <div className="max-w-3xl mx-auto px-8 py-8">
        <h1 className="text-heading-2 font-heading-2 text-default-font">プラン</h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          サブスクリプションプランを管理します
        </p>

        {error && (
          <div className="mt-4 rounded-md border border-error-200 bg-error-50 px-4 py-3 text-caption font-caption text-error-700">
            {error}
          </div>
        )}

        <div className="mt-6 grid gap-6 md:grid-cols-2">
          {/* Free Plan */}
          <div
            className={`rounded-lg border p-5 relative ${
              currentPlan === "free" ? "border-2 border-brand-600" : "border-border bg-card"
            }`}
          >
            {currentPlan === "free" && (
              <div className="absolute -top-3 left-4">
                <span className="inline-block rounded-full bg-brand-600 px-3 py-0.5 text-caption font-caption text-white">
                  現在のプラン
                </span>
              </div>
            )}
            <h2 className="text-body-bold font-body-bold text-default-font mt-1">Free</h2>
            <p className="text-heading-2 font-heading-2 text-default-font mt-2">
              $0<span className="text-caption font-caption text-subtext-color">/month</span>
            </p>
            <ul className="mt-4 space-y-2">
              {FREE_FEATURES.map((feature) => (
                <li
                  key={feature}
                  className="flex items-start gap-2 text-caption font-caption text-subtext-color"
                >
                  <Check className="h-4 w-4 mt-0.5 text-success-700 shrink-0" />
                  {feature}
                </li>
              ))}
            </ul>
            {currentPlan !== "free" && (
              <div className="mt-4 flex gap-2">
                <Button
                  variant="neutral-secondary"
                  className={`flex-1 ${confirmDowngrade ? "border-destructive text-destructive hover:bg-destructive/10" : ""}`}
                  onClick={handleDowngrade}
                  disabled={downgrading}
                >
                  {downgrading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      処理中...
                    </>
                  ) : confirmDowngrade ? (
                    "本当にダウングレードしますか？"
                  ) : (
                    "ダウングレード"
                  )}
                </Button>
                {confirmDowngrade && (
                  <Button
                    variant="neutral-secondary"
                    className="shrink-0"
                    onClick={() => setConfirmDowngrade(false)}
                  >
                    キャンセル
                  </Button>
                )}
              </div>
            )}
          </div>

          {/* Pro Plan */}
          <div
            className={`rounded-lg border p-5 relative ${
              currentPlan === "pro" ? "border-2 border-brand-600" : "border-border bg-card"
            }`}
          >
            {currentPlan === "pro" && (
              <div className="absolute -top-3 left-4">
                <span className="inline-block rounded-full bg-brand-600 px-3 py-0.5 text-caption font-caption text-white">
                  現在のプラン
                </span>
              </div>
            )}
            <h2 className="text-body-bold font-body-bold text-default-font mt-1">Pro</h2>
            <p className="text-heading-2 font-heading-2 text-default-font mt-2">
              $29<span className="text-caption font-caption text-subtext-color">/month</span>
            </p>
            <ul className="mt-4 space-y-2">
              {PRO_FEATURES.map((feature) => (
                <li
                  key={feature}
                  className="flex items-start gap-2 text-caption font-caption text-subtext-color"
                >
                  <Check className="h-4 w-4 mt-0.5 text-success-700 shrink-0" />
                  {feature}
                </li>
              ))}
            </ul>
            {currentPlan !== "pro" && (
              <Button className="w-full mt-4" onClick={handleUpgrade} disabled={upgrading}>
                {upgrading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    処理中...
                  </>
                ) : (
                  <>
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Pro にアップグレード
                  </>
                )}
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
