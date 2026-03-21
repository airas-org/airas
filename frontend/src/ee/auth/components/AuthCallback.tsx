import { useEffect } from "react";
import { getSupabase } from "@/ee/auth/lib/supabase";

export function AuthCallback() {
  useEffect(() => {
    const client = getSupabase();
    if (client) {
      client.auth.getSession().then(() => {
        window.location.href = "/";
      });
    } else {
      window.location.href = "/";
    }
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-muted-foreground">Signing in...</div>
    </div>
  );
}
