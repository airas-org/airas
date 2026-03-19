import { getSupabase } from "@/ee/auth/lib/supabase";

export function useAuth() {
  const signInWithGoogle = async () => {
    const client = getSupabase();
    if (!client) throw new Error("Supabase is not configured");
    const { error } = await client.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) throw error;
  };

  const signInWithGitHub = async () => {
    const client = getSupabase();
    if (!client) throw new Error("Supabase is not configured");
    const { error } = await client.auth.signInWithOAuth({
      provider: "github",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (error) throw error;
  };

  const signOut = async () => {
    const client = getSupabase();
    if (!client) throw new Error("Supabase is not configured");
    const { error } = await client.auth.signOut();
    if (error) throw error;
  };

  return { signInWithGoogle, signInWithGitHub, signOut };
}
