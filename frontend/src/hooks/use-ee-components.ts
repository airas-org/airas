import axios from "axios";
import type { ComponentType } from "react";
import { useEffect, useState } from "react";
import { isEnterpriseEnabled } from "@/ee/config";
import { EePlanService, OpenAPI } from "@/lib/api";

type EEComponents = {
  AuthCallback: ComponentType;
  UserMenu: ComponentType;
  LoginPage: ComponentType;
};

export type PlanType = "free" | "pro";

export interface EEState {
  components: EEComponents | null;
  isAuthenticated: boolean;
  planType: PlanType | null;
  loading: boolean;
}

const NON_EE_STATE: EEState = {
  components: null,
  isAuthenticated: false,
  planType: null,
  loading: false,
};

async function fetchPlanType(): Promise<PlanType> {
  try {
    const data = await EePlanService.getPlanAirasEePlanGet();
    return data.plan_type === "pro" ? "pro" : "free";
  } catch {
    return "free";
  }
}

export function useEE(): EEState {
  const [state, setState] = useState<EEState>(
    isEnterpriseEnabled()
      ? { components: null, isAuthenticated: false, planType: null, loading: true }
      : NON_EE_STATE,
  );

  useEffect(() => {
    if (!isEnterpriseEnabled()) return;

    let mounted = true;
    let interceptorId: number | null = null;
    let authSubscription: { unsubscribe: () => void } | null = null;

    async function load() {
      try {
        const [authCallback, userMenu, loginPage, interceptor, supabaseMod] = await Promise.all([
          import("@/ee/auth/components/AuthCallback"),
          import("@/ee/auth/components/UserMenu"),
          import("@/ee/auth/components/LoginPage"),
          import("@/ee/auth/lib/axios-interceptor"),
          import("@/ee/auth/lib/supabase"),
        ]);

        if (!mounted) return;

        const components: EEComponents = {
          AuthCallback: authCallback.AuthCallback,
          UserMenu: userMenu.UserMenu,
          LoginPage: loginPage.LoginPage,
        };

        const client = supabaseMod.getSupabase();
        if (!client) {
          console.error(
            "ENTERPRISE_ENABLED is true but VITE_SUPABASE_URL/VITE_SUPABASE_ANON_KEY are not set",
          );
          setState(NON_EE_STATE);
          return;
        }

        const previousToken = OpenAPI.TOKEN;
        OpenAPI.TOKEN = interceptor.openApiTokenResolver;
        interceptorId = axios.interceptors.request.use(interceptor.authRequestInterceptor);

        const {
          data: { session },
        } = await client.auth.getSession().catch((e: unknown) => {
          if (interceptorId !== null) {
            axios.interceptors.request.eject(interceptorId);
            interceptorId = null;
          }
          OpenAPI.TOKEN = previousToken;
          throw e;
        });

        if (!mounted) return;

        const authenticated = !!session;
        const planType = authenticated ? await fetchPlanType() : null;

        if (!mounted) return;

        setState({ components, isAuthenticated: authenticated, planType, loading: false });

        const {
          data: { subscription },
        } = client.auth.onAuthStateChange(async (_event, session) => {
          if (!mounted) return;
          const authed = !!session;
          const plan = authed ? await fetchPlanType() : null;
          if (mounted) {
            setState((prev) => ({ ...prev, isAuthenticated: authed, planType: plan }));
          }
        });
        authSubscription = subscription;
      } catch (error) {
        console.error("Failed to initialize EE modules", error);
        if (mounted) {
          setState((prev) => ({ ...prev, loading: false }));
        }
      }
    }

    void load();

    return () => {
      mounted = false;
      if (interceptorId !== null) {
        axios.interceptors.request.eject(interceptorId);
      }
      authSubscription?.unsubscribe();
    };
  }, []);

  return state;
}
