import { Check, ExternalLink, Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { OpenAPI } from "@/lib/api";

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
      // API not available - fallback to free plan
      setPlan({ plan_type: "free", status: "active", stripe_customer_id: null });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.has("plan")) {
      // Redirected from Stripe checkout - poll for plan update
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
      await fetchPlan();
    } catch {
      setError("Failed to cancel subscription. Please try again.");
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
          success_url: `${window.location.origin}?plan=upgraded&nav=user-plan`,
          cancel_url: window.location.href,
        }),
      });
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch {
      setError("Failed to start checkout. Please try again.");
    } finally {
      setUpgrading(false);
    }
  };

  const currentPlan = plan.plan_type.toLowerCase();

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  return (
    <div className="flex-1 p-8 overflow-y-auto">
      <h1 className="text-2xl font-bold text-foreground">User Plan</h1>
      <p className="mt-2 text-sm text-muted-foreground">Manage your subscription plan.</p>

      {error && (
        <div className="mt-4 rounded-md border border-destructive bg-destructive/10 px-4 py-3 text-sm text-destructive">
          {error}
        </div>
      )}

      <div className="mt-8 grid gap-6 md:grid-cols-2 max-w-3xl">
        {/* Free Plan */}
        <Card
          className={
            currentPlan === "free"
              ? "border-2 border-blue-500 relative"
              : "border border-border relative"
          }
        >
          {currentPlan === "free" && (
            <div className="absolute -top-3 left-4">
              <span className="inline-block rounded-full bg-blue-500 px-3 py-0.5 text-xs font-semibold text-white">
                Current Plan
              </span>
            </div>
          )}
          <CardHeader>
            <CardTitle className="text-lg">Free</CardTitle>
            <p className="text-3xl font-bold text-foreground">
              $0<span className="text-sm font-normal text-muted-foreground">/month</span>
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <ul className="space-y-2">
              {FREE_FEATURES.map((feature) => (
                <li key={feature} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <Check className="h-4 w-4 mt-0.5 text-green-500 shrink-0" />
                  {feature}
                </li>
              ))}
            </ul>
            {currentPlan !== "free" && (
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  className={`flex-1 ${confirmDowngrade ? "border-destructive text-destructive hover:bg-destructive/10" : ""}`}
                  onClick={handleDowngrade}
                  disabled={downgrading}
                >
                  {downgrading ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Processing...
                    </>
                  ) : confirmDowngrade ? (
                    "Are you sure?"
                  ) : (
                    "Downgrade"
                  )}
                </Button>
                {confirmDowngrade && (
                  <Button
                    variant="outline"
                    className="shrink-0"
                    onClick={() => setConfirmDowngrade(false)}
                  >
                    Cancel
                  </Button>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Pro Plan */}
        <Card
          className={
            currentPlan === "pro"
              ? "border-2 border-blue-500 relative"
              : "border border-border relative"
          }
        >
          {currentPlan === "pro" && (
            <div className="absolute -top-3 left-4">
              <span className="inline-block rounded-full bg-blue-500 px-3 py-0.5 text-xs font-semibold text-white">
                Current Plan
              </span>
            </div>
          )}
          <CardHeader>
            <CardTitle className="text-lg">Pro</CardTitle>
            <p className="text-3xl font-bold text-foreground">
              $29<span className="text-sm font-normal text-muted-foreground">/month</span>
            </p>
          </CardHeader>
          <CardContent className="space-y-4">
            <ul className="space-y-2">
              {PRO_FEATURES.map((feature) => (
                <li key={feature} className="flex items-start gap-2 text-sm text-muted-foreground">
                  <Check className="h-4 w-4 mt-0.5 text-green-500 shrink-0" />
                  {feature}
                </li>
              ))}
            </ul>
            {currentPlan !== "pro" && (
              <Button className="w-full" onClick={handleUpgrade} disabled={upgrading}>
                {upgrading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Processing...
                  </>
                ) : (
                  <>
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Upgrade to Pro
                  </>
                )}
              </Button>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
