import { useEffect } from "react";
import { supabase } from "@/ee/auth/lib/supabase";
import { OpenAPI } from "@/lib/api";

export function AuthCallback() {
  useEffect(() => {
    supabase.auth.getSession().then(async ({ data: { session } }) => {
      if (session?.provider_token && session.user.app_metadata?.provider === "github") {
        try {
          const token =
            typeof OpenAPI.TOKEN === "function"
              ? await (OpenAPI.TOKEN as (options: unknown) => Promise<string>)({})
              : OpenAPI.TOKEN;
          await fetch(`${OpenAPI.BASE}/airas/ee/github-token`, {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              ...(token ? { Authorization: `Bearer ${token}` } : {}),
            },
            body: JSON.stringify({ github_token: session.provider_token }),
          });
        } catch (e) {
          console.error("Failed to save GitHub token:", e);
        }
      }
      window.location.href = "/";
    });
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-muted-foreground">Signing in...</div>
    </div>
  );
}
