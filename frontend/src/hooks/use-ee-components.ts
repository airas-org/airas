import axios from "axios";
import type { ComponentType } from "react";
import { useEffect, useState } from "react";
import { OpenAPI } from "@/lib/api";

type EEComponents = {
  AuthCallback: ComponentType;
  UserMenu: ComponentType;
  LoginPage: ComponentType;
};

export interface EEState {
  components: EEComponents | null;
  isAuthenticated: boolean;
  loading: boolean;
}

export function useEE(): EEState {
  const [state, setState] = useState<EEState>({
    components: null,
    isAuthenticated: false,
    loading: true,
  });

  useEffect(() => {
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
          // Supabase未設定: コンポーネントは使えるが未認証
          setState({ components, isAuthenticated: false, loading: false });
          return;
        }

        OpenAPI.TOKEN = interceptor.openApiTokenResolver;
        interceptorId = axios.interceptors.request.use(interceptor.authRequestInterceptor);

        const {
          data: { session },
        } = await client.auth.getSession();

        if (!mounted) return;

        setState({ components, isAuthenticated: !!session, loading: false });

        const {
          data: { subscription },
        } = client.auth.onAuthStateChange((_event, session) => {
          if (mounted) {
            setState((prev) => ({ ...prev, isAuthenticated: !!session }));
          }
        });
        authSubscription = subscription;
      } catch {
        // EE components not available
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
