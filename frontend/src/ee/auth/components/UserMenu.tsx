import { LogOut, UserCircle } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/ee/auth/hooks/useAuth";
import { useSession } from "@/ee/auth/hooks/useSession";

export function UserMenu() {
  const { session } = useSession();
  const { signOut } = useAuth();
  const [open, setOpen] = useState(false);

  if (!session) return null;

  const email = session.user.email ?? "";

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 rounded-md border border-border px-3 py-1.5 text-sm text-foreground hover:bg-muted/60 transition-colors"
      >
        <UserCircle className="h-5 w-5" />
        <span className="max-w-[120px] truncate">{email}</span>
      </button>
      {open && (
        <div className="absolute right-0 top-full mt-1 w-48 rounded-md border border-border bg-card shadow-lg z-50">
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
