import axios from "axios";
import { useEffect, useState } from "react";
import { OpenAPI } from "@/lib/api";

type EEComponents = {
  AuthCallback: React.ComponentType;
  UserMenu: React.ComponentType;
  LoginPage: React.ComponentType;
};

export interface EEState {
  components: EEComponents | null;
  isAuthenticated: boolean;
}

export function useEE(): EEState {
  const [state, setState] = useState<EEState>({
    components: null,
    isAuthenticated: false,
  });

  useEffect(() => {
    let mounted = true;
    let interceptorId: number | null = null;

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
          setState({ components, isAuthenticated: false });
          return;
        }

        OpenAPI.TOKEN = interceptor.openApiTokenResolver;
        interceptorId = axios.interceptors.request.use(interceptor.authRequestInterceptor);

        const {
          data: { session },
        } = await client.auth.getSession();

        if (!mounted) return;

        setState({ components, isAuthenticated: !!session });

        client.auth.onAuthStateChange((_event, session) => {
          if (mounted) {
            setState((prev) => ({ ...prev, isAuthenticated: !!session }));
          }
        });
      } catch {
        // EE components not available
      }
    }

    void load();

    return () => {
      mounted = false;
      if (interceptorId !== null) {
        axios.interceptors.request.eject(interceptorId);
      }
    };
  }, []);

  return state;
}
