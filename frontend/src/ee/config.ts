export const isEnterpriseEnabled = (): boolean =>
  import.meta.env.VITE_ENTERPRISE_ENABLED !== "false";

export const isSelfHosted = (): boolean => import.meta.env.VITE_SELF_HOSTED === "true";
