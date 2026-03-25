export const isEnterpriseEnabled = (): boolean => import.meta.env.ENTERPRISE_ENABLED === "true";

export const GITHUB_SESSION_KEY = "github_session_token";

export const OAUTH_PROXY_URL = import.meta.env.VITE_OAUTH_PROXY_URL as string | undefined;
