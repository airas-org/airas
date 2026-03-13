import { LogOut, UserCircle } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { useAuth } from "@/ee/auth/hooks/useAuth";
import { useSession } from "@/ee/auth/hooks/useSession";
import { OpenAPI } from "@/lib/api";

export function UserMenu() {
  const { session } = useSession();
  const { signOut } = useAuth();
  const [open, setOpen] = useState(false);
  const [plan, setPlan] = useState<string | null>(null);

  const fetchPlan = useCallback(async () => {
    try {
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      if (OpenAPI.TOKEN) {
        const token =
          typeof OpenAPI.TOKEN === "function"
            ? await (OpenAPI.TOKEN as (options: unknown) => Promise<string>)({})
            : OpenAPI.TOKEN;
        if (token) headers.Authorization = `Bearer ${token}`;
      }
      const res = await fetch(`${OpenAPI.BASE}/airas/ee/plan`, { headers });
      if (res.ok) {
        const data = (await res.json()) as { plan_type: string };
        setPlan(data.plan_type === "pro" ? "Pro" : "Free");
      }
    } catch {
      // API not available - fallback
    }
  }, []);

  useEffect(() => {
    if (session) void fetchPlan();
  }, [session, fetchPlan]);

  if (!session) return null;

  const avatarUrl = (session.user.user_metadata?.avatar_url as string) ?? "";

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center rounded-full hover:opacity-80 transition-opacity"
      >
        {avatarUrl ? (
          <img
            src={avatarUrl}
            alt="User avatar"
            className="h-8 w-8 rounded-full object-cover"
            referrerPolicy="no-referrer"
          />
        ) : (
          <UserCircle className="h-8 w-8 text-muted-foreground" />
        )}
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 w-48 rounded-md border border-border bg-card shadow-lg z-50">
          <div className="px-3 py-2 text-xs text-muted-foreground border-b border-border truncate">
            {session.user.email ?? ""}
          </div>
          <div className="px-3 py-1.5 border-b border-border">
            <span className="inline-block rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-800 dark:bg-blue-900 dark:text-blue-200">
              {plan ?? "Free"}
            </span>
          </div>
          <button
            type="button"
            onClick={() => {
              signOut();
              setOpen(false);
            }}
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted/60 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      )}
    </div>
  );
}
