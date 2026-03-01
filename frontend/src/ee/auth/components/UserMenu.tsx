import { Copy, LogOut, UserCircle } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/ee/auth/hooks/useAuth";
import { useSession } from "@/ee/auth/hooks/useSession";
import { supabase } from "@/ee/auth/lib/supabase";

export function UserMenu() {
  const { session } = useSession();
  const { signOut } = useAuth();
  const [open, setOpen] = useState(false);
  const [copied, setCopied] = useState(false);

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
          <button
            type="button"
            onClick={async () => {
              const {
                data: { session: s },
              } = await supabase.auth.getSession();
              if (s?.access_token) {
                await navigator.clipboard.writeText(s.access_token);
                setCopied(true);
                setTimeout(() => setCopied(false), 2000);
              }
            }}
            className="flex w-full items-center gap-2 px-3 py-2 text-sm text-foreground hover:bg-muted/60 transition-colors"
          >
            <Copy className="h-4 w-4" />
            {copied ? "Copied!" : "Copy Access Token"}
          </button>
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
