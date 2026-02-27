import type { ReactNode } from "react";
import { LoginPage } from "@/ee/auth/components/LoginPage";
import { useSession } from "@/ee/auth/hooks/useSession";
import { LoadingSpinner } from "@/ee/auth/components/LoadingSpinner";

export function AuthGuard({ children }: { children: ReactNode }) {
  const { session, loading } = useSession();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
        <div className="flex flex-col items-center gap-4">
          <img src="/airas_logo.png" alt="AIRAS" className="h-12 w-auto" />
          <LoadingSpinner className="h-6 w-6 text-slate-400" />
        </div>
      </div>
    );
  }

  if (!session) {
    return <LoginPage />;
  }

  return <>{children}</>;
}
