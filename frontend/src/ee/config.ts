export const isSelfHosted = (): boolean => import.meta.env.VITE_SELF_HOSTED === "true";

export const GITHUB_SESSION_KEY = "github_session_token";

export const OAUTH_PROXY_URL = import.meta.env.VITE_OAUTH_PROXY_URL as string | undefined;
