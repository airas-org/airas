import axios from "axios";
import { useEffect, useState } from "react";
import { isEnterpriseEnabled } from "@/ee/config";
import { OpenAPI } from "@/lib/api";

// Lazy-loaded EE components (only imported when EE is enabled)
type AuthGuardType = typeof import("@/ee/auth/components/AuthGuard").AuthGuard;
type UserMenuType = typeof import("@/ee/auth/components/UserMenu").UserMenu;
type AuthCallbackType = typeof import("@/ee/auth/components/AuthCallback").AuthCallback;

export interface EEComponents {
  AuthGuard: AuthGuardType;
  UserMenu: UserMenuType;
  AuthCallback: AuthCallbackType;
}

export function useEEComponents() {
  const [eeComponents, setEeComponents] = useState<EEComponents | null>(null);

  useEffect(() => {
    if (!isEnterpriseEnabled()) return;

    Promise.all([
      import("@/ee/auth/components/AuthGuard"),
      import("@/ee/auth/components/UserMenu"),
      import("@/ee/auth/components/AuthCallback"),
      import("@/ee/auth/lib/axios-interceptor"),
    ]).then(([authGuard, userMenu, authCallback, interceptor]) => {
      // Set token resolver for the OpenAPI generated client
      OpenAPI.TOKEN = interceptor.openApiTokenResolver;
      // Also keep axios interceptor for any direct axios calls
      axios.interceptors.request.use(interceptor.authRequestInterceptor);
      setEeComponents({
        AuthGuard: authGuard.AuthGuard,
        UserMenu: userMenu.UserMenu,
        AuthCallback: authCallback.AuthCallback,
      });
    });
  }, []);

  return eeComponents;
}
