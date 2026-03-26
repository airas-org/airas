// Manual client for OAuth Proxy endpoints.
// The auto-generated OpenAPI client hardcodes OpenAPI.BASE (the local backend),
// but proxy-authorize must be sent to the production backend (VITE_OAUTH_PROXY_URL).
// A thin fetch wrapper is used instead to avoid coupling to generated internals.

import { OAUTH_PROXY_URL } from "./config";

interface AuthorizeResponse {
  authorize_url: string;
  state: string;
}

export function isProxyEnabled(): boolean {
  return !!OAUTH_PROXY_URL;
}

export async function proxyAuthorizeGitHub(origin: string): Promise<AuthorizeResponse> {
  if (!OAUTH_PROXY_URL) {
    throw new Error("VITE_OAUTH_PROXY_URL is not configured");
  }
  const url = `${OAUTH_PROXY_URL}/airas/ee/github/proxy-authorize?origin=${encodeURIComponent(origin)}`;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Proxy authorize failed: ${res.status}`);
  return res.json() as Promise<AuthorizeResponse>;
}
