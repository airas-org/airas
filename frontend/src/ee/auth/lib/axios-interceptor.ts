import type { InternalAxiosRequestConfig } from "axios";
import { getSupabase } from "@/ee/auth/lib/supabase";

async function getAccessToken(): Promise<string | null> {
  const client = getSupabase();
  if (!client) return null;
  const {
    data: { session },
  } = await client.auth.getSession();
  return session?.access_token ?? null;
}

export async function authRequestInterceptor(
  config: InternalAxiosRequestConfig,
): Promise<InternalAxiosRequestConfig> {
  const token = await getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}

/**
 * Token resolver for the OpenAPI generated client.
 * Set as `OpenAPI.TOKEN` to attach auth tokens to all generated API calls.
 */
export async function openApiTokenResolver(): Promise<string> {
  return (await getAccessToken()) ?? "";
}
