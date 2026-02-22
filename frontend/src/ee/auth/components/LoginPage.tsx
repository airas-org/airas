import { useAuth } from "@/ee/auth/hooks/useAuth";

export function LoginPage() {
  const { signInWithGoogle } = useAuth();

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="w-full max-w-sm space-y-6 rounded-lg border border-border bg-card p-8">
        <div className="text-center">
          <img src="/airas_logo.png" alt="AIRAS" className="mx-auto h-12 w-auto" />
          <h1 className="mt-4 text-xl font-semibold text-foreground">Sign in to AIRAS</h1>
        </div>
        <div className="space-y-3">
          <button
            type="button"
            onClick={signInWithGoogle}
            className="flex w-full items-center justify-center gap-2 rounded-md border border-border bg-background px-4 py-2 text-sm font-medium text-foreground hover:bg-muted/60 transition-colors"
          >
            Sign in with Google
          </button>
        </div>
      </div>
    </div>
  );
}
