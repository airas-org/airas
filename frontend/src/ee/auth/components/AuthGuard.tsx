import type { ReactNode } from "react";
import { LoginPage } from "@/ee/auth/components/LoginPage";
import { useSession } from "@/ee/auth/hooks/useSession";

export function AuthGuard({ children }: { children: ReactNode }) {
  const { session, loading } = useSession();

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!session) {
    return <LoginPage />;
  }

  return <>{children}</>;
}
