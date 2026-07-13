import { Check, Loader2 } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { OpenAPI } from "@/lib/api";

interface PlanInfo {
  plan_type: string;
  status: string;
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

export function UserPlanPage() {
  const { t } = useTranslation();
  const [plan, setPlan] = useState<PlanInfo>({
    plan_type: "free",
    status: "active",
  });
  const [loading, setLoading] = useState(true);

  const fetchPlan = useCallback(async () => {
    try {
      const data = await apiFetch<PlanInfo>("/plan");
      setPlan(data);
    } catch {
      setPlan({ plan_type: "free", status: "active" });
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void fetchPlan();
  }, [fetchPlan]);

  const currentPlan = plan.plan_type.toLowerCase();
  const freeFeatures = t("userPlan.freeFeatures", { returnObjects: true }) as string[];
  const proFeatures = t("userPlan.proFeatures", { returnObjects: true }) as string[];

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
        <h1 className="text-heading-2 font-heading-2 text-default-font">
          {t("userPlan.planTitle")}
        </h1>
        <p className="text-caption font-caption text-subtext-color mt-1">
          {t("userPlan.planSubtitle")}
        </p>

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
                  {t("userPlan.currentPlan")}
                </span>
              </div>
            )}
            <h2 className="text-body-bold font-body-bold text-default-font mt-1">Free</h2>
            <p className="text-heading-2 font-heading-2 text-default-font mt-2">
              $0
              <span className="text-caption font-caption text-subtext-color">
                {t("userPlan.perMonth")}
              </span>
            </p>
            <ul className="mt-4 space-y-2">
              {freeFeatures.map((feature) => (
                <li
                  key={feature}
                  className="flex items-start gap-2 text-caption font-caption text-subtext-color"
                >
                  <Check className="h-4 w-4 mt-0.5 text-success-700 shrink-0" />
                  {feature}
                </li>
              ))}
            </ul>
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
                  {t("userPlan.currentPlan")}
                </span>
              </div>
            )}
            <h2 className="text-body-bold font-body-bold text-default-font mt-1">Pro</h2>
            <p className="text-heading-2 font-heading-2 text-default-font mt-2">
              $29
              <span className="text-caption font-caption text-subtext-color">
                {t("userPlan.perMonth")}
              </span>
            </p>
            <ul className="mt-4 space-y-2">
              {proFeatures.map((feature) => (
                <li
                  key={feature}
                  className="flex items-start gap-2 text-caption font-caption text-subtext-color"
                >
                  <Check className="h-4 w-4 mt-0.5 text-success-700 shrink-0" />
                  {feature}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
