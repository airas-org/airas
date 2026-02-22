import { useEffect } from "react";
import { supabase } from "@/ee/auth/lib/supabase";

export function AuthCallback() {
  useEffect(() => {
    supabase.auth.getSession().then(() => {
      window.location.href = "/";
    });
  }, []);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-muted-foreground">Signing in...</div>
    </div>
  );
}
